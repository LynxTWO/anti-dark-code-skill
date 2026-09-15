#!/usr/bin/env python3
"""Opt-in lifecycle review tickets and reported labels; never an automatic grader."""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import sqlite3
import subprocess
import sys

HEX = re.compile(r"[0-9a-f]{64}")
MAX_INPUT = 1024 * 1024
REVIEWERS = ("agent-self-review", "human-review", "unknown")
BASES = ("acceptance-checks", "observed-result", "owner-feedback", "unknown")


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash(kind, value):
    if not isinstance(value, str) or not value or len(value) > 256:
        raise ValueError("review requires bounded native thread and turn identifiers")
    return hashlib.sha256(("codex:" + kind + ":" + value).encode()).hexdigest()


def _usage():
    spec = importlib.util.spec_from_file_location("review_usage_backend", Path(__file__).with_name("adc_usage.py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def _settings(db):
    row = db.execute("SELECT value FROM metadata WHERE id='review_config'").fetchone()
    if row is None:
        return {"enabled": False}
    value = json.loads(row[0])
    if (not isinstance(value, dict) or value.get("schema") != 1
            or type(value.get("enabled")) is not bool):
        raise ValueError("invalid review configuration")
    return value


def configure(directory, *, enabled, opt_in=False):
    if enabled and opt_in is not True:
        raise ValueError("routine review collection requires explicit opt-in")
    usage = _usage()
    directory, config = usage._config(directory)
    if enabled and not config["enabled"]:
        raise ValueError("usage collection is disabled; review collection remains disabled")
    with closing(usage._connect(directory)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        previous = _settings(db)
        if enabled:
            db.execute("CREATE TABLE IF NOT EXISTS reviews (id TEXT PRIMARY KEY, value TEXT NOT NULL)")
        value = {"schema": 1, "enabled": enabled, "since": previous.get("since", _now())}
        db.execute("INSERT OR REPLACE INTO metadata VALUES ('review_config',?)", (json.dumps(value),))
    return {"status": "review-enabled" if enabled else "review-disabled", "history": "retained"}


def _records(db):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='reviews'").fetchone():
        return {}
    return {key: json.loads(raw) for key, raw in db.execute("SELECT id,value FROM reviews")}


def coverage(db, tasks=None):
    config = _settings(db)
    records = _records(db)
    result = {"enabled": config["enabled"], "observed": len(records), "submitted": 0,
              "missing_labels": 0, "linked": 0, "awaiting_usage": 0,
              "ambiguous": 0, "feedback_conflict": 0, "stopped_without_labels": 0,
              "reported_failed_attempts": 0}
    for row in records.values():
        submitted = row.get("labels") is not None
        result["submitted" if submitted else "missing_labels"] += 1
        result[row.get("link_status", "awaiting_usage")] += 1
        if row.get("stopped_at") and not submitted:
            result["stopped_without_labels"] += 1
        if submitted and row["labels"].get("had_failed_attempt") == "yes":
            result["reported_failed_attempts"] += 1
    # Surface missing host delivery too, not only missing labels on delivered hooks.
    # This is a time-window count; paused/untrusted hosts can contribute gaps.
    if tasks is None:
        tasks = {}
        for raw, in db.execute("SELECT value FROM events"):
            event = json.loads(raw)
            if event.get("usage_semantics", "").startswith("codex-"):
                task = tasks.setdefault(event["root_task_id"], {"first_seen": event["timestamp"],
                                        "scope": event.get("task_scope", "turn")})
                task["first_seen"] = min(task["first_seen"], event["timestamp"])
                if event.get("task_scope") in {"turn", "root-turn"}:
                    task["scope"] = event["task_scope"]
    since = config.get("since")
    recent = {key for key, value in tasks.items() if since and value["first_seen"] >= since
              and value.get("scope") in {"turn", "root-turn"}}
    linked = {r["task_id"] for r in records.values() if r.get("task_id")}
    result["usage_groups_since_review_opt_in"] = len(recent)
    result["usage_groups_without_lifecycle_ticket"] = len(recent - linked)
    return result


def reconcile(db):
    """Join scoped native hashes to observed parent usage; never guess latest task."""
    if not _settings(db)["enabled"]:
        return
    records = _records(db)
    if not records:
        return
    wanted = {(r["thread_hash"], r["turn_hash"]) for r in records.values()}
    matches = {key: set() for key in wanted}
    for raw, in db.execute("SELECT value FROM events"):
        event = json.loads(raw)
        key = (event.get("host_thread_hash"), event.get("host_turn_hash"))
        if (key in matches and event.get("role") == "agent"
                and event.get("task_scope") in {"turn", "root-turn"}
                and event.get("usage_semantics", "").startswith("codex-")):
            matches[key].add(event["root_task_id"])
    for ticket, row in records.items():
        previous = json.dumps(row, sort_keys=True)
        old_task = row.get("task_id")
        candidates = matches[(row["thread_hash"], row["turn_hash"])]
        row["link_status"] = "awaiting_usage" if not candidates else "ambiguous"
        row["task_id"] = None
        # Derived feedback must not survive a disproved link. Preserve the review
        # and its labels/history, and never remove an independently edited row.
        if old_task and (len(candidates) != 1 or old_task not in candidates):
            old_feedback = db.execute("SELECT value FROM feedback WHERE id=?", (old_task,)).fetchone()
            if old_feedback and json.loads(old_feedback[0]).get("review_ticket") == ticket:
                db.execute("DELETE FROM feedback WHERE id=?", (old_task,))
        if len(candidates) == 1:
            task = next(iter(candidates))
            row.update(task_id=task, link_status="linked")
            labels = row.get("labels")
            if labels is not None:
                existing = db.execute("SELECT value FROM feedback WHERE id=?", (task,)).fetchone()
                if existing and json.loads(existing[0]).get("review_ticket") != ticket:
                    row["link_status"] = "feedback_conflict"
                else:
                    value = {**labels, "review_ticket": ticket}
                    if not existing or json.loads(existing[0]) != value:
                        db.execute("INSERT OR REPLACE INTO feedback VALUES (?,?)", (task, json.dumps(value)))
        if json.dumps(row, sort_keys=True) != previous:
            db.execute("UPDATE reviews SET value=? WHERE id=?", (json.dumps(row), ticket))


def _command(directory, ticket):
    argv = [sys.executable, "-B", str(Path(__file__).resolve()), "submit", "--directory",
            str(directory), "--ticket", ticket, "--reviewer", "agent-self-review"]
    if os.name == "nt":
        # This text is for a PowerShell task-closeout command, not execution here.
        return "& " + " ".join("'" + s.replace("'", "''") + "'" for s in argv)
    return shlex.join(argv)


def observe(directory, payload):
    if not isinstance(payload, dict) or payload.get("hook_event_name") not in {"UserPromptSubmit", "Stop"}:
        raise ValueError("unsupported review lifecycle event")
    # Codex hook session_id is its thread identifier, not the usage transport session_id.
    # Ignore prompt, assistant message, transcript_path, cwd and arbitrary extra fields.
    thread = _hash("thread", payload.get("session_id"))
    turn = _hash("turn", payload.get("turn_id"))
    ticket = hashlib.sha256(("review:codex:" + thread + ":" + turn).encode()).hexdigest()
    usage = _usage()
    directory, config = usage._config(directory)
    if not config["enabled"]:
        return {}
    with closing(usage._connect(directory)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        if not _settings(db)["enabled"]:
            return {}
        previous = db.execute("SELECT value FROM reviews WHERE id=?", (ticket,)).fetchone()
        row = json.loads(previous[0]) if previous else {
            "thread_hash": thread, "turn_hash": turn, "started_at": None, "stopped_at": None,
            "labels": None, "task_id": None, "link_status": "awaiting_usage",
            "review_helper_version": Path(__file__).parents[1].joinpath("VERSION").read_text().strip(),
            "review_helper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        }
        event = payload["hook_event_name"]
        field = "started_at" if event == "UserPromptSubmit" else "stopped_at"
        row[field] = row.get(field) or _now()
        db.execute("INSERT OR REPLACE INTO reviews VALUES (?,?)", (ticket, json.dumps(row)))
        reconcile(db)
    if event == "Stop":
        return {}  # No continuation, task-success inference or extra model call.
    text = (
        "Opted-in local task review. This reminder is not a skill activation. "
        "Before your final response, record only what this task supports with: "
        + _command(directory, ticket) + " --used yes|no|unknown --expected yes|no|unknown "
        "--invocation explicit|implicit|unknown --quality passed|failed|unknown "
        "--basis acceptance-checks|observed-result|owner-feedback|unknown "
        "--task-class map|audit|verify|remediate|install|other. Replace choices with one value. "
        "used means anti-dark-code guided the work, not that you read this reminder. "
        "expected is whether the user's request warranted it; label misses and non-activations too. "
        "invocation is explicit only when the user requested anti-dark-code; otherwise implicit, "
        "including non-use. Use unknown when the request is unclear. "
        "Known quality needs observed acceptance evidence; with acceptance-checks include "
        "--evidence-sha256 HASH of an existing result. Report --skill-version VERSION only "
        "from the skill that guided the task. Uncertain fields stay unknown. "
        "Use --had-failed-attempt yes|no|unknown to retain failures before recovery. "
        "Do not run extra tests or read old transcripts merely to label a task. If recording fails, "
        "leave the review pending; do not delay the requested work or claim a label was saved."
    )
    return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": text}}


def submit(directory, ticket, *, used="unknown", expected="unknown", invocation="unknown",
           quality="unknown", task_class="other", reviewer="agent-self-review", basis="unknown",
           evidence_sha256=(), skill_version=None, had_failed_attempt="unknown"):
    if (not isinstance(ticket, str) or not HEX.fullmatch(ticket)
            or used not in {"yes", "no", "unknown"} or expected not in {"yes", "no", "unknown"}
            or invocation not in {"explicit", "implicit", "unknown"}
            or quality not in {"passed", "failed", "unknown"}
            or task_class not in {"map", "audit", "verify", "remediate", "install", "other"}
            or reviewer not in REVIEWERS or basis not in BASES
            or had_failed_attempt not in {"yes", "no", "unknown"}
            or not isinstance(evidence_sha256, (list, tuple)) or len(evidence_sha256) > 4
            or any(not isinstance(x, str) or not HEX.fullmatch(x) for x in evidence_sha256)):
        raise ValueError("invalid structured review labels")
    if quality != "unknown" and basis == "unknown":
        raise ValueError("known quality requires a reported observation basis")
    if basis == "acceptance-checks" and not evidence_sha256:
        raise ValueError("acceptance-check labels require an existing result digest")
    if skill_version is not None and (used != "yes" or not isinstance(skill_version, str)
            or not re.fullmatch(r"\d{4}\.\d{2}\.\d{2}-unified\.\d+(?:-rc\.\d+)?", skill_version)):
        raise ValueError("invalid reported skill version")
    usage = _usage()
    directory, config = usage._config(directory)
    if not config["enabled"]:
        raise ValueError("review collection is disabled; labels were not changed")
    with closing(usage._connect(directory)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        if not _settings(db)["enabled"]:
            raise ValueError("review collection is disabled; labels were not changed")
        previous = db.execute("SELECT value FROM reviews WHERE id=?", (ticket,)).fetchone()
        if not previous:
            raise ValueError("review requires an observed lifecycle ticket")
        row = json.loads(previous[0])
        labels = {"used": used, "expected": expected, "invocation": invocation,
            "quality": quality, "task_class": task_class, "reviewer": reviewer, "basis": basis,
            "evidence_sha256": sorted(set(evidence_sha256)), "reported_skill_version": skill_version,
            "had_failed_attempt": had_failed_attempt}
        old_labels = row.get("labels")
        if old_labels is None or {k: v for k, v in old_labels.items() if k != "labeled_at"} != labels:
            history = row.setdefault("label_history", [])
            if old_labels is not None:
                if len(history) >= 32:
                    raise ValueError("review correction history is full; retain it for inspection")
                history.append(old_labels)
            row["labels"] = {**labels, "labeled_at": _now()}
        db.execute("UPDATE reviews SET value=? WHERE id=?", (json.dumps(row), ticket))
        reconcile(db)
        saved = json.loads(db.execute("SELECT value FROM reviews WHERE id=?", (ticket,)).fetchone()[0])
    return {"status": "review-recorded", "ticket": ticket, "link_status": saved["link_status"],
            "task_id": saved["task_id"], "claim": "Reported review; not independent validation."}


def pending(directory, limit=20):
    if type(limit) is not int or not 0 <= limit <= 100:
        raise ValueError("review limit must be between zero and 100")
    usage = _usage()
    directory, _ = usage._config(directory)
    with closing(usage._connect(directory)) as db:
        records = _records(db)
        rows = [{"ticket": ticket, "started_at": r["started_at"], "stopped_at": r["stopped_at"],
                 "link_status": r["link_status"], "task_id": r["task_id"]}
                for ticket, r in records.items() if r.get("labels") is None]
        return {"coverage": coverage(db), "pending": sorted(rows,
                key=lambda x: x["started_at"] or x["stopped_at"] or "", reverse=True)[:limit]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("enable", "disable", "hook", "submit", "pending"):
        command = sub.add_parser(name)
        command.add_argument("--directory", required=True, type=Path)
        if name == "enable":
            command.add_argument("--opt-in", action="store_true")
        if name == "pending":
            command.add_argument("--limit", type=int, default=20)
        if name == "submit":
            command.add_argument("--ticket", required=True)
            for flag, default in (("used", "unknown"), ("expected", "unknown"),
                    ("invocation", "unknown"), ("quality", "unknown"), ("task-class", "other"),
                    ("reviewer", "agent-self-review"), ("basis", "unknown")):
                command.add_argument("--" + flag, default=default)
            command.add_argument("--evidence-sha256", action="append", default=[])
            command.add_argument("--skill-version")
            command.add_argument("--had-failed-attempt", default="unknown")
    args = parser.parse_args(argv)
    try:
        if args.command == "hook":
            raw = sys.stdin.buffer.read(MAX_INPUT + 1)
            if len(raw) > MAX_INPUT:
                raise ValueError("oversized hook input")
            result = observe(args.directory, json.loads(raw))
        elif args.command in {"enable", "disable"}:
            result = configure(args.directory, enabled=args.command == "enable", opt_in=getattr(args, "opt_in", False))
        elif args.command == "pending":
            result = pending(args.directory, args.limit)
        else:
            values = vars(args).copy()
            del values["command"]
            result = submit(**values)
        print(json.dumps(result, ensure_ascii=True))
        return 0
    except (ValueError, OSError, sqlite3.Error, RecursionError):
        # Hook inputs can carry prompts/secrets. Never echo payloads or exception text.
        if args.command == "hook":
            try:
                usage = _usage()
                directory, config = usage._config(args.directory)
                with closing(usage._connect(directory)) as db, db:
                    if config["enabled"] and _settings(db)["enabled"]:
                        db.execute("INSERT INTO diagnostics VALUES ('review_hook_refused',1) "
                                   "ON CONFLICT(id) DO UPDATE SET count=count+1")
            except (ValueError, OSError, sqlite3.Error, RecursionError):
                pass  # No writable authorized ledger; the host warning remains visible.
            print(json.dumps({"systemMessage": "Local task review was not recorded; inspect review configuration and coverage. Work may continue."}))
            return 0
        print("REFUSED: review was not changed; inspect opt-in, task identity, labels and private paths.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
