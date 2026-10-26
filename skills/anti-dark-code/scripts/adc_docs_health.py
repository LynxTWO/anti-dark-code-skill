"""Bounded documentation counts; repository documents are data, never code."""

from __future__ import annotations

import collections
import datetime as dt
import json
import re
import stat
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

MAX_FILES = 50_000
MAX_FILE_BYTES = 2_000_000
MAX_TOTAL_BYTES = 64_000_000
RULE_ROOT = "https://github.com/LynxTWO/anti-dark-code-skill/blob/59f3dc0/skills/anti-dark-code/"
UNKNOWNS_RULE = "Unknowns entry shape and item status (" + RULE_ROOT + "references/00-conventions.md#L87-L102)"
MAP_RULE = "Compact map tables or flow notes (" + RULE_ROOT + "references/02-architecture-map.md#L11-L13)"
BOUNDS_RULE = "Inspect boundedness, exclusions, and unknowns (" + RULE_ROOT + "SKILL.md#L64)"
PATH_RULE = "Local managed/calibration paths must not traverse links (" + RULE_ROOT + "SKILL.md#L78)"

HEADING = re.compile(r"^ {0,3}(#{1,6})\s+(.+?)(?:\s+#+\s*)?$")
FIELD = re.compile(
    r"^\s*(?:[-*+]\s+)?(?:\*\*)?"
    r"(Risk(?: level)?|Status|Blocks|Revisit|Concern|Area or file|Why it matters|Next best check)"
    r"\s*:(?:\*\*)?\s*(.*?)\s*$", re.I)
DATE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b|\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|"
    r"May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|"
    r"Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{1,2}(?:st|nd|rd|th)?\b", re.I)
CANDIDATE = re.compile(r"\bcandidate\b", re.I)
PATH_TOKEN = re.compile(
    r"\[(?P<label>[^\]\n]*)\]\((?P<link>[^)\n]+)\)|`(?P<code>[^`\n]+)`|"
    r"(?<!\S)(?P<bare>[^\s|<>]+\.md)(?=$|[\s|])", re.I)
CLOSED_STATUSES = {"resolved", "fixed", "done", "closed"}
RISK_VALUE = re.compile(r"^(low|medium|high|critical)(?=$|[\s([{,:;.\-])")
STATUS_VALUE = re.compile(r"^(in progress|open|ready|blocked|deferred|resolved|fixed|done|closed)(?=$|[\s([{,:;.\-])")
BLOCKS_VALUE = re.compile(r"^(next release|later|nothing)(?=$|[\s([{,:;.\-])")
REVISIT_DATE = re.compile(
    r"^(?P<markup>`+|\*{1,3}|_{1,3})?(?P<date>\d{4}-\d{2}-\d{2})"
    r"(?(markup)(?P=markup))(?=$|[\s([{,:;.\-])")
REVISIT_MARKUP = re.compile(r"^(`+|\*{1,3}|_{1,3})")


def markdown_lines(text: str):
    """Ignore examples in backtick and tilde fences for fields and headings."""
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not line.strip()[len(token):].strip():
                fence = None
            continue
        if fence is None:
            yield line


def normalized_value(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip(" `*_\t.").lower())


def vocabulary_value(value: str, pattern: re.Pattern[str]) -> str:
    match = pattern.match(value)
    return match.group(1) if match else value


def revisit_date(value: str) -> dt.date | None:
    value = value.strip()
    markup_match = REVISIT_MARKUP.match(value)
    if markup_match:
        markup = markup_match.group(1)
        if len(value) > 2 * len(markup) and value.endswith(markup):
            value = value[len(markup):-len(markup)].strip()
    match = REVISIT_DATE.match(value)
    if match:
        try:
            return dt.date.fromisoformat(match.group("date"))
        except ValueError:
            pass
    return None


def unknown_entries(text: str) -> list[dict[str, Any]]:
    entries = []
    section: list[str] = []
    heading_level = 0
    heading_title = ""
    closed_level = None
    in_closed = False

    def section_fields() -> dict[str, str]:
        fields = {}
        for line in section:
            parts = re.split(r"\s+(?=\*\*(?:Risk(?: level)?|Status|Blocks|Revisit):\*\*)", line, flags=re.I)
            for part in parts:
                match = FIELD.match(part)
                if match:
                    field_name = match.group(1).lower()
                    # Preserve paired date markup before an optional qualifier.
                    fields[field_name] = match.group(2).strip() if field_name == "revisit" else normalized_value(match.group(2))
        return fields

    def finish() -> None:
        if heading_title == "closed items":
            # Closed items is a container at any heading level, not an entry.
            for line in section:
                if re.match(r"^\s*[-*+]\s+\*\*[^*]+\*\*\s*[-:]", line):
                    entries.append({"status": "closed", "risk": "missing", "blocks": "missing", "revisit": "", "open": False, "missing_status": True})
            return
        fields = section_fields()
        if fields or (heading_level >= 3 and any(line.strip() for line in section)):
            status = vocabulary_value(fields.get("status", ""), STATUS_VALUE)
            risk = vocabulary_value(fields.get("risk level", fields.get("risk", "")), RISK_VALUE)
            entries.append({
                "status": "closed" if in_closed else status or "missing",
                "risk": risk or "missing",
                "blocks": vocabulary_value(fields.get("blocks", ""), BLOCKS_VALUE) or "missing",
                "revisit": fields.get("revisit", ""),
                "open": not in_closed and status not in CLOSED_STATUSES,
                "missing_status": not bool(status),
            })

    for line in markdown_lines(text):
        match = HEADING.match(line)
        if not match:
            section.append(line)
            continue
        next_level = len(match.group(1))
        title = normalized_value(match.group(2))
        if (next_level > heading_level and heading_title != "closed items"
                and title != "closed items"
                and (section_fields() or (heading_level >= 3 and any(item.strip() for item in section)))):
            # Evidence notes and other subheadings remain part of this entry.
            section.append(line)
            continue
        finish()
        section = []
        heading_level = next_level
        heading_title = title
        if closed_level is not None and heading_level <= closed_level:
            closed_level = None
        if title == "closed items":
            closed_level = heading_level
        in_closed = closed_level is not None
    finish()
    return entries


def map_counts(text: str) -> dict[str, int]:
    headings = [match.group(2) for line in markdown_lines(text) if (match := HEADING.match(line))]
    return {
        "line_count": len(text.splitlines()),
        "heading_count": len(headings),
        "dated_heading_count": sum(bool(DATE.search(title)) for title in headings),
        "candidate_heading_count": sum(bool(CANDIDATE.search(title)) for title in headings),
        "appended_heading_count": sum(bool(DATE.search(title) or CANDIDATE.search(title)) for title in headings),
    }


def path_kind(label: str) -> str | None:
    label = label.lower().replace("_", "-")
    if "unknown" in label:
        return "unknowns"
    if re.search(r"\bmaps?\b|coverage[- ]ledger", label):
        return "maps"
    return None


def calibration_paths(text: str, suffix: str):
    """Use existing labeled Markdown links/code paths and JSON path values."""
    if suffix == ".json":
        try:
            data = json.loads(text)
        except (ValueError, RecursionError):
            return

        pending = [(data, None)]
        while pending:
            value, kind = pending.pop()
            if isinstance(value, dict):
                pending.extend((child, path_kind(key) or kind) for key, child in value.items())
            elif isinstance(value, list):
                pending.extend((child, kind) for child in value)
            elif isinstance(value, str) and kind:
                yield kind, value, False
    else:
        section_kind = None
        for line in markdown_lines(text):
            heading = HEADING.match(line)
            if heading:
                section_kind = path_kind(heading.group(2))
            for match in PATH_TOKEN.finditer(line):
                value = match.group("link") or match.group("code") or match.group("bare")
                # Classify the label before the path, not unrelated prose after it.
                kind = path_kind(match.group("label") or "") or path_kind(line[:match.start()]) or path_kind(value) or section_kind
                if kind:
                    yield kind, value, match.group("link") is not None or value.startswith(".")


def report(repo: Path, adc, max_open: int | None = None, *, today: dt.date | None = None) -> dict[str, Any]:
    today = today if today is not None else dt.date.today()
    repo = repo.expanduser().resolve()
    if not repo.is_dir():
        raise SystemExit("Repository directory not found")
    findings = []
    scan = {"complete": True, "files_read": 0, "max_files": MAX_FILES,
            "max_file_bytes": MAX_FILE_BYTES, "max_total_bytes": MAX_TOTAL_BYTES,
            "ignored_directories": sorted(adc.IGNORED_DIRS), "skipped_nested_repositories": []}
    contents: dict[Path, str | None] = {}
    bytes_read = 0

    def finding(code, detail, rule, path=None):
        row = {"code": code, "message": f"{detail}; rule: {rule}"}
        if path is not None:
            row["path"] = path.relative_to(repo).as_posix()
        findings.append(row)

    def safe_path(path: Path) -> bool:
        candidate = adc.lexical_absolute(path)
        try:
            candidate.relative_to(repo)
        except ValueError:
            scan["complete"] = False
            finding("unsafe-path", "Skipped a calibrated path outside the repository", PATH_RULE)
            return False
        if adc.symlink_components(candidate, repo):
            scan["complete"] = False
            finding("unsafe-path", "Skipped a symlink or junction", PATH_RULE, candidate)
            return False
        return True

    def read(path: Path) -> str | None:
        nonlocal bytes_read
        if path in contents:
            return contents[path]
        contents[path] = None
        if not safe_path(path):
            return None
        try:
            if not path.exists():
                return None
            if not stat.S_ISREG(path.stat().st_mode):
                raise ValueError("not a regular file")
            if scan["files_read"] >= MAX_FILES or bytes_read >= MAX_TOTAL_BYTES:
                raise ValueError("read budget exhausted")
            limit = min(MAX_FILE_BYTES, MAX_TOTAL_BYTES - bytes_read)
            with path.open("rb") as handle:
                data = handle.read(limit + 1)
            scan["files_read"] += 1
            bytes_read += len(data)
            if len(data) > limit:
                raise ValueError("file exceeds the bounded read budget")
            contents[path] = data.decode("utf-8")
        except (OSError, ValueError) as exc:
            scan["complete"] = False
            reason = str(exc) if isinstance(exc, ValueError) and not isinstance(exc, UnicodeError) else "unreadable UTF-8 file"
            finding("read-limit", f"Skipped document: {reason}", BOUNDS_RULE, path)
        return contents[path]

    def files(directory: Path):
        if not safe_path(directory) or not directory.is_dir():
            return []
        nested = []
        found, truncated = adc.iter_repo_files(directory, max_files=MAX_FILES, skipped_nested_repositories=nested)
        scan["skipped_nested_repositories"].extend(
            (directory / path).relative_to(repo).as_posix() for path in nested)
        if truncated:
            scan["complete"] = False
            finding("scan-limit", "Document traversal reached its file limit", BOUNDS_RULE, directory)
        return found

    paths = {"unknowns": set(), "maps": {
        repo / "docs/architecture/system-map.md", repo / "docs/architecture/service-map.md",
        repo / "service-map.md", repo / "docs/architecture/coverage-ledger.md"}}
    paths["unknowns"].update(path for path in files(repo / "docs/unknowns") if path.suffix.lower() == ".md")
    calibration = adc.calibration_dir(repo)
    paths["maps"].update({calibration / "system-map.md", calibration / "coverage-ledger.md"})
    for source in files(calibration):
        if source.suffix.lower() not in {".md", ".json"}:
            continue
        text = read(source)
        if text is None:
            continue
        own_kind = path_kind(source.stem)
        if source.suffix.lower() == ".md" and own_kind:
            paths[own_kind].add(source)
        for kind, raw, source_relative in calibration_paths(text, source.suffix.lower()):
            try:
                parsed = urlsplit(raw.strip().strip("<>"))
            except ValueError:
                scan["complete"] = False
                finding("unsafe-path", "Skipped a malformed calibrated path", PATH_RULE, source)
                continue
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            value = unquote(parsed.path).replace("\\", "/")
            if any(ord(char) < 32 or ord(char) == 127 for char in value):
                scan["complete"] = False
                finding("unsafe-path", "Skipped a calibrated path containing control characters", PATH_RULE, source)
                continue
            # Stored paths are repo-relative; Markdown relative links use their source.
            base = source.parent if source_relative else repo
            candidate = adc.lexical_absolute(base / value)
            if not safe_path(candidate):
                continue
            if kind == "unknowns" and candidate.is_dir():
                paths[kind].update(path for path in files(candidate) if path.suffix.lower() == ".md")
            elif candidate.suffix.lower() == ".md":
                paths[kind].add(candidate)

    entries = []
    unknown_files = []
    for path in sorted(paths["unknowns"]):
        text = read(path)
        if text is not None:
            unknown_files.append(path.relative_to(repo).as_posix())
            entries.extend(unknown_entries(text))
    unknowns = {
        "rule": UNKNOWNS_RULE, "files": unknown_files, "total_entries": len(entries),
        "by_status": dict(sorted(collections.Counter(row["status"] for row in entries).items())),
        "by_risk": dict(sorted(collections.Counter(row["risk"] for row in entries).items())),
        "by_blocks": dict(sorted(collections.Counter(row["blocks"] for row in entries).items())),
        "open_entries": sum(row["open"] for row in entries),
        "open_without_status": sum(row["open"] and row["missing_status"] for row in entries),
        "open_high_critical": sum(row["open"] and row["risk"] in {"high", "critical"} for row in entries),
        "open_past_revisit": sum(bool(row["open"] and (date := revisit_date(row["revisit"])) is not None and date < today) for row in entries),
    }
    if unknowns["open_without_status"]:
        finding("missing-status", f"{unknowns['open_without_status']} open entries have no status", UNKNOWNS_RULE)
    maps = []
    for path in sorted(paths["maps"]):
        text = read(path)
        if text is None:
            continue
        row = {"path": path.relative_to(repo).as_posix(), "rule": MAP_RULE, **map_counts(text)}
        maps.append(row)
        if row["appended_heading_count"]:
            finding("map-heading-signal", f"{row['appended_heading_count']} dated or candidate headings are an appended-history signal", MAP_RULE, path)
    exceeded = max_open is not None and unknowns["open_entries"] > max_open
    if exceeded:
        finding("max-open", f"Open entries {unknowns['open_entries']} exceed --max-open {max_open}", UNKNOWNS_RULE)
    return {"schema_version": 1, "evaluated_on": today.isoformat(), "unknowns": unknowns, "maps": maps, "scan": scan,
            "max_open": max_open, "max_open_exceeded": exceeded, "findings": findings}


def print_report(result: dict[str, Any]) -> None:
    unknowns = result["unknowns"]
    print(f"EVALUATED_ON {result['evaluated_on']}")
    print("UNKNOWNS " + " ".join(f"{key}={unknowns[key]}" for key in (
        "total_entries", "open_entries", "open_without_status", "open_high_critical", "open_past_revisit")))
    print(f"  rule: {unknowns['rule']}")
    for key in ("by_status", "by_risk", "by_blocks"):
        print(f"  {key}: " + (", ".join(f"{name}={count}" for name, count in unknowns[key].items()) or "none"))
    for row in result["maps"]:
        print(f"MAP {row['path']} " + " ".join(f"{key}={value}" for key, value in row.items() if key not in {"path", "rule"}))
        print(f"  rule: {row['rule']}")
    print(f"SCAN complete={str(result['scan']['complete']).lower()} files_read={result['scan']['files_read']}")
    for row in result["findings"]:
        print(f"  {row['code']}: " + (f"{row['path']}: " if "path" in row else "") + row["message"])
