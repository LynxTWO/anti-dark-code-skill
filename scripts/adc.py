#!/usr/bin/env python3
"""Deterministic local helpers for the Anti-Dark-Code skill.

Standard-library only. Commands are dry-run or read-only unless an explicit write
or execution flag is supplied.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlsplit

SCHEMA_VERSION = 1
SKILL_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = SKILL_ROOT / "assets" / "verification-capabilities.json"
CALIBRATION_TEMPLATE_DIR = SKILL_ROOT / "assets" / "templates" / "calibration"
VERSION = (SKILL_ROOT / "VERSION").read_text(encoding="utf-8").strip() if (SKILL_ROOT / "VERSION").exists() else "unknown"
SOURCE_SCOPE_FILENAME = "SOURCE-SCOPE.json"
SOURCE_SCOPE_KIND = "anti-dark-code-core"
SOURCE_SCOPE_VALUE = "universal"
REPO_BINDING_FILENAME = "repo-binding.json"

LEGACY_CALIBRATION_REL_PATHS = (
    (".anti-dark-code", "calibration"),
    (".claude", "skills", "anti-dark-code", "calibration"),
    (".gemini", "skills", "anti-dark-code", "calibration"),
)

IGNORED_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", ".cache", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".tox", ".nox", ".venv", "venv", "env",
    "node_modules", "bower_components", "vendor", "dist", "build", "out", ".next",
    ".nuxt", ".turbo", "coverage", "target", "bin", "obj", ".gradle", ".terraform",
    "Library", "Temp", "Logs", "DerivedData", "Pods", "__pycache__", ".anti-dark-code",
}

SOURCE_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".go", ".rs", ".java",
    ".kt", ".kts", ".cs", ".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".swift",
    ".rb", ".php", ".scala", ".ex", ".exs", ".fs", ".fsx", ".dart", ".lua", ".gd",
    ".sh", ".bash", ".zsh", ".ps1", ".sql", ".tf", ".hcl", ".vue", ".svelte",
}

TEXT_EXTENSIONS = SOURCE_EXTENSIONS | {
    ".json", ".jsonc", ".yaml", ".yml", ".toml", ".xml", ".md", ".txt", ".ini",
    ".cfg", ".conf", ".properties", ".gradle", ".graphql", ".gql", ".proto", ".csproj",
    ".sln", ".props", ".targets", ".html", ".css", ".scss", ".less", ".csv",
}

LANGUAGE_BY_EXT = {
    ".ts": "TypeScript", ".tsx": "TypeScript", ".js": "JavaScript", ".jsx": "JavaScript",
    ".mjs": "JavaScript", ".cjs": "JavaScript", ".py": "Python", ".go": "Go",
    ".rs": "Rust", ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin", ".cs": "C#",
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".c": "C", ".h": "C/C++",
    ".hpp": "C++", ".swift": "Swift", ".rb": "Ruby", ".php": "PHP", ".scala": "Scala",
    ".ex": "Elixir", ".exs": "Elixir", ".fs": "F#", ".fsx": "F#", ".dart": "Dart",
    ".lua": "Lua", ".gd": "GDScript", ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".ps1": "PowerShell", ".sql": "SQL", ".tf": "Terraform", ".hcl": "HCL",
    ".vue": "Vue", ".svelte": "Svelte",
}

MANIFEST_NAMES = {
    "package.json", "pnpm-workspace.yaml", "yarn.lock", "pnpm-lock.yaml", "package-lock.json",
    "pyproject.toml", "requirements.txt", "Pipfile", "poetry.lock", "uv.lock", "go.mod",
    "Cargo.toml", "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle",
    "settings.gradle.kts", "Gemfile", "composer.json", "mix.exs", "pubspec.yaml", "Package.swift",
    "CMakeLists.txt", "Makefile", "Justfile", "Taskfile.yml", "Dockerfile", "docker-compose.yml",
    "docker-compose.yaml", "project.godot", "ProjectVersion.txt", "*.uproject", "*.sln", "*.csproj",
}

STEERING_NAMES = {
    "AGENTS.md", "CLAUDE.md", "GEMINI.md", "COPILOT_INSTRUCTIONS.md", ".cursorrules",
    ".github/copilot-instructions.md",
}

SIGNAL_SCAN_EXCLUDED_NAMES = {
    "package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock",
    "bun.lock", "bun.lockb", "poetry.lock", "uv.lock", "Pipfile.lock",
    "Cargo.lock", "Gemfile.lock", "composer.lock", "Podfile.lock",
}

MANAGED_SKILL_PREFIXES = {
    (".agents", "skills", "anti-dark-code"),
    (".claude", "skills", "anti-dark-code"),
}
ADC_INTERNAL_PATH_PREFIXES = (
    ".agents/skills/anti-dark-code/",
    ".claude/skills/anti-dark-code/",
    ".anti-dark-code/",
)

CONTENT_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "stateful": (re.compile(r"\b(state|store|reducer|transaction|workflow|state machine)\b", re.I),),
    "workflow_or_ui": (re.compile(r"\b(route|screen|view|component|button|navigation|dialog|window|ui)\b", re.I),),
    "persistence": (re.compile(r"\b(sql|sqlite|postgres|mysql|database|repository|localstorage|indexeddb|save|migration|orm)\b", re.I),),
    "randomness_or_time": (re.compile(r"\b(Math\.random|random\.|rand\(|Date\.now|datetime\.now|time\.time|clock|rng|seed)\b", re.I),),
    "deterministic_or_replay": (re.compile(r"\b(determin|replay|golden|seeded|receipt|event log|snapshot)\b", re.I),),
    "public_api": (re.compile(r"\b(openapi|swagger|router|endpoint|controller|graphql|rpc|public api)\b", re.I),),
    "external_dependencies": (re.compile(r"\b(http|https|fetch\(|axios|requests\.|grpc|websocket|s3|stripe|twilio|firebase|supabase)\b", re.I),),
    "concurrency_or_async": (re.compile(r"\b(async|await|thread|mutex|semaphore|worker|queue|concurrent|parallel|coroutine)\b", re.I),),
    "security_sensitive": (re.compile(r"\b(auth|oauth|jwt|session|permission|role|secret|access token|refresh token|api token|encrypt|decrypt|password)\b", re.I),),
    "financial_or_entitlement": (re.compile(r"\b(payment|billing|price|currency|purchase|entitlement|subscription|economy|wallet)\b", re.I),),
    "generated_or_serialized_output": (re.compile(r"\b(serialize|deserialize|snapshot|golden|generator|codegen|compiler|rendered? output|export (?:file|data|artifact|report|image|audio|video))\b", re.I),),
    "emergent_or_simulation": (re.compile(r"\b(simulation|simulate|world tick|agent behavior|economy|population|ecology|combat|physics)\b", re.I),),
    "performance_sensitive": (re.compile(r"\b(performance|benchmark|latency|throughput|fps|frame time|memory|cache|memo|profil)\b", re.I),),
    "long_running_or_background": (re.compile(r"\b(background|daemon|worker|scheduler|cron|long running|foreground|lifecycle)\b", re.I),),
    "multiple_implementations": (re.compile(r"\b(adapter|implementation|legacy|compat|native|web|reference implementation)\b", re.I),),
    "migration_or_rewrite": (re.compile(r"\b(migration|migrate|rewrite|replacement|legacy|compatibility)\b", re.I),),
    "batch_or_chunk_processing": (re.compile(r"\b(batch|chunk|partition|page size|window|catch.?up)\b", re.I),),
    "search_or_numerical": (re.compile(r"\b(search|rank|score|vector|matrix|numeric|float|geometry|optimization)\b", re.I),),
    "parser_or_protocol": (re.compile(r"\b(parser|parse|protocol|codec|decoder|encoder|grammar|tokenizer)\b", re.I),),
    "rendered_output": (re.compile(r"\b(render|canvas|dom|view model|screenshot|svg|pdf|report)\b", re.I),),
    "cross_platform": (re.compile(r"\b(windows|linux|macos|android|ios|cross.?platform|native|web)\b", re.I),),
    "release_sensitive": (re.compile(r"\b(deploy|release|publish|migration|production|app store|play store|terraform apply)\b", re.I),),
    "localization": (re.compile(r"\b(i18n|l10n|locale|localization|translation|transcreation)\b", re.I),),
}

SECRET_PATTERNS = [
    re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key|private[_-]?key)\b\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+\-/]+=*"),
]

POSIX_USER_PATH_RE = re.compile(r"(?<![A-Za-z0-9])/(?:home|Users)/([^/\s`\"'<>]+)/")
WINDOWS_USER_PATH_RE = re.compile(r"(?i)(?<![A-Za-z0-9])[A-Z]:\\Users\\([^\\\s`\"'<>]+)\\")
PLACEHOLDER_PATH_SEGMENTS = {
    "<username>", "<user>", "username", "user", "your-user", "your-username",
    "example", "example-user", "name", "placeholder",
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def eprint(*args: Any) -> None:
    print(*args, file=sys.stderr)


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        if default is not None:
            return default
        raise
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False, dir=path.parent) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def write_json_atomic(path: Path, data: Any) -> None:
    write_text_atomic(path, json.dumps(data, indent=2, sort_keys=False) + "\n")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalized_json_hash(data: Any, volatile_keys: set[str] | None = None) -> str:
    volatile_keys = volatile_keys or set()

    def clean(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: clean(v) for k, v in sorted(value.items()) if k not in volatile_keys}
        if isinstance(value, list):
            return [clean(v) for v in value]
        return value

    payload = json.dumps(clean(data), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def calibration_payload_files(path: Path) -> list[Path]:
    if not path.exists() or not path.is_dir():
        return []
    return sorted(
        item
        for item in path.rglob("*")
        if item.is_file()
        and item.name != ".DS_Store"
        and item.suffix != ".pyc"
        and "__pycache__" not in item.parts
    )


def calibration_substantive_files(path: Path) -> list[Path]:
    return [item for item in calibration_payload_files(path) if item.name != REPO_BINDING_FILENAME]


def normalize_git_remote(value: str) -> str:
    raw = value.strip().replace("\\", "/").rstrip("/")
    if not raw:
        return raw

    def strip_git_suffix(path: str) -> str:
        cleaned = re.sub(r"/+", "/", path.strip("/"))
        return cleaned[:-4] if cleaned.endswith(".git") else cleaned

    # Keep Windows drive paths out of the SCP-style remote parser.
    if re.match(r"^[A-Za-z]:/", raw):
        return strip_git_suffix(os.path.normcase(os.path.normpath(raw)).replace("\\", "/"))

    # Canonicalize common SCP-style Git remotes, such as git@example.com:org/repo.git.
    if "://" not in raw:
        match = re.match(r"^(?:[^@/\s]+@)?([^:/\s]+):(.+)$", raw)
        if match:
            host = match.group(1).lower()
            path = strip_git_suffix(match.group(2))
            return f"{host}/{path}"

    if "://" in raw:
        try:
            parsed = urlsplit(raw)
            host = (parsed.hostname or "").lower()
            port = parsed.port
        except ValueError:
            parsed = None
            host = ""
            port = None
        if parsed and host:
            default_ports = {"ssh": 22, "https": 443, "http": 80, "git": 9418}
            port_text = f":{port}" if port and port != default_ports.get(parsed.scheme.lower()) else ""
            path = strip_git_suffix(parsed.path)
            return f"{host}{port_text}/{path}"

    return strip_git_suffix(raw)


def compute_repository_binding(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    origin = git_output(repo, ["config", "--get", "remote.origin.url"])
    roots_raw = git_output(repo, ["rev-list", "--max-parents=0", "HEAD"])
    roots = sorted({line.strip() for line in (roots_raw or "").splitlines() if line.strip()})
    is_git = git_output(repo, ["rev-parse", "--is-inside-work-tree"]) == "true"
    normalized_path = os.path.normcase(str(repo))
    path_hash = sha256_bytes(normalized_path.encode("utf-8"))

    components: dict[str, Any] = {
        "origin_present": bool(origin),
        "origin_sha256": None,
        "root_commits_present": bool(roots),
        "root_commits_sha256": None,
        "path_sha256": None,
    }
    identity_payload: dict[str, Any]

    if origin:
        normalized_origin = normalize_git_remote(origin)
        components["origin_sha256"] = sha256_bytes(normalized_origin.encode("utf-8"))
    if roots:
        roots_text = "\n".join(roots)
        components["root_commits_sha256"] = sha256_bytes(roots_text.encode("utf-8"))

    if origin:
        # The canonical remote is the stable identity. Root commits remain hashed
        # evidence, but they do not change the binding after a first commit or
        # ordinary history maintenance.
        identity_payload = {
            "kind": "git-origin",
            "origin_sha256": components["origin_sha256"],
        }
        identity_method = "git-origin-sha256"
    elif is_git:
        components["path_sha256"] = path_hash
        identity_payload = {"kind": "git-local-path", "path_sha256": path_hash}
        identity_method = "git-local-path-sha256"
    else:
        components["path_sha256"] = path_hash
        identity_payload = {"kind": "non-git-path", "path_sha256": path_hash}
        identity_method = "non-git-path-sha256"

    repository_id = "adc-repo-" + normalized_json_hash(identity_payload)[:32]
    return {
        "schema_version": SCHEMA_VERSION,
        "binding_status": "bound",
        "repository_id": repository_id,
        "identity_method": identity_method,
        "identity_components": components,
    }


def assess_repository_binding(repo: Path, calibration: Path) -> dict[str, Any]:
    current = compute_repository_binding(repo)
    binding_path = calibration / REPO_BINDING_FILENAME
    all_files = calibration_payload_files(calibration)
    substantive = calibration_substantive_files(calibration)
    binding: dict[str, Any] | None = None
    binding_error: str | None = None
    if binding_path.exists():
        try:
            loaded = json.loads(binding_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                binding = loaded
            else:
                binding_error = "repo-binding.json is not a JSON object"
        except (OSError, json.JSONDecodeError) as exc:
            binding_error = f"repo-binding.json is invalid: {exc}"

    if not all_files:
        status = "new"
    elif binding_error:
        status = "invalid"
    elif not binding or binding.get("binding_status") != "bound" or not binding.get("repository_id"):
        status = "unbound"
    elif binding.get("repository_id") == current["repository_id"]:
        status = "match"
    else:
        status = "mismatch"

    return {
        "status": status,
        "calibration_path": str(calibration),
        "file_count": len(all_files),
        "substantive_file_count": len(substantive),
        "binding_error": binding_error,
        "stored_repository_id": binding.get("repository_id") if binding else None,
        "current_repository_id": current["repository_id"],
        "identity_method": current["identity_method"],
        "current": current,
        "binding": binding,
    }


def write_repository_binding(
    calibration: Path,
    assessment: dict[str, Any],
    *,
    accepted_unbound: bool = False,
    rebound: bool = False,
) -> Path:
    now = utc_now()
    current = assessment["current"]
    existing = assessment.get("binding") if isinstance(assessment.get("binding"), dict) else {}
    raw_previous = existing.get("previous_repository_ids", []) if isinstance(existing, dict) else []
    previous = list(raw_previous) if isinstance(raw_previous, list) else []
    old_id = existing.get("repository_id") if isinstance(existing, dict) else None
    if rebound and old_id and old_id != current["repository_id"]:
        previous.append({"repository_id": old_id, "replaced_at_utc": now})

    bound_at = existing.get("bound_at_utc") if assessment.get("status") == "match" else now
    notes = [
        "This calibration belongs to one repository identity.",
        "Do not transplant this calibration directory into another repository.",
    ]
    if accepted_unbound:
        notes.append("Legacy unbound calibration was accepted explicitly during migration.")
    if rebound:
        notes.append("The repository binding was changed explicitly after identity review.")

    data = {
        "schema_version": SCHEMA_VERSION,
        "binding_status": "bound",
        "repository_id": current["repository_id"],
        "identity_method": current["identity_method"],
        "identity_components": current["identity_components"],
        "bound_at_utc": bound_at,
        "last_verified_at_utc": now,
        "previous_repository_ids": previous,
        "notes": notes,
    }
    path = calibration / REPO_BINDING_FILENAME
    write_json_atomic(path, data)
    return path


def initialize_binding_for_empty_calibration(repo: Path, calibration: Path) -> Path | None:
    if calibration_payload_files(calibration):
        return None
    calibration.mkdir(parents=True, exist_ok=True)
    assessment = assess_repository_binding(repo, calibration)
    return write_repository_binding(calibration, assessment)


def legacy_calibration_locations(repo: Path, target_calibration: Path) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for parts in LEGACY_CALIBRATION_REL_PATHS:
        candidate = repo.joinpath(*parts)
        if candidate.resolve() == target_calibration.resolve() or not candidate.exists():
            continue
        files = calibration_payload_files(candidate)
        if not files:
            continue
        assessment = assess_repository_binding(repo, candidate)
        found.append({
            "path": candidate.relative_to(repo).as_posix(),
            "file_count": len(files),
            "binding_status": assessment["status"],
            "auto_migration": candidate == repo / ".anti-dark-code" / "calibration",
        })
    return found


def is_placeholder_path_segment(value: str) -> bool:
    lowered = value.strip().lower()
    return (
        lowered in PLACEHOLDER_PATH_SEGMENTS
        or "<" in value
        or "{" in value
        or "$" in value
        or "%" in value
    )


def personal_absolute_path_hits(content: str) -> list[str]:
    hits: list[str] = []
    for match in POSIX_USER_PATH_RE.finditer(content):
        if not is_placeholder_path_segment(match.group(1)):
            hits.append(match.group(0))
    for match in WINDOWS_USER_PATH_RE.finditer(content):
        if not is_placeholder_path_segment(match.group(1)):
            hits.append(match.group(0))
    return sorted(set(hits))


def validate_calibration_templates(template_dir: Path) -> list[str]:
    errors: list[str] = []
    if not template_dir.exists() or not template_dir.is_dir():
        return [f"Calibration templates not found: {template_dir}"]

    binding_path = template_dir / REPO_BINDING_FILENAME
    if not binding_path.exists():
        errors.append(f"Missing calibration template {REPO_BINDING_FILENAME}")
    else:
        try:
            binding = json.loads(binding_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Invalid calibration binding template: {exc}")
        else:
            if not isinstance(binding, dict):
                errors.append("Calibration binding template is not a JSON object")
            else:
                if binding.get("binding_status") != "unbound-template":
                    errors.append("Calibration binding template must remain unbound-template")
                if binding.get("repository_id") is not None:
                    errors.append("Calibration binding template contains a repository id")
                if binding.get("bound_at_utc") is not None or binding.get("last_verified_at_utc") is not None:
                    errors.append("Calibration binding template contains repository timestamps")

    gates_path = template_dir / "gates.json"
    if not gates_path.exists():
        errors.append("Missing calibration template gates.json")
    else:
        try:
            gates_data = json.loads(gates_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Invalid calibration gate template: {exc}")
        else:
            policy = gates_data.get("execution_policy", {}) if isinstance(gates_data, dict) else {}
            if policy.get("owner_confirmed_safe_to_execute"):
                errors.append("Calibration gate template enables global execution confirmation")
            for gate in gates_data.get("gates", []) if isinstance(gates_data, dict) else []:
                if not isinstance(gate, dict):
                    errors.append("Calibration gate template contains a non-object gate")
                    continue
                if gate.get("enabled"):
                    errors.append(f"Calibration gate template enables gate {gate.get('id', '?')}")
                if str(gate.get("review_status", "")).lower() == "approved":
                    errors.append(f"Calibration gate template pre-approves gate {gate.get('id', '?')}")

    for path in calibration_payload_files(template_dir):
        if path.suffix.lower() not in TEXT_EXTENSIONS | {".yaml", ".yml"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        hits = personal_absolute_path_hits(content)
        if hits:
            errors.append(
                f"Calibration template {path.relative_to(template_dir)} contains likely personal absolute paths: "
                + ", ".join(hits)
            )
    return errors


def inspect_gate_config_for_migration(path: Path) -> dict[str, Any]:
    result = {
        "present": path.exists(),
        "valid": True,
        "error": None,
        "enabled_count": 0,
        "approved_count": 0,
        "owner_confirmed": False,
    }
    if not path.exists():
        return result
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result.update({"valid": False, "error": f"invalid gates.json: {exc}"})
        return result
    if not isinstance(data, dict) or not isinstance(data.get("gates", []), list):
        result.update({"valid": False, "error": "gates.json must be an object with a gates array"})
        return result
    result["owner_confirmed"] = bool(data.get("execution_policy", {}).get("owner_confirmed_safe_to_execute"))
    for gate in data.get("gates", []):
        if not isinstance(gate, dict):
            result.update({"valid": False, "error": "gates.json contains a non-object gate"})
            return result
        if gate.get("enabled"):
            result["enabled_count"] += 1
        if str(gate.get("review_status", "")).lower() == "approved":
            result["approved_count"] += 1
    return result


def reset_gate_approvals(path: Path, reason: str) -> dict[str, Any]:
    inspection = inspect_gate_config_for_migration(path)
    if not inspection["present"]:
        return {**inspection, "reset": False, "reset_gate_count": 0}
    if not inspection["valid"]:
        raise SystemExit(f"Cannot reset migrated gate approvals: {inspection['error']}")

    data = read_json(path)
    policy = data.setdefault("execution_policy", {})
    policy["owner_confirmed_safe_to_execute"] = False
    policy["notes"] = (
        "Gate approvals were reset during migration. Review every exact command in this repository, "
        "approve gates individually, then reconfirm execution safety."
    )
    reset_count = 0
    for gate in data.get("gates", []):
        if not isinstance(gate, dict):
            continue
        if gate.get("enabled") or str(gate.get("review_status", "")).lower() != "proposed":
            reset_count += 1
        gate["enabled"] = False
        gate["review_status"] = "proposed"
        gate["migration_review_required"] = reason
    write_json_atomic(path, data)
    return {**inspection, "reset": True, "reset_gate_count": reset_count}


def inspect_install_source(source: Path, repo: Path) -> dict[str, Any]:
    marker_path = source / SOURCE_SCOPE_FILENAME
    marker: dict[str, Any] | None = None
    marker_error: str | None = None
    if marker_path.exists():
        try:
            loaded = json.loads(marker_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                marker = loaded
            else:
                marker_error = f"{SOURCE_SCOPE_FILENAME} is not a JSON object"
        except (OSError, json.JSONDecodeError) as exc:
            marker_error = f"{SOURCE_SCOPE_FILENAME} is invalid: {exc}"
    else:
        marker_error = f"{SOURCE_SCOPE_FILENAME} is missing"

    marker_valid = bool(
        marker
        and marker.get("kind") == SOURCE_SCOPE_KIND
        and marker.get("scope") == SOURCE_SCOPE_VALUE
        and marker.get("repo_calibration_transfer") == "prohibited"
    )
    if marker and not marker_valid and marker_error is None:
        marker_error = f"{SOURCE_SCOPE_FILENAME} does not identify a universal Anti-Dark-Code core"

    source_calibration = source / "calibration"
    source_calibration_files = calibration_payload_files(source_calibration)
    unsafe_issues: list[str] = []
    if not marker_valid:
        unsafe_issues.append(marker_error or "source scope marker is invalid")
    if path_is_within(source, repo):
        unsafe_issues.append("source skill is located inside the target repository")
    if (source / ".adc-managed.json").exists():
        unsafe_issues.append("source skill contains a repo-local managed-install manifest")
    if source_calibration_files:
        unsafe_issues.append("source skill contains repo-owned top-level calibration")

    template_errors = validate_calibration_templates(source / "assets" / "templates" / "calibration")
    return {
        "marker_valid": marker_valid,
        "marker_error": marker_error,
        "source_inside_target_repo": path_is_within(source, repo),
        "source_has_managed_install_manifest": (source / ".adc-managed.json").exists(),
        "source_calibration_ignored": [item.relative_to(source_calibration).as_posix() for item in source_calibration_files],
        "unsafe_issues": unsafe_issues,
        "template_errors": template_errors,
    }


def is_adc_internal_relpath(path: str) -> bool:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.lstrip("/")
    return any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in ADC_INTERNAL_PATH_PREFIXES)


def is_managed_skill_parts(parts: Sequence[str]) -> bool:
    return any(tuple(parts[:len(prefix)]) == prefix for prefix in MANAGED_SKILL_PREFIXES)


def is_ignored(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        parts = path.parts
    if is_managed_skill_parts(parts):
        return True
    return any(part in IGNORED_DIRS for part in parts[:-1])


def iter_repo_files(root: Path, max_files: int = 50_000) -> tuple[list[Path], bool]:
    files: list[Path] = []
    truncated = False
    for current, dirs, names in os.walk(root):
        current_path = Path(current)
        try:
            current_parts = current_path.relative_to(root).parts
        except ValueError:
            current_parts = current_path.parts
        dirs[:] = sorted(
            d for d in dirs
            if d not in IGNORED_DIRS and not is_managed_skill_parts((*current_parts, d))
        )
        for name in sorted(names):
            path = current_path / name
            if is_ignored(path, root):
                continue
            files.append(path)
            if len(files) >= max_files:
                truncated = True
                return files, truncated
    return files, truncated


def file_matches_manifest(path: Path) -> bool:
    name = path.name
    return any(fnmatch.fnmatch(name, pattern) for pattern in MANIFEST_NAMES)


def likely_test(path: Path) -> bool:
    lower = path.as_posix().lower()
    name = path.name.lower()
    return (
        "/test/" in lower or "/tests/" in lower or "/__tests__/" in lower or
        name.startswith("test_") or name.endswith("_test.py") or ".test." in name or
        ".spec." in name or name.endswith("tests.cs") or name.endswith("test.cs")
    )


def git_output(repo: Path, args: Sequence[str]) -> str | None:
    try:
        proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=15, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def git_bytes(repo: Path, args: Sequence[str], timeout: int = 15) -> bytes | None:
    try:
        proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, timeout=timeout, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def git_paths(repo: Path, args: Sequence[str]) -> list[str] | None:
    raw = git_bytes(repo, [*args, "-z"])
    if raw is None:
        return None
    return [item.decode("utf-8", errors="surrogateescape") for item in raw.split(b"\0") if item]


def current_source_identity(repo: Path) -> dict[str, Any]:
    commit = git_output(repo, ["rev-parse", "HEAD"])
    branch = git_output(repo, ["rev-parse", "--abbrev-ref", "HEAD"])
    status_raw = git_bytes(repo, [
        "status", "--porcelain=v1", "--untracked-files=all", "-z", "--", ".",
        ":(exclude).agents/skills/anti-dark-code/**",
        ":(exclude).claude/skills/anti-dark-code/**",
        ":(exclude).anti-dark-code/**",
    ])
    return {
        "git_commit": commit,
        "git_branch": branch,
        "worktree_clean": status_raw == b"" if status_raw is not None else None,
        "worktree_status_sha256": sha256_bytes(status_raw) if status_raw is not None else None,
        "identity_excludes": list(ADC_INTERNAL_PATH_PREFIXES),
    }


def detect_js_runner(package_dir: Path, repo: Path, data: dict[str, Any]) -> str:
    declared = data.get("packageManager")
    if isinstance(declared, str) and declared.strip():
        name = declared.split("@", 1)[0].strip().lower()
        if name in {"npm", "pnpm", "yarn", "bun"}:
            return name

    current = package_dir.resolve()
    repo = repo.resolve()
    while True:
        for filename, runner in (
            ("pnpm-lock.yaml", "pnpm"),
            ("yarn.lock", "yarn"),
            ("bun.lockb", "bun"),
            ("bun.lock", "bun"),
            ("package-lock.json", "npm"),
            ("npm-shrinkwrap.json", "npm"),
        ):
            if (current / filename).exists():
                return runner
        if current == repo or repo not in current.parents:
            break
        current = current.parent
    return "npm"


def js_run_argv(runner: str, script_name: str) -> list[str]:
    return [runner, "run", script_name]


def add_evidence(signals: dict[str, dict[str, Any]], signal: str, evidence: str, limit: int = 12) -> None:
    entry = signals.setdefault(signal, {"present": False, "evidence": []})
    entry["present"] = True
    if evidence not in entry["evidence"] and len(entry["evidence"]) < limit:
        entry["evidence"].append(evidence)


def parse_package_json(path: Path, repo: Path, profile: dict[str, Any]) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return
    deps: dict[str, Any] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        value = data.get(key)
        if isinstance(value, dict):
            deps.update(value)
    dep_names = {str(k).lower() for k in deps}
    scripts = data.get("scripts") if isinstance(data.get("scripts"), dict) else {}
    package_rel = rel(path, repo)
    runner = detect_js_runner(path.parent, repo, data)

    type_hints = profile.setdefault("_type_hints", set())
    if any(x in dep_names for x in {"react", "next", "vite", "@angular/core", "vue", "svelte", "solid-js"}):
        type_hints.add("frontend")
    if any(x in dep_names for x in {"express", "fastify", "@nestjs/core", "koa", "hapi", "apollo-server", "@apollo/server"}):
        type_hints.add("service-web")
    if any(x in dep_names for x in {"react-native", "expo", "@capacitor/core", "cordova"}):
        type_hints.add("mobile-native")
    if any(x in dep_names for x in {"electron", "@tauri-apps/api", "commander", "yargs", "oclif"}):
        type_hints.add("cli-desktop")
    if any(x in dep_names for x in {"three", "phaser", "pixi.js", "babylonjs", "@babylonjs/core"}):
        type_hints.add("game-simulation")
    if any(x in dep_names for x in {"tensorflow", "@tensorflow/tfjs", "onnxruntime-node", "langchain", "openai"}):
        type_hints.add("ai-data")
    if "workspaces" in data or path.parent != repo:
        type_hints.add("monorepo")

    for name, command in sorted(scripts.items()):
        if not isinstance(command, str):
            continue
        lname = name.lower()
        level = None
        resource = "light"
        if any(word in lname for word in ("format:check", "format-check", "typecheck", "type-check", "lint", "validate", "check")):
            level = 0
        elif any(word in lname for word in ("unit", "contract", "integration", "test:changed", "test:affected")):
            level = 1
        elif any(word in lname for word in ("fuzz", "property", "mutation", "e2e", "smoke", "benchmark", "perf")):
            level = 2
            resource = "medium"
        elif lname in {"test", "test:ci", "ci", "build"} or any(word in lname for word in ("full", "all", "release")):
            level = 3
            resource = "heavy"
        if level is None:
            continue
        script_slug = re.sub(r"[^a-z0-9]+", "-", lname).strip("-")
        cwd_rel = rel(path.parent, repo) or "."
        scope_slug = re.sub(r"[^a-z0-9]+", "-", cwd_rel.lower()).strip("-")
        gate_id = f"{runner}-{script_slug}" if cwd_rel == "." else f"{runner}-{scope_slug}-{script_slug}"
        profile["exact_commands"].append({
            "id": gate_id,
            "level": level,
            "argv": js_run_argv(runner, name),
            "enabled": False,
            "source": f"{package_rel}#scripts.{name}",
            "source_definition_sha256": sha256_bytes(command.encode("utf-8")),
            "confidence": "verified",
            "timeout_seconds": 900 if resource == "heavy" else 300,
            "resource_class": resource,
            "cwd": cwd_rel,
            "include_globs": [],
            "exclude_globs": [],
        })

    for dep in dep_names:
        if any(term in dep for term in ("zod", "joi", "yup", "ajv", "pydantic", "jsonschema")):
            add_evidence(profile["signals"], "schema_validation_present", package_rel)
        if any(term in dep for term in ("dependency-cruiser", "madge", "eslint-plugin-boundaries", "archunit")):
            add_evidence(profile["signals"], "architecture_tool_present", package_rel)
        if any(term in dep for term in ("stryker", "mutmut", "pitest", "cargo-mutants")):
            add_evidence(profile["signals"], "mutation_tool_present", package_rel)
        if any(term in dep for term in ("fast-check", "hypothesis", "quickcheck", "proptest")):
            add_evidence(profile["signals"], "property_tool_present", package_rel)


def add_conventional_commands(repo: Path, profile: dict[str, Any], manifests: set[str]) -> None:
    existing_ids = {item["id"] for item in profile["exact_commands"]}

    def add(item: dict[str, Any]) -> None:
        if item["id"] not in existing_ids:
            profile["exact_commands"].append(item)
            existing_ids.add(item["id"])

    if "pyproject.toml" in manifests or "requirements.txt" in manifests:
        add({"id":"python-pytest", "level":3, "argv":[sys.executable, "-m", "pytest"], "enabled":False,
             "source":"conventional candidate from Python manifest", "confidence":"inferred", "timeout_seconds":900,
             "resource_class":"heavy", "cwd":".", "include_globs":[], "exclude_globs":[]})
    if "Cargo.toml" in manifests:
        add({"id":"cargo-check", "level":0, "argv":["cargo", "check", "--all-targets"], "enabled":False,
             "source":"conventional candidate from Cargo.toml", "confidence":"inferred", "timeout_seconds":600,
             "resource_class":"medium", "cwd":".", "include_globs":[], "exclude_globs":[]})
        add({"id":"cargo-test", "level":3, "argv":["cargo", "test", "--all-targets"], "enabled":False,
             "source":"conventional candidate from Cargo.toml", "confidence":"inferred", "timeout_seconds":1200,
             "resource_class":"heavy", "cwd":".", "include_globs":[], "exclude_globs":[]})
    if "go.mod" in manifests:
        add({"id":"go-test", "level":3, "argv":["go", "test", "./..."], "enabled":False,
             "source":"conventional candidate from go.mod", "confidence":"inferred", "timeout_seconds":900,
             "resource_class":"heavy", "cwd":".", "include_globs":[], "exclude_globs":[]})
    if any(name.endswith(".sln") or name.endswith(".csproj") for name in manifests):
        add({"id":"dotnet-test", "level":3, "argv":["dotnet", "test"], "enabled":False,
             "source":"conventional candidate from .NET manifest", "confidence":"inferred", "timeout_seconds":1200,
             "resource_class":"heavy", "cwd":".", "include_globs":[], "exclude_globs":[]})
    if any(name.endswith(".tf") for name in manifests) or "terraform" in profile.get("repo_types", []):
        add({"id":"terraform-fmt", "level":0, "argv":["terraform", "fmt", "-check", "-recursive"], "enabled":False,
             "source":"conventional candidate from Terraform files", "confidence":"inferred", "timeout_seconds":180,
             "resource_class":"light", "cwd":".", "include_globs":["**/*.tf"], "exclude_globs":[]})


def probe_repo(repo: Path, max_files: int = 50_000, content_scan_limit: int = 4_000) -> dict[str, Any]:
    repo = repo.resolve()
    if not repo.exists() or not repo.is_dir():
        raise SystemExit(f"Repo directory not found: {repo}")

    files, truncated = iter_repo_files(repo, max_files=max_files)
    ext_counts: collections.Counter[str] = collections.Counter()
    lang_counts: collections.Counter[str] = collections.Counter()
    source_count = 0
    test_count = 0
    total_bytes = 0
    manifests: list[str] = []
    ci_files: list[str] = []
    steering_files: list[str] = []
    profile: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_by": f"anti-dark-code {VERSION} adc.py probe",
        "generated_at_utc": utc_now(),
        "repo_root": ".",
        "source_identity": current_source_identity(repo),
        "scan": {
            "complete": not truncated,
            "files_seen": len(files),
            "files_scanned_for_indicators": 0,
            "scan_limit": max_files,
            "content_scan_limit": content_scan_limit,
            "ignored_directories": sorted(IGNORED_DIRS),
        },
        "repo_types": [],
        "languages": [],
        "manifests": manifests,
        "ci_files": ci_files,
        "steering_files": steering_files,
        "counts": {},
        "signals": {},
        "exact_commands": [],
        "notes": [],
        "_type_hints": set(),
    }

    for path in files:
        try:
            size = path.stat().st_size
        except OSError:
            continue
        total_bytes += size
        suffix = path.suffix.lower()
        ext_counts[suffix or "<none>"] += 1
        if suffix in SOURCE_EXTENSIONS:
            source_count += 1
            lang_counts[LANGUAGE_BY_EXT.get(suffix, suffix)] += 1
        if likely_test(path):
            test_count += 1
        r = rel(path, repo)
        if file_matches_manifest(path):
            manifests.append(r)
        if r.startswith(".github/workflows/") or r.startswith(".gitlab-ci") or path.name in {"Jenkinsfile", "azure-pipelines.yml", "bitbucket-pipelines.yml"}:
            ci_files.append(r)
        if r in STEERING_NAMES or path.name in STEERING_NAMES:
            steering_files.append(r)
        if path.name == "package.json" and size <= 2_000_000:
            parse_package_json(path, repo, profile)

    signals: dict[str, dict[str, Any]] = profile["signals"]
    if test_count:
        add_evidence(signals, "has_tests", f"{test_count} test-like files")
    if ci_files:
        add_evidence(signals, "has_ci", ci_files[0])
    if source_count > 250:
        add_evidence(signals, "large_repo", f"{source_count} source files")

    # Structure-based evidence is cheap and stronger than content keywords.
    structure_rules = {
        "stateful": ("state", "store", "models", "domain"),
        "workflow_or_ui": ("app", "pages", "screens", "components", "ui", "views"),
        "persistence": ("db", "database", "migrations", "storage", "repositories"),
        "emergent_or_simulation": ("engine", "simulation", "world", "game", "physics"),
        "long_running_or_background": ("workers", "jobs", "scheduler", "background"),
        "localization": ("locales", "i18n", "translations"),
    }
    top_parts = {p.parts[0].lower() for p in (path.relative_to(repo) for path in files) if p.parts}
    for signal, names in structure_rules.items():
        for name in names:
            if name in top_parts:
                add_evidence(signals, signal, f"top-level path: {name}/")

    # Bounded content scan. Record paths and matched signal names, never matched values.
    scanned = 0
    for path in files:
        if scanned >= content_scan_limit:
            break
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if path.name in SIGNAL_SCAN_EXCLUDED_NAMES or path.name.endswith((".min.js", ".min.css")):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS or size > 300_000 or size == 0:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        scanned += 1
        r = rel(path, repo)
        for signal, patterns in CONTENT_PATTERNS.items():
            if any(pattern.search(text) for pattern in patterns):
                add_evidence(signals, signal, r)
    profile["scan"]["files_scanned_for_indicators"] = scanned
    if scanned >= content_scan_limit and len(files) > scanned:
        profile["notes"].append("Indicator content scan reached its bound. Signals are evidence of presence, not proof of absence.")
    if truncated:
        profile["notes"].append("File enumeration reached its bound. Counts and absence claims are partial.")

    manifest_basenames = {Path(m).name for m in manifests}
    type_hints: set[str] = profile.pop("_type_hints")
    all_rel = {rel(path, repo) for path in files}

    if "pnpm-workspace.yaml" in manifest_basenames or any(name in manifest_basenames for name in {"turbo.json", "nx.json"}) or sum(1 for m in manifests if m.endswith("package.json")) > 2:
        type_hints.add("monorepo")
    if "project.godot" in manifest_basenames or any(name.endswith(".uproject") for name in manifest_basenames) or "ProjectSettings/ProjectVersion.txt" in all_rel or "assets" in top_parts:
        type_hints.add("game-simulation")
    if any(path.suffix.lower() == ".tf" for path in files) or any(r.startswith(("terraform/", "infra/", "infrastructure/", "k8s/", "helm/")) for r in all_rel):
        type_hints.add("infra-as-code")
    if any(path.suffix.lower() == ".ipynb" for path in files) or any(part in top_parts for part in {"notebooks", "pipelines", "models", "datasets"}):
        type_hints.add("ai-data")
    if any(name in manifest_basenames for name in {"go.mod", "Cargo.toml", "pyproject.toml", "pom.xml"}) and not type_hints:
        type_hints.add("library-sdk")
    if "app" in top_parts and "frontend" not in type_hints and "mobile-native" not in type_hints:
        type_hints.add("service-web")
    if source_count < 25 and not type_hints:
        type_hints.add("small-new")
    if not type_hints:
        type_hints.add("mixed")
    if len(type_hints - {"monorepo"}) > 1:
        type_hints.add("mixed")

    profile["repo_types"] = sorted(type_hints)
    profile["languages"] = [{"name": name, "source_files": count} for name, count in lang_counts.most_common()]
    profile["manifests"] = sorted(set(manifests))
    profile["ci_files"] = sorted(set(ci_files))
    profile["steering_files"] = sorted(set(steering_files))
    profile["counts"] = {
        "total_files": len(files),
        "source_files": source_count,
        "test_like_files": test_count,
        "total_bytes": total_bytes,
        "extensions": dict(ext_counts.most_common(30)),
    }

    # Add conventional candidates only after type classification.
    if any(path.suffix.lower() == ".tf" for path in files):
        manifest_basenames.add("*.tf")
    add_conventional_commands(repo, profile, manifest_basenames)
    profile["exact_commands"] = sorted(profile["exact_commands"], key=lambda x: (x["level"], x["id"], x.get("cwd", ".")))

    # Normalize signals. Absence is unknown under a bounded scan, not verified false.
    for name in sorted(set(CONTENT_PATTERNS) | {"has_tests", "has_ci", "large_repo", "schema_validation_present", "architecture_tool_present", "mutation_tool_present", "property_tool_present"}):
        profile["signals"].setdefault(name, {"present": False, "evidence": []})
    profile["signals"] = {name: profile["signals"][name] for name in sorted(profile["signals"])}
    return profile


def calibration_dir(repo: Path) -> Path:
    canonical = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
    if canonical.exists() or (repo / ".agents" / "skills" / "anti-dark-code").exists():
        return canonical
    return repo / ".anti-dark-code" / "calibration"


def write_profile(repo: Path, profile: dict[str, Any]) -> Path:
    calibration = calibration_dir(repo)
    initialize_binding_for_empty_calibration(repo, calibration)
    path = calibration / "repo-profile.json"
    write_json_atomic(path, profile)
    return path


def select_primary_repo_type(repo_types: Sequence[str]) -> str:
    priority = ["game-simulation", "mobile-native", "infra-as-code", "ai-data", "frontend", "service-web", "library-sdk", "cli-desktop", "monorepo", "small-new", "mixed"]
    for item in priority:
        if item in repo_types:
            return item
    return "mixed"


def build_plan(profile: dict[str, Any]) -> dict[str, Any]:
    catalog = read_json(CATALOG_PATH)
    signals = profile.get("signals", {})
    repo_types = profile.get("repo_types") or ["mixed"]
    primary = select_primary_repo_type(repo_types)
    source_count = int(profile.get("counts", {}).get("source_files", 0) or 0)
    high_risk_present = any(signals.get(name, {}).get("present") for name in (
        "security_sensitive", "financial_or_entitlement", "persistence", "release_sensitive",
        "emergent_or_simulation", "external_dependencies"
    ))
    capabilities: list[dict[str, Any]] = []
    summary = collections.Counter()

    for cap in catalog["capabilities"]:
        selection = cap["selection"]
        matched_signals = [s for s in selection.get("signals_any", []) if signals.get(s, {}).get("present")]
        matched_risks = [s for s in selection.get("risks_any", []) if signals.get(s, {}).get("present")]
        evidence: list[str] = []
        for name in matched_signals + matched_risks:
            for item in signals.get(name, {}).get("evidence", []):
                if item not in evidence and len(evidence) < 12:
                    evidence.append(item)

        if selection.get("core"):
            status = "selected"
            reason = "Core capability for a maintained repo. Use the light repo-fit form."
            if cap["id"] == "V17" and not high_risk_present and source_count < 25:
                reason = "Selected in light form. One deterministic verifier is enough for low-risk work; add independent agent roles when risk rises."
        elif matched_signals or matched_risks:
            status = "selected"
            matched = ", ".join(matched_signals + matched_risks)
            reason = f"Selected because the deterministic profile observed: {matched}."
        elif primary == "small-new" and cap.get("cost") == "high":
            status = "deferred"
            reason = "Deferred for the small or new repo profile until the named trigger appears."
        elif selection.get("candidate_if_missing"):
            status = "candidate"
            reason = "Candidate. Confirm the needed workflow, oracle, boundary, or risk before adding tooling."
        else:
            status = "not_applicable"
            reason = "No current repo evidence supports this capability. Re-evaluate when the repo profile changes."

        # Capability-specific hard conditions.
        if cap["id"] == "V01" and not signals.get("has_tests", {}).get("present"):
            status = "deferred"
            reason = "Mutation testing needs meaningful tests first."
        if cap["id"] == "V04" and not (signals.get("multiple_implementations", {}).get("present") or signals.get("migration_or_rewrite", {}).get("present")):
            status = "candidate"
            reason = "Candidate only when two implementations or a simple reference oracle can be named."
        if cap["id"] == "V12" and not (signals.get("has_ci", {}).get("present") or signals.get("cross_platform", {}).get("present") or source_count > 100):
            status = "candidate" if primary != "small-new" else "deferred"
            reason = "Add stronger hermetic isolation when CI, cross-platform behavior, releases, or machine drift becomes material."
        if cap["id"] == "V15" and not any(signals.get(s, {}).get("present") for s in ("external_dependencies", "persistence", "concurrency_or_async", "long_running_or_background")):
            status = "deferred" if primary == "small-new" else "candidate"
            reason = "Add fault injection when a real persistence, process, network, or background boundary exists."

        summary[status] += 1
        capabilities.append({
            "id": cap["id"],
            "slug": cap["slug"],
            "name": cap["name"],
            "status": status,
            "reason": reason,
            "default_level": cap["default_level"],
            "cost": cap["cost"],
            "repo_type": primary,
            "adaptation": cap.get("adaptations", {}).get(primary) or cap.get("adaptations", {}).get("mixed"),
            "evidence": evidence,
            "deterministic_work": cap["local_work"],
            "agent_judgment": cap["agent_work"],
            "dependency_policy": "Do not install tools automatically. Prefer existing repo tooling; propose additions for human review.",
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_by": f"anti-dark-code {VERSION} adc.py plan",
        "generated_at_utc": utc_now(),
        "catalog_version": catalog.get("catalog_version"),
        "repo_profile_sha256": normalized_json_hash(profile, {"generated_at_utc"}),
        "repo_types": repo_types,
        "primary_repo_type": primary,
        "summary": {status: summary.get(status, 0) for status in catalog["statuses"]},
        "confidence_levels": catalog["confidence_levels"],
        "capabilities": capabilities,
        "notes": [
            "All 20 capabilities were evaluated. Status does not authorize dependency installation or repo-code execution.",
            "Re-run after architecture, risk, test, CI, or runtime boundaries change."
        ],
    }


def gate_level(gate: dict[str, Any], default: int = 99) -> int:
    try:
        return int(gate.get("level", default))
    except (TypeError, ValueError):
        return default


def gate_definition_hash(gate: dict[str, Any]) -> str:
    material = {
        key: gate.get(key)
        for key in (
            "level", "argv", "source", "source_definition_sha256", "confidence", "timeout_seconds",
            "resource_class", "cwd", "include_globs", "exclude_globs"
        )
    }
    return normalized_json_hash(material)


def verify_gate_source(repo: Path, gate: dict[str, Any]) -> tuple[bool, str | None]:
    source = str(gate.get("source") or "")
    expected = gate.get("source_definition_sha256")
    if "#scripts." not in source or not expected:
        return True, None
    path_text, script_name = source.split("#scripts.", 1)
    package_path = (repo / path_text).resolve()
    try:
        package_path.relative_to(repo.resolve())
    except ValueError:
        return False, "source package path escapes repo"
    try:
        data = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return False, f"could not read source package script: {exc}"
    scripts = data.get("scripts") if isinstance(data, dict) else None
    command = scripts.get(script_name) if isinstance(scripts, dict) else None
    if not isinstance(command, str):
        return False, "source package script no longer exists"
    actual = sha256_bytes(command.encode("utf-8"))
    if actual != expected:
        return False, "source package script changed after gate approval"
    return True, None


def merge_gate_suggestions(repo: Path, profile: dict[str, Any]) -> tuple[Path, int]:
    path = calibration_dir(repo) / "gates.json"
    if path.exists():
        data = read_json(path)
    else:
        data = read_json(CALIBRATION_TEMPLATE_DIR / "gates.json")
    if not isinstance(data, dict):
        raise SystemExit(f"Gate config must be a JSON object: {path}")
    policy = data.setdefault("execution_policy", {})
    gates = data.setdefault("gates", [])
    if not isinstance(gates, list):
        raise SystemExit(f"gates must be an array: {path}")

    by_id = {
        str(g.get("id")): g
        for g in gates
        if isinstance(g, dict) and g.get("id")
    }
    current_ids: set[str] = set()
    changed = 0

    for command in profile.get("exact_commands", []):
        if not isinstance(command, dict) or not command.get("id"):
            continue
        gate_id = str(command["id"])
        current_ids.add(gate_id)
        proposal = dict(command)
        proposal["enabled"] = False
        proposal["review_status"] = "proposed"
        proposal["notes"] = "Review command behavior, machine cost, external reach, and changed-slice globs before approving."
        existing = by_id.get(gate_id)
        if existing is None:
            gates.append(proposal)
            by_id[gate_id] = proposal
            changed += 1
            continue

        old_hash = gate_definition_hash(existing)
        new_hash = gate_definition_hash(proposal)
        if old_hash != new_hash:
            previous = old_hash
            preserved_notes = existing.get("owner_notes")
            existing.update(proposal)
            existing["previous_definition_sha256"] = previous
            if preserved_notes:
                existing["owner_notes"] = preserved_notes
            changed += 1
        elif str(existing.get("review_status", "")).lower() == "proposed" and existing.get("enabled"):
            existing["enabled"] = False
            changed += 1

    # A generated package-script gate that disappeared is no longer verified.
    for gate in gates:
        if not isinstance(gate, dict):
            continue
        gate_id = str(gate.get("id") or "")
        source = str(gate.get("source") or "")
        if "#scripts." not in source or gate_id in current_ids:
            continue
        if str(gate.get("review_status", "")).lower() != "stale" or gate.get("enabled"):
            gate["enabled"] = False
            gate["review_status"] = "stale"
            gate["notes"] = "The source package script was not found in the latest deterministic profile. Reconfirm or remove this gate."
            changed += 1

    if changed:
        policy["owner_confirmed_safe_to_execute"] = False
        policy["notes"] = "Gate definitions changed. Review and approve individual gates, then reconfirm execution safety."

    gates.sort(key=lambda x: (gate_level(x) if isinstance(x, dict) else 99, str(x.get("id", "")) if isinstance(x, dict) else ""))
    write_json_atomic(path, data)
    return path, changed


def write_plan(repo: Path, profile: dict[str, Any], plan: dict[str, Any], add_gate_suggestions: bool = True) -> tuple[Path, Path | None, int]:
    path = calibration_dir(repo) / "verification-plan.json"
    write_json_atomic(path, plan)
    gate_path = None
    added = 0
    if add_gate_suggestions:
        gate_path, added = merge_gate_suggestions(repo, profile)
    return path, gate_path, added


def managed_source_files(source: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for current, dirs, names in os.walk(source):
        current_path = Path(current)
        rel_dir = current_path.relative_to(source)
        excluded_here = {"__pycache__", ".git"}
        if not rel_dir.parts:
            excluded_here.update({"calibration", "incoming"})
        dirs[:] = sorted(d for d in dirs if d not in excluded_here)
        if rel_dir.parts and rel_dir.parts[0] in {"calibration", "incoming"}:
            continue
        for name in sorted(names):
            if name in {".adc-managed.json", ".DS_Store"} or name.endswith(".pyc"):
                continue
            path = current_path / name
            r = path.relative_to(source).as_posix()
            if r.startswith("calibration/") or r.startswith("incoming/"):
                continue
            files[r] = path
    return files


def core_digest(files: dict[str, Path]) -> str:
    h = hashlib.sha256()
    for r, path in sorted(files.items()):
        h.update(r.encode("utf-8"))
        h.update(b"\0")
        h.update(bytes.fromhex(sha256_file(path)))
    return h.hexdigest()


def migrate_fallback_calibration(repo: Path, target: Path) -> list[str]:
    source = repo / ".anti-dark-code" / "calibration"
    destination = target / "calibration"
    migrated: list[str] = []
    if not source.exists() or source.resolve() == destination.resolve():
        return migrated
    destination.mkdir(parents=True, exist_ok=True)
    for item in sorted(source.iterdir()):
        if not item.is_file():
            continue
        dest = destination / item.name
        if dest.exists():
            continue
        shutil.copy2(item, dest)
        migrated.append(dest.relative_to(target).as_posix())
    return migrated


def initialize_calibration(target: Path, template_dir: Path, version: str, digest: str) -> list[str]:
    if not template_dir.exists() or not template_dir.is_dir():
        raise SystemExit(f"Calibration templates not found: {template_dir}")
    created: list[str] = []
    cal = target / "calibration"
    cal.mkdir(parents=True, exist_ok=True)
    for template in sorted(template_dir.iterdir()):
        if not template.is_file():
            continue
        dest = cal / template.name
        if not dest.exists():
            shutil.copy2(template, dest)
            created.append(dest.relative_to(target).as_posix())
    upstream_path = cal / "upstream.json"
    upstream = read_json(upstream_path, {})
    if not isinstance(upstream, dict):
        upstream = {}
    upstream["installed_version"] = version
    upstream["installed_core_sha256"] = digest
    upstream["promotion_mode"] = "proposal-only"
    upstream.setdefault("parent_path", None)
    write_json_atomic(upstream_path, upstream)
    return created


def claude_adapter_text() -> str:
    return textwrap.dedent("""\
    ---
    name: anti-dark-code
    description: Claude Code adapter for the repo's canonical cross-host Anti-Dark-Code skill. Use for repo mapping, deterministic verification, dark-code audits, calibrated local workflows, remediation, and flow-back.
    ---

    # Anti-Dark-Code Claude Code Adapter

    Read and follow `../../../.agents/skills/anti-dark-code/SKILL.md` as the canonical skill.

    Resolve its relative references from `.agents/skills/anti-dark-code/`, then load `.agents/skills/anti-dark-code/references/host-claude-code.md`.

    Do not copy or edit core policy in this adapter. Repo-specific learning belongs in `.agents/skills/anti-dark-code/calibration/`.
    """)


def install_skill(
    repo: Path,
    source: Path,
    apply: bool,
    force: bool,
    hosts: str,
    *,
    allow_unsafe_source: bool = False,
    accept_unbound_calibration: bool = False,
    rebind_calibration: bool = False,
) -> dict[str, Any]:
    repo = repo.resolve()
    source = source.resolve()
    target = repo / ".agents" / "skills" / "anti-dark-code"
    target_calibration = target / "calibration"
    fallback_calibration = repo / ".anti-dark-code" / "calibration"
    if not (source / "SKILL.md").exists():
        raise SystemExit(f"Source skill is missing SKILL.md: {source}")
    template_dir = source / "assets" / "templates" / "calibration"
    if not template_dir.exists():
        raise SystemExit(f"Source skill is missing calibration templates: {template_dir}")

    source_inspection = inspect_install_source(source, repo)
    source_files = managed_source_files(source)
    if not source_files:
        raise SystemExit(f"Source skill contains no managed files: {source}")
    digest = core_digest(source_files)

    target_calibration_files = calibration_payload_files(target_calibration)
    fallback_calibration_files = calibration_payload_files(fallback_calibration)
    if target_calibration_files:
        binding_source = target_calibration
    elif fallback_calibration_files:
        binding_source = fallback_calibration
    else:
        binding_source = target_calibration
    binding = assess_repository_binding(repo, binding_source)

    fallback_action = "none"
    if fallback_calibration_files:
        if target_calibration_files:
            fallback_action = "left-in-place-target-calibration-already-exists"
        else:
            fallback_action = "migrate-missing-files"

    gate_reset_required = (
        fallback_action == "migrate-missing-files"
        or binding["status"] in {"unbound", "invalid", "mismatch"}
    )
    legacy_gate_review = inspect_gate_config_for_migration(binding_source / "gates.json")

    blocked_reasons: list[str] = []
    if source_inspection["template_errors"]:
        blocked_reasons.extend(f"unsafe calibration template: {item}" for item in source_inspection["template_errors"])
    if source_inspection["unsafe_issues"] and not allow_unsafe_source:
        blocked_reasons.extend(
            f"untrusted installation source: {item}; use --allow-unsafe-source only after manual review"
            for item in source_inspection["unsafe_issues"]
        )
    if binding["status"] in {"unbound", "invalid"} and not accept_unbound_calibration:
        blocked_reasons.append(
            "existing calibration is unbound; review that it belongs to this repository, then use --accept-unbound-calibration"
        )
    if binding["status"] == "mismatch" and not rebind_calibration:
        blocked_reasons.append(
            "existing calibration is bound to a different repository identity; do not import it unless this is a reviewed move or fork, then use --rebind-calibration"
        )
    if gate_reset_required and legacy_gate_review["present"] and not legacy_gate_review["valid"]:
        blocked_reasons.append(
            "legacy gate configuration cannot be migrated safely: "
            + str(legacy_gate_review["error"])
            + "; repair or quarantine gates.json before migration"
        )

    manifest_path = target / ".adc-managed.json"
    old_manifest = read_json(manifest_path, {}) if manifest_path.exists() else {}
    old_files = old_manifest.get("files", {}) if isinstance(old_manifest, dict) else {}
    conflicts: list[str] = []
    copies: list[str] = []
    removals: list[str] = []

    for r, src in source_files.items():
        dst = target / r
        src_hash = sha256_file(src)
        if dst.exists():
            dst_hash = sha256_file(dst)
            old_hash = old_files.get(r)
            if old_hash is None and dst_hash != src_hash:
                conflicts.append(r)
            elif old_hash is not None and dst_hash != old_hash and dst_hash != src_hash:
                conflicts.append(r)
            elif dst_hash != src_hash:
                copies.append(r)
        else:
            copies.append(r)

    for r, old_hash in old_files.items():
        if r in source_files:
            continue
        dst = target / r
        if dst.exists() and sha256_file(dst) == old_hash:
            removals.append(r)
        elif dst.exists():
            conflicts.append(r)

    should_adapter = hosts == "all" or (hosts == "auto" and ((repo / ".claude").exists() or (repo / "CLAUDE.md").exists()))
    adapter = repo / ".claude" / "skills" / "anti-dark-code" / "SKILL.md"
    expected_adapter = claude_adapter_text()
    if should_adapter and adapter.exists() and adapter.read_text(encoding="utf-8") != expected_adapter and not force:
        conflicts.append(".claude/skills/anti-dark-code/SKILL.md")

    plan = {
        "source": str(source),
        "target": str(target),
        "version": (source / "VERSION").read_text(encoding="utf-8").strip() if (source / "VERSION").exists() else "unknown",
        "core_sha256": digest,
        "copy_count": len(copies),
        "remove_count": len(removals),
        "conflicts": sorted(set(conflicts)),
        "blocked": bool(blocked_reasons),
        "blocked_reasons": blocked_reasons,
        "source_scope": {
            "marker_valid": source_inspection["marker_valid"],
            "marker_error": source_inspection["marker_error"],
            "source_inside_target_repo": source_inspection["source_inside_target_repo"],
            "source_has_managed_install_manifest": source_inspection["source_has_managed_install_manifest"],
            "source_calibration_ignored": source_inspection["source_calibration_ignored"],
            "unsafe_issues": source_inspection["unsafe_issues"],
            "unsafe_override_requested": allow_unsafe_source,
        },
        "calibration_preserved": True,
        "calibration_binding": {
            "status": binding["status"],
            "binding_source": binding_source.relative_to(repo).as_posix(),
            "stored_repository_id": binding["stored_repository_id"],
            "current_repository_id": binding["current_repository_id"],
            "identity_method": binding["identity_method"],
            "requires_accept_unbound": binding["status"] in {"unbound", "invalid"},
            "requires_rebind": binding["status"] == "mismatch",
            "accept_unbound_requested": accept_unbound_calibration,
            "rebind_requested": rebind_calibration,
        },
        "fallback_calibration_detected": bool(fallback_calibration_files),
        "fallback_calibration_action": fallback_action,
        "legacy_gate_review": {
            **legacy_gate_review,
            "approval_reset_required": gate_reset_required and legacy_gate_review["present"],
        },
        "legacy_calibration_locations": legacy_calibration_locations(repo, target_calibration),
        "hosts": hosts,
        "applied": False,
    }
    if not apply:
        return plan
    if blocked_reasons:
        raise SystemExit("Installation blocked:\n  " + "\n  ".join(blocked_reasons))
    if conflicts and not force:
        raise SystemExit("Managed-file conflicts detected. Review or rerun with --force:\n  " + "\n  ".join(sorted(set(conflicts))))

    target.mkdir(parents=True, exist_ok=True)
    for r in removals:
        try:
            (target / r).unlink()
        except FileNotFoundError:
            pass
    for r, src in source_files.items():
        dst = target / r
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and r in conflicts and not force:
            continue
        shutil.copy2(src, dst)

    installed_files = {r: sha256_file(target / r) for r in sorted(source_files)}
    version = plan["version"]
    migrated_cal: list[str] = []
    if fallback_action == "migrate-missing-files":
        migrated_cal = migrate_fallback_calibration(repo, target)
    created_cal = initialize_calibration(target, template_dir, version, digest)
    gate_reset = {"present": False, "reset": False, "reset_gate_count": 0}
    if gate_reset_required:
        reason = (
            "fallback calibration moved into the canonical repo skill"
            if fallback_action == "migrate-missing-files"
            else f"repository calibration migration status was {binding['status']}"
        )
        gate_reset = reset_gate_approvals(target_calibration / "gates.json", reason)
    binding_path = write_repository_binding(
        target_calibration,
        binding,
        accepted_unbound=binding["status"] in {"unbound", "invalid"},
        rebound=binding["status"] == "mismatch",
    )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "installed_at_utc": utc_now(),
        "source_version": version,
        "source_core_sha256": digest,
        "source_scope": SOURCE_SCOPE_VALUE,
        "source_scope_marker_sha256": sha256_file(source / SOURCE_SCOPE_FILENAME) if (source / SOURCE_SCOPE_FILENAME).exists() else None,
        "repo_binding_required": True,
        "files": installed_files,
        "calibration_ownership": "repo-owned and preserved",
    }
    write_json_atomic(manifest_path, manifest)

    adapter_created = False
    if should_adapter:
        adapter.parent.mkdir(parents=True, exist_ok=True)
        write_text_atomic(adapter, expected_adapter)
        adapter_created = True

    plan["applied"] = True
    plan["calibration_migrated"] = migrated_cal
    plan["calibration_created"] = created_cal
    plan["calibration_binding_written"] = binding_path.relative_to(target).as_posix()
    plan["migrated_gate_approvals"] = gate_reset
    plan["claude_adapter_created"] = adapter_created
    return plan


def ensure_run_gitignore(repo: Path) -> None:
    root = repo / ".anti-dark-code"
    root.mkdir(parents=True, exist_ok=True)
    path = root / ".gitignore"
    desired = "runs/\n"
    if not path.exists():
        write_text_atomic(path, desired)
    else:
        text = path.read_text(encoding="utf-8")
        if "runs/" not in text.splitlines():
            write_text_atomic(path, text.rstrip("\n") + "\nruns/\n")


def changed_files(repo: Path, ref: str) -> list[str]:
    base_paths: list[str] | None = None
    for separator in ("...", ".."):
        base_paths = git_paths(repo, ["diff", "--name-only", f"{ref}{separator}HEAD"])
        if base_paths is not None:
            break
    if base_paths is None:
        raise SystemExit(f"Could not compute changed files from {ref}")

    working_paths = git_paths(repo, ["diff", "--name-only", "HEAD"]) or []
    untracked_paths = git_paths(repo, ["ls-files", "--others", "--exclude-standard"]) or []
    combined = set(base_paths) | set(working_paths) | set(untracked_paths)
    return sorted(path for path in combined if not is_adc_internal_relpath(path))


def gate_applies(gate: dict[str, Any], changed: Sequence[str] | None) -> bool:
    if changed is None:
        return True
    includes = gate.get("include_globs") or []
    excludes = gate.get("exclude_globs") or []
    if not includes:
        return True
    for path in changed:
        if any(fnmatch.fnmatch(path, pattern) for pattern in excludes):
            continue
        if any(fnmatch.fnmatch(path, pattern) for pattern in includes):
            return True
    return False


def redact_line(line: str) -> str:
    result = line
    for pattern in SECRET_PATTERNS:
        result = pattern.sub(lambda m: f"{m.group(1) if m.lastindex else 'secret'}=<redacted>", result)
    return result.rstrip("\n")


def redact_text(text: str) -> str:
    return "\n".join(redact_line(line) for line in text.splitlines())


def redact_argv(argv: Sequence[str]) -> list[str]:
    return [redact_line(value) for value in argv]


def redact_log_file(raw_path: Path, redacted_path: Path) -> None:
    redacted_path.parent.mkdir(parents=True, exist_ok=True)
    with raw_path.open("r", encoding="utf-8", errors="replace") as source, redacted_path.open("w", encoding="utf-8", newline="\n") as destination:
        for line in source:
            destination.write(redact_line(line) + "\n")


def bounded_log(path: Path, first_n: int = 16, last_n: int = 48) -> list[str]:
    first: list[str] = []
    last: collections.deque[str] = collections.deque(maxlen=last_n)
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for index, line in enumerate(handle):
                clean = redact_line(line)
                if index < first_n:
                    first.append(clean)
                else:
                    last.append(clean)
    except OSError as exc:
        return [f"<could not read log: {exc}>"]
    if not last:
        return first
    return first + ["... output omitted; redacted log retained locally ..."] + list(last)


def run_gates(repo: Path, level: int, allow_exec: bool, changed_from: str | None, keep_going: bool) -> int:
    repo = repo.resolve()
    config_path = calibration_dir(repo) / "gates.json"
    if not config_path.exists():
        raise SystemExit(f"Gate config not found: {config_path}")
    config = read_json(config_path)
    if not isinstance(config, dict) or not isinstance(config.get("gates", []), list):
        raise SystemExit(f"Invalid gate config structure: {config_path}")

    binding = assess_repository_binding(repo, config_path.parent)
    if binding["status"] != "match":
        print(
            "BINDING WARNING: calibration is "
            f"{binding['status']} for this repository. Migrate, accept, or rebind it before trusting local gates."
        )
        if allow_exec:
            print("REFUSED: deterministic gates cannot execute from unbound or foreign calibration.")
            return 2

    candidates = [
        g for g in config.get("gates", [])
        if isinstance(g, dict) and g.get("enabled") and gate_level(g) <= level
    ]
    changed = changed_files(repo, changed_from) if changed_from else None
    candidates = [g for g in candidates if gate_applies(g, changed)]
    blocked: list[tuple[dict[str, Any], str]] = []
    gates: list[dict[str, Any]] = []
    for gate in candidates:
        if str(gate.get("review_status", "")).lower() != "approved":
            blocked.append((gate, f"review_status={gate.get('review_status', 'missing')}"))
            continue
        source_ok, source_reason = verify_gate_source(repo, gate)
        if not source_ok:
            blocked.append((gate, source_reason or "source definition is stale"))
            continue
        gates.append(gate)

    if blocked:
        print(f"BLOCKED: {len(blocked)} enabled gate(s) need review:")
        for gate, reason in blocked:
            print(f"  {gate.get('id', 'unnamed')}: {reason}")
        if allow_exec:
            print("REFUSED: rerun the planner after source changes, then approve each command and reconfirm execution safety.")
            return 2

    if not gates:
        print(f"NO GATES: no approved, enabled, applicable gates at Level {level}. Review {config_path}")
        return 0

    print(f"GATE PLAN: {len(gates)} approved gate(s), Level <= {level}, execute={'yes' if allow_exec else 'no'}")
    for gate in gates:
        shown_argv = redact_argv(gate.get("argv", []) if isinstance(gate.get("argv"), list) else [])
        print(f"  L{gate.get('level')} {gate.get('id')}: {json.dumps(shown_argv)} cwd={gate.get('cwd', '.')} resource={gate.get('resource_class', 'unknown')}")
    if not allow_exec:
        print("DRY RUN: add --allow-exec only after command behavior, repo ownership, and machine cost are reviewed.")
        return 0

    owner_confirmed = bool(config.get("execution_policy", {}).get("owner_confirmed_safe_to_execute"))
    if not owner_confirmed:
        print("REFUSED: gates.json does not record owner confirmation. Review commands, then set execution_policy.owner_confirmed_safe_to_execute to true.")
        return 2

    ensure_run_gitignore(repo)
    source_identity = current_source_identity(repo)
    gate_material = [{"id": g.get("id"), "definition": gate_definition_hash(g)} for g in gates]
    input_hash = sha256_bytes(json.dumps({"level": level, "gates": gate_material, "source": source_identity, "changed": changed or []}, sort_keys=True).encode())[:10]
    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + input_hash
    run_dir = repo / ".anti-dark-code" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    failures: list[dict[str, Any]] = []
    passed = 0
    started_all = time.monotonic()

    def record_config_failure(gate_id: str, gate: dict[str, Any], message: str) -> None:
        core = {"gate": gate_id, "config_error": message, "source": source_identity}
        failure_id = "ADC-FAIL-" + sha256_bytes(json.dumps(core, sort_keys=True).encode())[:12]
        packet = {
            "schema_version": SCHEMA_VERSION,
            "failure_id": failure_id,
            "gate_id": gate_id,
            "level": gate.get("level"),
            "exit_code": None,
            "config_error": message,
            "command": redact_argv(gate.get("argv", []) if isinstance(gate.get("argv"), list) else []),
            "cwd": str(gate.get("cwd", ".")),
            "source_identity": source_identity,
            "changed_files": changed or [],
            "bounded_output": [],
            "redaction_note": "Command fields were pattern-redacted. Review the local gate config directly.",
        }
        packet_path = run_dir / f"{failure_id}.json"
        write_json_atomic(packet_path, packet)
        failures.append({"gate_id": gate_id, "failure_id": failure_id, "packet": rel(packet_path, repo), "config_error": message})
        print(f"FAIL {gate_id} config={message} packet={rel(packet_path, repo)}")

    for gate in gates:
        gate_id = str(gate.get("id") or "unnamed")
        argv = gate.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
            record_config_failure(gate_id, gate, "invalid argv array")
            if not keep_going:
                break
            continue

        cwd = (repo / str(gate.get("cwd", "."))).resolve()
        try:
            cwd.relative_to(repo)
        except ValueError:
            record_config_failure(gate_id, gate, "cwd escapes repo")
            if not keep_going:
                break
            continue

        try:
            timeout_seconds = int(gate.get("timeout_seconds", 600))
        except (TypeError, ValueError):
            timeout_seconds = 0
        if timeout_seconds < 1 or timeout_seconds > 86_400:
            record_config_failure(gate_id, gate, "timeout_seconds must be between 1 and 86400")
            if not keep_going:
                break
            continue

        safe_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", gate_id)
        log_path = run_dir / f"{safe_id}.log"
        raw_path = run_dir / f".{safe_id}.raw.tmp"
        started = time.monotonic()
        exit_code = 124
        timed_out = False
        launch_error: str | None = None
        try:
            raw_path.touch(mode=0o600, exist_ok=False)
            with raw_path.open("w", encoding="utf-8", newline="\n") as raw_log:
                proc = subprocess.run(argv, cwd=cwd, stdout=raw_log, stderr=subprocess.STDOUT, text=True, timeout=timeout_seconds, check=False)
                exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            with raw_path.open("a", encoding="utf-8") as raw_log:
                raw_log.write(f"\n[anti-dark-code] TIMEOUT after {timeout_seconds}s\n")
        except FileNotFoundError as exc:
            exit_code = 127
            launch_error = str(exc)
            write_text_atomic(raw_path, f"[anti-dark-code] launch error: {exc}\n")
        except OSError as exc:
            exit_code = 126
            launch_error = str(exc)
            write_text_atomic(raw_path, f"[anti-dark-code] launch error: {exc}\n")
        finally:
            if raw_path.exists():
                try:
                    redact_log_file(raw_path, log_path)
                finally:
                    raw_path.unlink(missing_ok=True)

        duration = round(time.monotonic() - started, 3)
        if exit_code == 0:
            passed += 1
            print(f"PASS {gate_id} ({duration:.3f}s)")
            continue

        bounded = bounded_log(log_path)
        failure_core = {"gate": gate_id, "exit": exit_code, "source": source_identity, "tail": bounded[-12:]}
        failure_id = "ADC-FAIL-" + sha256_bytes(json.dumps(failure_core, sort_keys=True).encode())[:12]
        shown_argv = redact_argv(argv)
        packet = {
            "schema_version": SCHEMA_VERSION,
            "failure_id": failure_id,
            "gate_id": gate_id,
            "level": gate.get("level"),
            "exit_code": exit_code,
            "timed_out": timed_out,
            "launch_error": redact_text(launch_error) if launch_error else None,
            "command": shown_argv,
            "cwd": rel(cwd, repo),
            "duration_seconds": duration,
            "first_bad_event": None,
            "violated_invariant": None,
            "expected": "exit code 0",
            "actual": f"exit code {exit_code}",
            "seed": None,
            "source_identity": source_identity,
            "changed_files": changed or [],
            "replay_command": " ".join(json.dumps(x) for x in shown_argv),
            "replay_command_redacted": shown_argv != argv,
            "bounded_output": bounded,
            "full_log_path": rel(log_path, repo),
            "redaction_note": "The retained log and packet use pattern-based redaction. This reduces exposure but is not proof that every sensitive value was removed.",
        }
        packet_path = run_dir / f"{failure_id}.json"
        write_json_atomic(packet_path, packet)
        failures.append({"gate_id": gate_id, "failure_id": failure_id, "packet": rel(packet_path, repo), "exit_code": exit_code})
        print(f"FAIL {gate_id} exit={exit_code} packet={rel(packet_path, repo)}")
        if not keep_going:
            break

    duration_all = round(time.monotonic() - started_all, 3)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "level": level,
        "source_identity": source_identity,
        "changed_from": changed_from,
        "changed_files": changed or [],
        "passed": passed,
        "failed": len(failures),
        "duration_seconds": duration_all,
        "failures": failures,
    }
    write_json_atomic(run_dir / "summary.json", summary)
    if failures:
        print(f"RESULT: {passed} passed, {len(failures)} failed, {duration_all:.3f}s. Redacted artifacts: {rel(run_dir, repo)}")
        return 1
    print(f"RESULT: {passed} passed, 0 failed, {duration_all:.3f}s. Redacted artifacts: {rel(run_dir, repo)}")
    return 0


def parse_candidates(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    matches = list(re.finditer(r"^##\s+(ADC-[^:\n]+):\s*(.+)$", text, flags=re.M))
    candidates: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end]
        fields: dict[str, str] = {"id": match.group(1).strip(), "title": match.group(2).strip(), "body": body.strip()}
        for field in ("Status", "Scope", "Lesson", "Evidence", "Limits", "Proposed target", "Proposed change"):
            field_match = re.search(rf"^-\s+{re.escape(field)}:\s*(.*)$", body, flags=re.M | re.I)
            fields[field.lower().replace(" ", "_")] = field_match.group(1).strip() if field_match else ""
        candidates.append(fields)
    return candidates


def sanitize_for_proposal(text: str, repo: Path) -> str:
    result = text.replace(str(repo.resolve()), "<repo>")
    home = str(Path.home())
    if home and home != "/":
        result = result.replace(home, "<home>")
    return redact_text(result)


def flowback(repo: Path, parent: Path | None, stage_to_parent: bool, mark_staged: bool) -> Path:
    repo = repo.resolve()
    calibration = calibration_dir(repo)
    binding = assess_repository_binding(repo, calibration)
    if binding["status"] != "match":
        raise SystemExit(
            f"Flow-back refused because calibration is {binding['status']} for this repository. "
            "Complete migration or an explicit rebind first."
        )
    candidate_path = calibration / "upstream-candidates.md"
    candidates = [c for c in parse_candidates(candidate_path) if c.get("status", "").lower() == "ready"]
    if not candidates:
        raise SystemExit(f"No ready upstream candidates in {candidate_path}")
    installed_version_path = repo / ".agents" / "skills" / "anti-dark-code" / "VERSION"
    installed_version = installed_version_path.read_text(encoding="utf-8").strip() if installed_version_path.exists() else VERSION
    lines = [
        "# Anti-Dark-Code Flow-Back Proposal",
        "",
        f"Source repo identity: `{git_output(repo, ['rev-parse', 'HEAD']) or 'unknown'}`",
        f"Installed skill version: `{sanitize_for_proposal(installed_version, repo)}`",
        "",
        "This is a proposal only. It does not modify shared core policy.",
        "",
    ]
    for candidate in candidates:
        lines.extend([
            f"## {candidate['id']}: {candidate['title']}",
            "",
            f"- Scope: {candidate.get('scope') or 'unspecified'}",
            f"- Lesson: {sanitize_for_proposal(candidate.get('lesson', ''), repo)}",
            f"- Evidence: {sanitize_for_proposal(candidate.get('evidence', ''), repo)}",
            f"- Limits: {sanitize_for_proposal(candidate.get('limits', ''), repo)}",
            f"- Proposed target: {sanitize_for_proposal(candidate.get('proposed_target', ''), repo)}",
            f"- Proposed change: {sanitize_for_proposal(candidate.get('proposed_change', ''), repo)}",
            "",
        ])
    body = "\n".join(lines).rstrip() + "\n"
    digest = sha256_bytes(body.encode("utf-8"))[:12]
    out_dir = repo / ".anti-dark-code" / "flowback"
    out_path = out_dir / f"flowback-{digest}.md"
    write_text_atomic(out_path, body)

    if stage_to_parent:
        if parent is None:
            env_parent = os.environ.get("ADC_PARENT_SKILL")
            if env_parent:
                parent = Path(env_parent)
        if parent is None:
            raise SystemExit("--stage-to-parent requires --parent or ADC_PARENT_SKILL")
        parent = parent.expanduser().resolve()
        if not (parent / "SKILL.md").exists():
            raise SystemExit(f"Parent skill does not look valid: {parent}")
        parent_scope = inspect_install_source(parent, repo)
        if parent_scope["unsafe_issues"] or parent_scope["template_errors"]:
            raise SystemExit("Parent skill is not a clean universal core. Stage the proposal to a reviewed shared source instead.")
        incoming = parent / "incoming"
        incoming.mkdir(parents=True, exist_ok=True)
        shutil.copy2(out_path, incoming / out_path.name)

    if mark_staged:
        text = candidate_path.read_text(encoding="utf-8")
        for candidate in candidates:
            heading = re.escape(f"## {candidate['id']}: {candidate['title']}")
            pattern = rf"({heading}.*?^-\s+Status:\s*)ready\b"
            text = re.sub(pattern, rf"\1staged", text, flags=re.M | re.S | re.I)
        write_text_atomic(candidate_path, text)
    return out_path


def validate_skill(skill: Path) -> tuple[list[str], list[str]]:
    skill = skill.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    skill_md = skill / "SKILL.md"
    if not skill_md.exists():
        return [f"Missing {skill_md}"], warnings
    text = skill_md.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) > 500:
        errors.append(f"SKILL.md has {len(lines)} lines; keep it at or below 500")

    front = ""
    if not text.startswith("---\n"):
        errors.append("SKILL.md is missing YAML frontmatter")
    else:
        end = text.find("\n---\n", 4)
        if end < 0:
            errors.append("SKILL.md frontmatter is not closed")
        else:
            front = text[4:end]
            name_match = re.search(r"^name:\s*['\"]?([^'\"\n]+)", front, flags=re.M)
            description_match = re.search(r"^description:\s*(.+)$", front, flags=re.M)
            if not name_match:
                errors.append("SKILL.md frontmatter missing name")
            else:
                name = name_match.group(1).strip()
                if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
                    errors.append(f"Invalid skill name: {name}")
                if name != skill.name:
                    errors.append(f"Skill name {name} does not match directory {skill.name}")
            if not description_match:
                errors.append("SKILL.md frontmatter missing description")
            else:
                description = description_match.group(1).strip().strip("'\"")
                if description not in {">", "|", ">-", "|-"} and not (1 <= len(description) <= 1024):
                    errors.append(f"Skill description length is {len(description)}, expected 1..1024")

    for token in sorted(set(re.findall(r"`((?:references|assets|scripts)/[^`\s]+)`", text))):
        cleaned = token.rstrip(".,;:")
        if not (skill / cleaned).exists():
            errors.append(f"SKILL.md references missing path: {cleaned}")
    if "so Claude can" in text or "so Codex can" in text:
        errors.append("Core description is host-specific")

    scope_path = skill / SOURCE_SCOPE_FILENAME
    if not scope_path.exists():
        errors.append(f"Missing {SOURCE_SCOPE_FILENAME}")
    else:
        try:
            scope = json.loads(scope_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Invalid {SOURCE_SCOPE_FILENAME}: {exc}")
        else:
            if not isinstance(scope, dict):
                errors.append(f"{SOURCE_SCOPE_FILENAME} is not a JSON object")
            else:
                if scope.get("kind") != SOURCE_SCOPE_KIND or scope.get("scope") != SOURCE_SCOPE_VALUE:
                    errors.append(f"{SOURCE_SCOPE_FILENAME} does not identify the universal core")
                if scope.get("repo_calibration_transfer") != "prohibited":
                    errors.append(f"{SOURCE_SCOPE_FILENAME} must prohibit repo calibration transfer")

    source_calibration_files = calibration_payload_files(skill / "calibration")
    if source_calibration_files:
        errors.append(
            "Universal core contains repo-owned top-level calibration: "
            + ", ".join(item.relative_to(skill).as_posix() for item in source_calibration_files)
        )

    artifact_paths = [
        path.relative_to(skill).as_posix()
        for path in skill.rglob("*")
        if path.name == "__pycache__" or path.suffix == ".pyc"
    ]
    if artifact_paths:
        errors.append("Generated Python artifacts found in package: " + ", ".join(sorted(artifact_paths)))

    for json_path in list(skill.rglob("*.json")):
        try:
            json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"Invalid JSON {json_path.relative_to(skill)}: {exc}")

    catalog_path = skill / "assets" / "verification-capabilities.json"
    if catalog_path.exists():
        catalog = read_json(catalog_path)
        caps = catalog.get("capabilities", []) if isinstance(catalog, dict) else []
        ids = [c.get("id") for c in caps if isinstance(c, dict)]
        if len(caps) != 20:
            errors.append(f"Capability catalog contains {len(caps)} entries, expected 20")
        if len(set(ids)) != len(ids):
            errors.append("Capability catalog contains duplicate ids")
        expected = {f"V{i:02d}" for i in range(1, 21)}
        if set(ids) != expected:
            errors.append(f"Capability ids differ from V01..V20: {sorted(set(ids) ^ expected)}")
        repo_types = catalog.get("repo_types", []) if isinstance(catalog, dict) else []
        required = {"id", "slug", "name", "category", "default_level", "cost", "purpose", "local_work", "agent_work", "adaptations", "selection"}
        for cap in caps:
            if not isinstance(cap, dict):
                errors.append("Capability entry is not an object")
                continue
            missing = sorted(required - set(cap))
            if missing:
                errors.append(f"Capability {cap.get('id', '?')} missing fields: {', '.join(missing)}")
            adaptations = cap.get("adaptations", {})
            missing_types = sorted(set(repo_types) - set(adaptations) if isinstance(adaptations, dict) else set(repo_types))
            if missing_types:
                errors.append(f"Capability {cap.get('id', '?')} missing repo adaptations: {', '.join(missing_types)}")
    else:
        errors.append("Missing assets/verification-capabilities.json")

    dash_files: list[str] = []
    hardcoded_files: list[str] = []
    for path in skill.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS | {".yaml", ".yml"}:
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if chr(0x2014) in content or chr(0x2013) in content:
                dash_files.append(path.relative_to(skill).as_posix())
            if personal_absolute_path_hits(content):
                hardcoded_files.append(path.relative_to(skill).as_posix())
    if dash_files:
        errors.append("Non-ASCII em/en dashes found in: " + ", ".join(dash_files))
    if hardcoded_files:
        errors.append("Likely personal absolute paths found in: " + ", ".join(hardcoded_files))

    python_files = list((skill / "scripts").glob("*.py")) + list((skill / "tests").glob("*.py"))
    for path in python_files:
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            errors.append(f"Python compile failed for {path.relative_to(skill)}: {exc}")

    template_errors = validate_calibration_templates(skill / "assets" / "templates" / "calibration")
    errors.extend(template_errors)
    if not (skill / "references" / "host-adapters.md").exists():
        warnings.append("No host adapter router found")
    if not (skill / "agents" / "openai.yaml").exists():
        warnings.append("No optional OpenAI metadata found")
    return errors, warnings


def command_probe(args: argparse.Namespace) -> int:
    repo = Path(args.repo).expanduser().resolve()
    profile = probe_repo(repo, max_files=args.max_files, content_scan_limit=args.content_scan_limit)
    if args.write:
        path = write_profile(repo, profile)
        print(f"WROTE {path}")
    if args.json:
        print(json.dumps(profile, indent=2))
    else:
        present = [name for name, item in profile["signals"].items() if item.get("present")]
        print(f"PROFILE types={','.join(profile['repo_types'])} source_files={profile['counts']['source_files']} tests={profile['counts']['test_like_files']} manifests={len(profile['manifests'])} signals={','.join(present)}")
        if not profile["scan"]["complete"]:
            print("LIMIT: file scan was partial")
    return 0


def profile_is_fresh(repo: Path, profile: dict[str, Any]) -> bool:
    recorded = profile.get("source_identity")
    if not isinstance(recorded, dict):
        return False
    current = current_source_identity(repo)
    # For a non-git directory, a cheap identity is unavailable. Re-probe rather
    # than treating old absence evidence as current truth.
    if current.get("git_commit") is None:
        return False
    return (
        recorded.get("git_commit") == current.get("git_commit")
        and recorded.get("worktree_status_sha256") == current.get("worktree_status_sha256")
    )


def load_or_probe(repo: Path) -> dict[str, Any]:
    path = calibration_dir(repo) / "repo-profile.json"
    if path.exists():
        data = read_json(path)
        if data.get("generated_at_utc") and profile_is_fresh(repo, data):
            return data
    return probe_repo(repo)


def command_plan(args: argparse.Namespace) -> int:
    repo = Path(args.repo).expanduser().resolve()
    profile = load_or_probe(repo)
    plan = build_plan(profile)
    if args.write:
        profile_path = calibration_dir(repo) / "repo-profile.json"
        if not profile_path.exists() or not profile.get("generated_at_utc"):
            write_profile(repo, profile)
        path, gate_path, added = write_plan(repo, profile, plan, add_gate_suggestions=not args.no_gate_suggestions)
        print(f"WROTE {path}")
        if gate_path:
            print(f"UPDATED {gate_path} with {added} gate proposal change(s)")
    if args.json:
        print(json.dumps(plan, indent=2))
    else:
        summary = plan["summary"]
        print("PLAN " + " ".join(f"{k}={v}" for k, v in summary.items()) + f" primary={plan['primary_repo_type']}")
        for cap in plan["capabilities"]:
            print(f"  {cap['id']} {cap['status']}: {cap['name']} - {cap['reason']}")
    return 0


def command_install(args: argparse.Namespace) -> int:
    repo = Path(args.repo).expanduser()
    source = Path(args.source_skill).expanduser() if args.source_skill else SKILL_ROOT
    plan = install_skill(
        repo,
        source,
        apply=args.apply,
        force=args.force,
        hosts=args.hosts,
        allow_unsafe_source=args.allow_unsafe_source,
        accept_unbound_calibration=args.accept_unbound_calibration,
        rebind_calibration=args.rebind_calibration,
    )
    print(json.dumps(plan, indent=2))
    if not args.apply:
        print("DRY RUN: add --apply after reviewing conflicts and target paths.")
    return 0


def command_bootstrap(args: argparse.Namespace) -> int:
    repo = Path(args.repo).expanduser().resolve()
    source = Path(args.source_skill).expanduser() if args.source_skill else SKILL_ROOT
    install_plan = install_skill(
        repo,
        source,
        apply=args.apply,
        force=args.force,
        hosts=args.hosts,
        allow_unsafe_source=args.allow_unsafe_source,
        accept_unbound_calibration=args.accept_unbound_calibration,
        rebind_calibration=args.rebind_calibration,
    )
    print(json.dumps(install_plan, indent=2))
    if not args.apply:
        print("DRY RUN: bootstrap did not write or execute repo code. Add --apply to install and generate calibration.")
        return 0
    profile = probe_repo(repo, max_files=args.max_files, content_scan_limit=args.content_scan_limit)
    profile_path = write_profile(repo, profile)
    plan = build_plan(profile)
    plan_path, gate_path, added = write_plan(repo, profile, plan, add_gate_suggestions=True)
    print(f"WROTE {profile_path}")
    print(f"WROTE {plan_path}")
    print(f"UPDATED {gate_path} with {added} gate proposal change(s)")
    print("No repo code was executed and no dependency was installed.")
    return 0


def command_gates(args: argparse.Namespace) -> int:
    return run_gates(Path(args.repo), level=args.level, allow_exec=args.allow_exec, changed_from=args.changed_from, keep_going=args.keep_going)


def command_flowback(args: argparse.Namespace) -> int:
    parent = Path(args.parent).expanduser() if args.parent else None
    path = flowback(Path(args.repo), parent, args.stage_to_parent, args.mark_staged)
    print(f"WROTE {path}")
    if args.stage_to_parent:
        print("STAGED proposal in parent incoming directory. Shared core was not modified.")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    skill = Path(args.skill).expanduser() if args.skill else SKILL_ROOT
    errors, warnings = validate_skill(skill)
    for warning in warnings:
        print(f"WARN {warning}")
    for error in errors:
        print(f"ERROR {error}")
    if errors:
        print(f"INVALID: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"VALID: 0 errors, {len(warnings)} warning(s)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="adc.py", description="Deterministic helpers for the Anti-Dark-Code skill")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("probe", help="Read-only deterministic repo profile")
    p.add_argument("--repo", default=".")
    p.add_argument("--write", action="store_true", help="Write calibration/repo-profile.json")
    p.add_argument("--json", action="store_true", help="Print full JSON")
    p.add_argument("--max-files", type=int, default=50_000)
    p.add_argument("--content-scan-limit", type=int, default=4_000)
    p.set_defaults(func=command_probe)

    p = sub.add_parser("plan", help="Evaluate all 20 verification capabilities")
    p.add_argument("--repo", default=".")
    p.add_argument("--write", action="store_true", help="Write verification plan and proposed gates")
    p.add_argument("--json", action="store_true", help="Print full JSON")
    p.add_argument("--no-gate-suggestions", action="store_true")
    p.set_defaults(func=command_plan)

    p = sub.add_parser("install", help="Install or update the managed core in a repo")
    p.add_argument("--repo", required=True)
    p.add_argument("--source-skill")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--allow-unsafe-source", action="store_true", help="Allow a reviewed legacy or repo-local source. Source calibration is still ignored.")
    p.add_argument("--accept-unbound-calibration", action="store_true", help="Bind reviewed legacy calibration to this repository.")
    p.add_argument("--rebind-calibration", action="store_true", help="Rebind calibration after a reviewed repo move, fork, or remote identity change.")
    p.add_argument("--hosts", choices=("auto", "all", "none"), default="auto")
    p.set_defaults(func=command_install)

    p = sub.add_parser("bootstrap", help="Install, profile, and plan without executing repo code")
    p.add_argument("--repo", required=True)
    p.add_argument("--source-skill")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--allow-unsafe-source", action="store_true", help="Allow a reviewed legacy or repo-local source. Source calibration is still ignored.")
    p.add_argument("--accept-unbound-calibration", action="store_true", help="Bind reviewed legacy calibration to this repository.")
    p.add_argument("--rebind-calibration", action="store_true", help="Rebind calibration after a reviewed repo move, fork, or remote identity change.")
    p.add_argument("--hosts", choices=("auto", "all", "none"), default="auto")
    p.add_argument("--max-files", type=int, default=50_000)
    p.add_argument("--content-scan-limit", type=int, default=4_000)
    p.set_defaults(func=command_bootstrap)

    p = sub.add_parser("gates", help="Dry-run or execute reviewed deterministic gates")
    p.add_argument("--repo", default=".")
    p.add_argument("--level", type=int, choices=(0, 1, 2, 3), default=0)
    p.add_argument("--allow-exec", action="store_true")
    p.add_argument("--changed-from")
    p.add_argument("--keep-going", action="store_true")
    p.set_defaults(func=command_gates)

    p = sub.add_parser("flowback", help="Stage ready repo lessons as a proposal")
    p.add_argument("--repo", default=".")
    p.add_argument("--parent")
    p.add_argument("--stage-to-parent", action="store_true")
    p.add_argument("--mark-staged", action="store_true")
    p.set_defaults(func=command_flowback)

    p = sub.add_parser("validate", help="Validate skill packaging and catalog")
    p.add_argument("--skill")
    p.set_defaults(func=command_validate)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        eprint("Interrupted")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
