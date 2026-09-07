#!/usr/bin/env python3
"""Opt-in local usage ledger. No provider calls, transcript storage, or uploads."""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys


FIELDS = ("input_tokens", "cache_read_input_tokens", "cache_write_input_tokens",
          "output_tokens", "reasoning_tokens", "provider_total_tokens")
MAX_LINE = 1024 * 1024
MAX_FILE = 4 * MAX_LINE
SCHEMA = 1


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safe_path(path):
    """Reject physical redirects, including Windows junction ancestors."""
    path = Path(os.path.abspath(Path(path).expanduser()))
    for component in (path, *path.parents):
        try:
            info = component.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("linked runtime or source path refused")
        if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
            raise ValueError("hard-linked runtime or source file refused")
    return path


def _json(path):
    path = _safe_path(path)
    if path.stat().st_size > MAX_LINE:
        raise ValueError("oversized local configuration refused")
    return json.loads(path.read_text(encoding="utf-8"))


def _config(directory):
    directory = _safe_path(directory)
    config = _json(directory / "config.json")
    if (not isinstance(config, dict) or config.get("schema") != SCHEMA
            or type(config.get("enabled")) is not bool
            or not isinstance(config.get("sources"), dict)
            or not config["sources"] or set(config["sources"]) - {"codex", "claude"}):
        raise ValueError("invalid local usage configuration")
    try:
        parsed = datetime.fromisoformat(config["since"].replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError()
    except (ValueError, TypeError, KeyError, AttributeError):
        raise ValueError("invalid opt-in timestamp") from None
    for value in config["sources"].values():
        if not isinstance(value, str) or not Path(value).is_absolute():
            raise ValueError("source roots must be absolute paths")
    return directory, config


def _connect(directory, *, create=False):
    for name in ("usage.sqlite3", "usage.sqlite3-journal", "usage.sqlite3-wal", "usage.sqlite3-shm"):
        _safe_path(directory / name)
    if not create and not (directory / "usage.sqlite3").is_file():
        raise ValueError("initialized ledger is missing; usage is unknown")
    db = sqlite3.connect(directory / "usage.sqlite3", timeout=5)
    db.execute("PRAGMA trusted_schema=OFF")
    if not create:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"events", "files", "feedback", "diagnostics", "metadata"}.issubset(tables):
            db.close()
            raise ValueError("initialized ledger is incomplete; usage is unknown")
        return db
    db.execute("CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, value TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS files (id TEXT PRIMARY KEY, value TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS feedback (id TEXT PRIMARY KEY, value TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS diagnostics (id TEXT PRIMARY KEY, count INTEGER NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS metadata (id TEXT PRIMARY KEY, value TEXT NOT NULL)")
    db.commit()
    return db


def init_ledger(directory, sources, *, opt_in=False):
    if opt_in is not True:
        raise ValueError("explicit --opt-in is required; no sources were read")
    directory = _safe_path(directory)
    if not isinstance(sources, dict) or not sources or set(sources) - {"codex", "claude"}:
        raise ValueError("choose explicit codex or claude source roots")
    roots = {}
    for host, value in sources.items():
        source = _safe_path(value)
        if not source.is_dir():
            raise ValueError("configured source root is not a directory")
        if source == directory or source in directory.parents or directory in source.parents:
            raise ValueError("source and ledger directories must not overlap")
        roots[host] = str(source)
    if directory.exists() and any(directory.iterdir()):
        raise ValueError("choose a new or empty private ledger directory")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    config = {"schema": SCHEMA, "enabled": True, "since": _now(), "sources": roots}
    with (directory / "config.json").open("x", encoding="utf-8") as stream:
        json.dump(config, stream, indent=2)
        stream.write("\n")
    (directory / ".gitignore").write_text("*\n", encoding="ascii")
    with closing(_connect(directory, create=True)):
        pass
    return {"status": "enabled", "since": config["since"], "hosts": sorted(roots)}


def _adapter():
    spec = importlib.util.spec_from_file_location("adc_usage_sources", Path(__file__).with_name("adc_usage_sources.py"))
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def _validate_usage(usage):
    if set(usage) != set(FIELDS) or any(
            value is not None and (type(value) is not int or value < 0 or value > 2**63 - 1)
            for value in usage.values()):
        raise ValueError("invalid usage counters; ledger transaction rolled back")
    inp, out, total = (usage[key] for key in ("input_tokens", "output_tokens", "provider_total_tokens"))
    if inp is not None:
        subsets = [usage[key] for key in ("cache_read_input_tokens", "cache_write_input_tokens")]
        if sum(value for value in subsets if value is not None) > inp:
            raise ValueError("input subset contradiction; ledger transaction rolled back")
    if out is not None and usage["reasoning_tokens"] is not None and usage["reasoning_tokens"] > out:
        raise ValueError("output subset contradiction; ledger transaction rolled back")
    if total is not None and inp is not None and out is not None and total != inp + out:
        raise ValueError("total contradiction; ledger transaction rolled back")


def _upsert_event(db, event):
    _validate_usage(event["usage"])
    previous = db.execute("SELECT value FROM events WHERE id=?", (event["event_id"],)).fetchone()
    if previous is None:
        db.execute("INSERT INTO events VALUES (?,?)", (event["event_id"], json.dumps(event)))
        return "inserted"
    old = json.loads(previous[0])
    for key in ("provider", "effort", "usage_semantics"):
        if old.get(key) is not None and event.get(key) is not None and old[key] != event[key]:
            raise ValueError("response attribution conflict; ledger transaction rolled back")
    # The first observed identity owns replayed/forked requests. A copied log is
    # not another task consuming those tokens. Missing metadata may be filled.
    new = dict(old)
    attribution_rank = {"unknown": 0, "turn-context": 1, "rerouted": 2, "usage": 3}
    before_rank = attribution_rank[old["model_source"]]
    after_rank = attribution_rank[event["model_source"]]
    if old.get("model") is not None and event.get("model") is not None and old["model"] != event["model"]:
        if before_rank == after_rank:
            raise ValueError("response model conflict; ledger transaction rolled back")
    if after_rank > before_rank and event.get("model") is not None:
        new["model"] = event["model"]
        new["model_source"] = event["model_source"]
    if old.get("task_scope") == "request" and event.get("task_scope") in {"turn", "root-turn"}:
        for key in ("task_id", "root_task_id", "task_scope"):
            new[key] = event[key]
    if old.get("role") == "unknown" and event.get("role") != "unknown":
        new["role"] = event["role"]
    for key in ("provider", "model", "effort", "host_version"):
        if new.get(key) is None and event.get(key) is not None:
            new[key] = event[key]
            if key == "model":
                new["model_source"] = event["model_source"]
    increasing = decreasing = False
    merged = dict(old["usage"])
    for key in FIELDS:
        before, after = old["usage"][key], event["usage"][key]
        if after is None:
            continue
        if before is None:
            merged[key] = after
        elif after > before:
            increasing = True
            merged[key] = after
        elif after < before:
            decreasing = True
    streaming = event["usage_semantics"].startswith("claude-")
    if (not streaming and (increasing or decreasing)) or (increasing and decreasing):
        raise ValueError("response usage conflict; ledger transaction rolled back")
    if not decreasing:
        new["usage"] = merged
    _validate_usage(new["usage"])
    if new == old:
        return "duplicates"
    db.execute("UPDATE events SET value=? WHERE id=?", (json.dumps(new), event["event_id"]))
    return "updated"


def _source_files(roots, diagnostics):
    files = []
    for host, root in roots.items():
        root = _safe_path(root)
        if not root.is_dir():
            diagnostics["missing_source_root"] += 1
            continue
        def walk_error(_error):
            diagnostics["unreadable_source_directory"] += 1
        for base, dirs, names in os.walk(root, followlinks=False, onerror=walk_error):
            for name in list(dirs):
                try:
                    _safe_path(Path(base) / name)
                except (ValueError, OSError):
                    dirs.remove(name)
                    diagnostics["linked_source_skipped"] += 1
            for name in names:
                if not name.endswith(".jsonl"):
                    continue
                path = Path(base) / name
                try:
                    path = _safe_path(path)
                    info = path.stat()
                    if stat.S_ISREG(info.st_mode):
                        files.append((info.st_mtime, host, path, info))
                except (ValueError, OSError):
                    diagnostics["unreadable_or_linked_source"] += 1
    return sorted(files, key=lambda entry: (entry[0], str(entry[2])), reverse=True)


def _read_batch(path, info, prior, budget, diagnostics):
    rows = []
    current = dict(prior or {})
    offset = current.get("offset", 0)
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino) or opened.st_nlink != 1:
            raise ValueError("source changed while opening; collection refused")
        prefix_size = current.get("prefix_size", min(4096, opened.st_size))
        prefix = hashlib.sha256(stream.read(prefix_size)).hexdigest()
        identity = [opened.st_dev, opened.st_ino]
        if current and (current.get("identity") != identity or current.get("prefix") != prefix
                        or opened.st_size < offset):
            current, offset = {}, 0
            stream.seek(0)
            prefix_size = min(4096, opened.st_size)
            prefix = hashlib.sha256(stream.read(prefix_size)).hexdigest()
            diagnostics["source_restarted"] += 1
        stream.seek(offset)
        started = offset
        skipping = current.get("skipping", False)
        while stream.tell() - started < budget:
            start = stream.tell()
            line = stream.readline(MAX_LINE + 1)
            if not line:
                break
            complete = line.endswith(b"\n")
            if skipping or len(line) > MAX_LINE:
                if not skipping:
                    diagnostics["oversized_line_skipped"] += 1
                skipping = not complete
                offset = stream.tell()
                continue
            if not complete:
                diagnostics["partial_line_deferred"] += 1
                stream.seek(start)
                break
            offset = stream.tell()
            try:
                rows.append(json.loads(line))
            except (ValueError, UnicodeDecodeError, RecursionError):
                diagnostics["malformed_json_line"] += 1
        current.update(offset=offset, identity=identity, prefix=prefix, prefix_size=prefix_size, skipping=skipping)
        return current, rows, max(0, stream.tell() - started), offset < opened.st_size


def collect(directory, *, max_bytes=32 * MAX_LINE):
    if type(max_bytes) is not int or max_bytes < 1:
        raise ValueError("read budget must be a positive integer")
    directory, config = _config(directory)
    if not config["enabled"]:
        return {"status": "disabled", "inserted": 0, "updated": 0, "duplicates": 0, "backlog": False}
    for value in config["sources"].values():
        source = _safe_path(value)
        if source == directory or source in directory.parents or directory in source.parents:
            raise ValueError("source and ledger directories must not overlap")
    diagnostics = Counter()
    result = {"status": "collected", "inserted": 0, "updated": 0, "duplicates": 0,
              "backlog": False, "bytes_read": 0}
    cutoff = datetime.fromisoformat(config["since"].replace("Z", "+00:00")).timestamp()
    adapter = _adapter()
    adapter_digest = hashlib.sha256(Path(adapter.__file__).read_bytes()).hexdigest()
    with closing(_connect(directory)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        for modified, host, path, info in _source_files(config["sources"], diagnostics):
            if modified < cutoff:
                continue
            key = hashlib.sha256((host + ":" + str(path)).encode("utf-8")).hexdigest()
            prior = db.execute("SELECT value FROM files WHERE id=?", (key,)).fetchone()
            prior = json.loads(prior[0]) if prior else {}
            if prior and prior.get("adapter_sha256") != adapter_digest:
                prior = {}
                diagnostics["adapter_context_rebuilt"] += 1
            if result["bytes_read"] >= max_bytes:
                if not prior or prior.get("offset", 0) < info.st_size:
                    result["backlog"] = True
                continue
            try:
                current, rows, read, pending = _read_batch(path, info, prior,
                    min(MAX_FILE, max_bytes - result["bytes_read"]), diagnostics)
            except OSError:
                diagnostics["unreadable_source_file"] += 1
                continue
            state, events, issues = adapter.parse_rows(rows, host, current.get("parser"))
            current["parser"] = state
            current["adapter_sha256"] = adapter_digest
            diagnostics.update(issues)
            for event in events:
                if event["timestamp"] >= config["since"]:
                    result[_upsert_event(db, event)] += 1
            db.execute("INSERT OR REPLACE INTO files VALUES (?,?)", (key, json.dumps(current)))
            result["bytes_read"] += read
            result["backlog"] |= pending
        for key, value in diagnostics.items():
            db.execute("INSERT INTO diagnostics VALUES (?,?) ON CONFLICT(id) DO UPDATE SET count=count+excluded.count", (key, value))
        db.execute("INSERT OR REPLACE INTO metadata VALUES ('last_collection',?)",
                   (json.dumps({"timestamp": _now(), "backlog": result["backlog"], "diagnostics": dict(diagnostics)}),))
    result["diagnostics"] = dict(diagnostics)
    return result


def _task_key(event):
    return event["root_task_id"] if event["usage_semantics"].startswith("codex-") else event["task_id"]


def record_feedback(directory, task_id, *, used="unknown", expected="unknown", invocation="unknown",
                    quality="unknown", task_class="other"):
    if (not isinstance(task_id, str) or not re.fullmatch(r"[0-9a-f]{64}", task_id)
            or used not in {"yes", "no", "unknown"} or expected not in {"yes", "no", "unknown"}
            or invocation not in {"implicit", "explicit", "unknown"}
            or quality not in {"passed", "failed", "unknown"}
            or task_class not in {"map", "audit", "verify", "remediate", "install", "other"}):
        raise ValueError("invalid structured feedback")
    directory, _ = _config(directory)
    value = dict(used=used, expected=expected, invocation=invocation, quality=quality,
                 task_class=task_class, labeled_at=_now())
    with closing(_connect(directory)) as db, db:
        if not any(_task_key(json.loads(row[0])) == task_id for row in db.execute("SELECT value FROM events")):
            raise ValueError("feedback requires an observed task identifier")
        db.execute("INSERT OR REPLACE INTO feedback VALUES (?,?)", (task_id, json.dumps(value)))
    return {"status": "feedback-recorded", "task_id": task_id}


def _empty_totals():
    return {key: {"known_subtotal": 0, "missing_events": 0} for key in FIELDS}


def _add_usage(totals, usage):
    for key in FIELDS:
        if usage[key] is None:
            totals[key]["missing_events"] += 1
        else:
            totals[key]["known_subtotal"] += usage[key]


def summary(directory):
    directory, config = _config(directory)
    with closing(_connect(directory)) as db:
        feedback = {key: json.loads(value) for key, value in db.execute("SELECT id,value FROM feedback")}
        diagnostics = dict(db.execute("SELECT id,count FROM diagnostics"))
        collection = db.execute("SELECT value FROM metadata WHERE id='last_collection'").fetchone()
        strata, tasks = {}, {}
        count = 0
        for raw, in db.execute("SELECT value FROM events"):
            event = json.loads(raw)
            count += 1
            task_id = _task_key(event)
            labels = feedback.get(task_id, {})
            dimensions = ("provider", "model", "model_source", "effort", "usage_semantics", "role", "host_version")
            identity = {key: event.get(key) for key in dimensions}
            identity.update(task_class=labels.get("task_class", "other"), quality=labels.get("quality", "unknown"),
                            skill_used=labels.get("used", "unknown"))
            key = json.dumps(identity, sort_keys=True)
            stratum = strata.setdefault(key, {**identity, "events": 0, "usage": _empty_totals()})
            stratum["events"] += 1
            _add_usage(stratum["usage"], event["usage"])
            scope = event.get("task_scope", "turn" if event["usage_semantics"].startswith("codex-") else "request")
            task = tasks.setdefault(task_id, {"task_id": task_id, "scope": scope,
                "first_seen": event["timestamp"], "last_seen": event["timestamp"], "events": 0,
                "quality": labels.get("quality", "unknown"), "feedback": labels or None, "usage": _empty_totals()})
            if scope in {"turn", "root-turn"}:
                task["scope"] = scope
            task["first_seen"] = min(task["first_seen"], event["timestamp"])
            task["last_seen"] = max(task["last_seen"], event["timestamp"])
            task["events"] += 1
            _add_usage(task["usage"], event["usage"])
    score = dict(tp=0, fp=0, fn=0, tn=0, labeled_implicit=0, excluded=len(tasks))
    for task_id, task in tasks.items():
        label = feedback.get(task_id, {})
        if (task["scope"] not in {"turn", "root-turn"} or label.get("invocation") != "implicit"
                or label.get("used") not in {"yes", "no"} or label.get("expected") not in {"yes", "no"}):
            continue
        key = {("yes", "yes"): "tp", ("yes", "no"): "fp", ("no", "yes"): "fn", ("no", "no"): "tn"}[
            label["used"], label["expected"]]
        score[key] += 1
        score["labeled_implicit"] += 1
        score["excluded"] -= 1
    score["precision"] = score["tp"] / (score["tp"] + score["fp"]) if score["tp"] + score["fp"] else None
    score["recall"] = score["tp"] / (score["tp"] + score["fn"]) if score["tp"] + score["fn"] else None
    return {"schema": SCHEMA, "enabled": config["enabled"], "since": config["since"], "events": count,
            "claim": "Observed local usage and feedback; no causal savings, billing attestation, or population trigger accuracy.",
            "savings": None, "subscription_cost": None, "quota_remaining": None,
            "strata": list(strata.values()), "tasks": sorted(tasks.values(), key=lambda task: task["last_seen"], reverse=True),
            "trigger_feedback": score, "diagnostics": diagnostics,
            "last_collection": json.loads(collection[0]) if collection else None}


def disable(directory):
    directory, config = _config(directory)
    config["enabled"] = False
    temp = _safe_path(directory / "config.disabled.tmp")
    with temp.open("x", encoding="utf-8") as stream:
        json.dump(config, stream, indent=2)
        stream.write("\n")
    os.replace(temp, _safe_path(directory / "config.json"))
    return {"status": "disabled", "history": "retained"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "collect", "summary", "feedback", "disable"):
        command = sub.add_parser(name)
        command.add_argument("--directory", required=True, type=Path)
        if name == "init":
            command.add_argument("--source", action="append", required=True, metavar="HOST=ROOT")
            command.add_argument("--opt-in", action="store_true")
        elif name == "summary":
            command.add_argument("--task-limit", type=int, default=20, help="Maximum recent tasks to display; aggregate totals always cover all records")
        elif name == "feedback":
            command.add_argument("--task-id", required=True)
            command.add_argument("--used", choices=("yes", "no", "unknown"), default="unknown")
            command.add_argument("--expected", choices=("yes", "no", "unknown"), default="unknown")
            command.add_argument("--invocation", choices=("implicit", "explicit", "unknown"), default="unknown")
            command.add_argument("--quality", choices=("passed", "failed", "unknown"), default="unknown")
            command.add_argument("--task-class", choices=("map", "audit", "verify", "remediate", "install", "other"), default="other")
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            sources = {}
            for source in args.source:
                host, separator, path = source.partition("=")
                if not separator or host in sources:
                    raise ValueError("provide each HOST=ROOT source once")
                sources[host] = path
            result = init_ledger(args.directory, sources, opt_in=args.opt_in)
        elif args.command == "feedback":
            result = record_feedback(args.directory, args.task_id, used=args.used, expected=args.expected,
                invocation=args.invocation, quality=args.quality, task_class=args.task_class)
        elif args.command == "summary":
            if args.task_limit < 0:
                raise ValueError("task limit must not be negative")
            result = summary(args.directory)
            result["task_count"] = len(result["tasks"])
            result["tasks"] = result["tasks"][:args.task_limit]
        else:
            result = {"collect": collect, "disable": disable}[args.command](args.directory)
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 0
    except ValueError as error:
        # All ValueError messages above are fixed labels; never echo source rows.
        if isinstance(error, json.JSONDecodeError):
            print("REFUSED: invalid local configuration JSON", file=sys.stderr)
        else:
            print("REFUSED: " + str(error), file=sys.stderr)
        return 2
    except (OSError, sqlite3.Error):
        print("REFUSED: local usage I/O failed; inspect paths and permissions locally", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
