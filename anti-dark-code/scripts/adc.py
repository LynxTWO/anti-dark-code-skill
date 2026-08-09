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
import signal
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
    (".codex", "skills", "anti-dark-code", "calibration"),
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

HOST_SKILL_TREE_PREFIXES = {
    (".agents", "skills"),
    (".claude", "skills"),
    (".gemini", "skills"),
    (".codex", "skills"),
}
TOOLING_PATH_PREFIXES = (
    ".agents/skills/",
    ".claude/skills/",
    ".gemini/skills/",
    ".codex/skills/",
    ".anti-dark-code/",
)

VALIDATION_MODES = ("auto", "distribution", "universal", "installed")

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

ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
SENSITIVE_ENV_NAME_RE = re.compile(
    r"(?i)(?:^|_)(?:password|passwd|secret|token|api_?key|private_?key|credentials?|auth(?:entication|orization)?|cookie)(?:_|$)"
)
ENV_IDENTITY_NAMES = {
    "APPDATA", "COMSPEC", "DOTNET_ROOT", "DOTNET_ROOT_X86", "HOME", "JAVA_HOME",
    "LANG", "LANGUAGE", "LOCALAPPDATA", "NODE_PATH", "PATH", "PATHEXT", "PSMODULEPATH",
    "PYTHONPATH", "SHELL", "SYSTEMROOT", "TEMP", "TMP", "TZ", "USERPROFILE", "WINDIR",
    "XDG_CACHE_HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME",
}
MAX_GATE_ENV_VARS = 32
MAX_GATE_ENV_VALUE_CHARS = 4096
MAX_GATE_ENV_TOTAL_CHARS = 32768

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


def path_is_linklike(path: Path) -> bool:
    """Return True for a symbolic link or a Windows directory junction."""
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    if callable(is_junction) and is_junction():
        return True
    os_isjunction = getattr(os.path, "isjunction", None)
    return bool(callable(os_isjunction) and os_isjunction(path))


def write_text_atomic(path: Path, text: str) -> None:
    if path_is_linklike(path):
        raise SystemExit(f"Refused atomic write through symlink or junction: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False, dir=path.parent) as tmp:
            tmp.write(text)
            tmp_path = Path(tmp.name)
        os.replace(tmp_path, path)
        tmp_path = None
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


def copy_file_atomic(source: Path, destination: Path) -> None:
    """Copy one regular file without following a destination symlink or junction."""
    if path_is_linklike(source) or not source.is_file():
        raise SystemExit(f"Refused copy from non-regular, symlink, or junction source: {source}")
    if path_is_linklike(destination):
        raise SystemExit(f"Refused copy through destination symlink or junction: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("wb", delete=False, dir=destination.parent) as tmp:
            tmp_path = Path(tmp.name)
        shutil.copy2(source, tmp_path)
        os.replace(tmp_path, destination)
        tmp_path = None
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


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


def source_set_hash(repo: Path, source_files: Sequence[str]) -> str:
    """Bind a conventional gate to the exact in-repo files that proposed it."""
    root = repo.resolve()
    entries: list[dict[str, str]] = []
    for item in sorted(set(source_files)):
        lexical = root / item
        resolved = lexical.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"source file escapes repo: {item}") from exc
        if path_is_linklike(lexical) or not resolved.is_file():
            raise ValueError(f"source file is missing or link-like: {item}")
        entries.append({"path": Path(item).as_posix(), "sha256": sha256_file(resolved)})
    if not entries:
        raise ValueError("source file set is empty")
    return normalized_json_hash(entries)


def gate_environment(gate: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any], list[str]]:
    """Build a reviewed gate environment and a value-free public identity record."""
    inherit_env = gate.get("inherit_env", True)
    if not isinstance(inherit_env, bool):
        raise ValueError("inherit_env must be true or false")
    overlay = gate.get("env", {})
    if overlay is None:
        overlay = {}
    if not isinstance(overlay, dict):
        raise ValueError("env must be an object of string names and values")
    if len(overlay) > MAX_GATE_ENV_VARS:
        raise ValueError(f"env may contain at most {MAX_GATE_ENV_VARS} variables")

    reviewed_overlay: dict[str, str] = {}
    total_chars = 0
    for name, value in overlay.items():
        if not isinstance(name, str) or not ENV_NAME_RE.fullmatch(name):
            raise ValueError(f"invalid environment variable name: {name!r}")
        if SENSITIVE_ENV_NAME_RE.search(name):
            raise ValueError(f"sensitive environment variable names are not allowed in env: {name}")
        if not isinstance(value, str):
            raise ValueError(f"environment variable {name} must have a string value")
        if len(value) > MAX_GATE_ENV_VALUE_CHARS:
            raise ValueError(f"environment variable {name} exceeds {MAX_GATE_ENV_VALUE_CHARS} characters")
        total_chars += len(name) + len(value)
        normalized_name = name.upper() if os.name == "nt" else name
        if normalized_name in reviewed_overlay:
            raise ValueError(f"duplicate environment variable after platform normalization: {name}")
        reviewed_overlay[normalized_name] = value
    if total_chars > MAX_GATE_ENV_TOTAL_CHARS:
        raise ValueError(f"env exceeds {MAX_GATE_ENV_TOTAL_CHARS} total characters")

    process_env = (
        {(name.upper() if os.name == "nt" else name): value for name, value in os.environ.items()}
        if inherit_env else {}
    )
    process_env.update(reviewed_overlay)
    overlay_names = set(reviewed_overlay)
    identity_names = sorted(
        name for name in process_env
        if name in overlay_names or name.upper() in ENV_IDENTITY_NAMES or name.upper().startswith("LC_")
    )
    identity_material = [{"name": name, "value": process_env[name]} for name in identity_names]
    public = {
        "inherit_env": inherit_env,
        "overlay_keys": sorted(reviewed_overlay),
        "identity_keys": identity_names,
        "fingerprint": "sha256:" + normalized_json_hash(identity_material)[:20],
    }
    literal_redactions = sorted(
        {value for value in reviewed_overlay.values() if value}, key=len, reverse=True
    )
    return process_env, public, literal_redactions


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


def lexical_absolute(path: Path) -> Path:
    """Return an absolute normalized path without resolving symlinks."""
    return Path(os.path.abspath(os.fspath(path)))


def symlink_components(path: Path, trusted_root: Path) -> list[Path]:
    """List existing symlink or junction components between trusted_root and path.

    The check is deliberately lexical. Resolving first would erase the evidence
    that a repo-local managed path points somewhere else.
    """
    root = lexical_absolute(trusted_root)
    candidate = lexical_absolute(path)
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise SystemExit(f"Managed path escapes trusted root: {candidate} (root {root})") from exc

    hits: list[Path] = []
    current = root
    for part in relative.parts:
        current = current / part
        try:
            os.lstat(current)
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise SystemExit(f"Could not inspect managed path component {current}: {exc}") from exc
        if path_is_linklike(current):
            hits.append(current)
    return hits


def require_no_symlink_components(path: Path, trusted_root: Path, purpose: str) -> None:
    hits = symlink_components(path, trusted_root)
    if not hits:
        return
    shown = ", ".join(rel(item, lexical_absolute(trusted_root)) for item in hits)
    raise SystemExit(
        f"Refused {purpose}: managed path traverses symlink or junction component(s): {shown}. "
        "Repo-local Anti-Dark-Code skill, calibration, adapter, and run paths must be real paths."
    )


def tree_symlinks(root: Path, *, excluded_top_level: set[str] | None = None) -> list[Path]:
    """Return symlinks or junctions under root without following linked directories."""
    if not root.exists() or not root.is_dir():
        return []
    excluded_top_level = excluded_top_level or set()
    found: list[Path] = []
    for current, dirs, names in os.walk(root, followlinks=False):
        current_path = Path(current)
        relative = current_path.relative_to(root)
        if relative.parts and relative.parts[0] in excluded_top_level:
            dirs[:] = []
            continue
        kept_dirs: list[str] = []
        for name in sorted(dirs):
            path = current_path / name
            if not relative.parts and name in excluded_top_level:
                continue
            if path_is_linklike(path):
                found.append(path)
            else:
                kept_dirs.append(name)
        dirs[:] = kept_dirs
        for name in sorted(names):
            path = current_path / name
            if path_is_linklike(path):
                found.append(path)
    return found


def calibration_payload_files(path: Path) -> list[Path]:
    if path_is_linklike(path) or not path.exists() or not path.is_dir():
        return []
    return sorted(
        item
        for item in path.rglob("*")
        if item.is_file()
        and not path_is_linklike(item)
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
    calibration_symlinks = ([calibration] if path_is_linklike(calibration) else []) + tree_symlinks(calibration)
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

    if calibration_symlinks:
        status = "invalid"
        binding_error = "calibration contains link-like entries: " + ", ".join(
            rel(item, calibration.parent) for item in calibration_symlinks
        )
    elif not all_files:
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
        "symlink_entries": [rel(item, calibration) for item in calibration_symlinks],
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
    calibration_symlinks = ([calibration] if path_is_linklike(calibration) else []) + tree_symlinks(calibration)
    if calibration_symlinks:
        raise SystemExit(
            "Refused repository binding write through calibration link-like entries: "
            + ", ".join(rel(item, calibration.parent) for item in calibration_symlinks)
        )
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
    template_symlinks = ([template_dir] if path_is_linklike(template_dir) else []) + tree_symlinks(template_dir)
    if template_symlinks:
        errors.append(
            "Calibration templates contain link-like entries: "
            + ", ".join(rel(item, template_dir) for item in template_symlinks)
        )

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
    source_calibration_symlinks = ([source_calibration] if path_is_linklike(source_calibration) else []) + tree_symlinks(source_calibration)
    source_core_symlinks = tree_symlinks(source, excluded_top_level={"calibration", "incoming"})
    unsafe_issues: list[str] = []
    fatal_issues: list[str] = []
    if not marker_valid:
        unsafe_issues.append(marker_error or "source scope marker is invalid")
    if path_is_within(source, repo):
        unsafe_issues.append("source skill is located inside the target repository")
    if (source / ".adc-managed.json").exists():
        unsafe_issues.append("source skill contains a repo-local managed-install manifest")
    if source_calibration_files or source_calibration_symlinks:
        unsafe_issues.append("source skill contains repo-owned top-level calibration")
    if source_core_symlinks:
        fatal_issues.append(
            "source core contains link-like entries: "
            + ", ".join(item.relative_to(source).as_posix() for item in source_core_symlinks)
        )

    template_errors = validate_calibration_templates(source / "assets" / "templates" / "calibration")
    return {
        "marker_valid": marker_valid,
        "marker_error": marker_error,
        "source_inside_target_repo": path_is_within(source, repo),
        "source_has_managed_install_manifest": (source / ".adc-managed.json").exists(),
        "source_calibration_ignored": sorted({
            item.relative_to(source_calibration).as_posix()
            for item in [*source_calibration_files, *source_calibration_symlinks]
            if item != source_calibration
        }),
        "unsafe_issues": unsafe_issues,
        "fatal_issues": fatal_issues,
        "template_errors": template_errors,
    }


def is_tooling_relpath(path: str) -> bool:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.lstrip("/")
    return any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in TOOLING_PATH_PREFIXES)


def is_adc_internal_relpath(path: str) -> bool:
    """Backward-compatible alias for callers using the v3 helper name."""
    return is_tooling_relpath(path)


def is_host_skill_tree_parts(parts: Sequence[str]) -> bool:
    return any(tuple(parts[:len(prefix)]) == prefix for prefix in HOST_SKILL_TREE_PREFIXES)


def is_ignored(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        parts = path.parts
    if is_host_skill_tree_parts(parts):
        return True
    return any(part in IGNORED_DIRS for part in parts[:-1])


def iter_repo_files(root: Path, max_files: int = 50_000) -> tuple[list[Path], bool]:
    files: list[Path] = []
    truncated = False
    for current, dirs, names in os.walk(root, followlinks=False):
        current_path = Path(current)
        try:
            current_parts = current_path.relative_to(root).parts
        except ValueError:
            current_parts = current_path.parts
        dirs[:] = sorted(
            d for d in dirs
            if d not in IGNORED_DIRS
            and not is_host_skill_tree_parts((*current_parts, d))
            and not path_is_linklike(current_path / d)
        )
        for name in sorted(names):
            path = current_path / name
            if path_is_linklike(path) or is_ignored(path, root):
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
        ":(exclude).agents/skills/**",
        ":(exclude).claude/skills/**",
        ":(exclude).gemini/skills/**",
        ":(exclude).codex/skills/**",
        ":(exclude).anti-dark-code/**",
    ])
    return {
        "git_commit": commit,
        "git_branch": branch,
        "worktree_clean": status_raw == b"" if status_raw is not None else None,
        "worktree_status_sha256": sha256_bytes(status_raw) if status_raw is not None else None,
        "identity_excludes": list(TOOLING_PATH_PREFIXES),
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
        # Lossy punctuation normalization can collapse distinct names such as
        # test:unit and test_unit. Keep simple ids readable, but suffix every
        # changed spelling so the id stays unique even if sibling scripts move.
        if script_slug != lname:
            script_slug += "-" + sha256_bytes(lname.encode("utf-8"))[:8]
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


def add_conventional_commands(
    repo: Path,
    profile: dict[str, Any],
    manifest_paths: Sequence[str],
    terraform_paths: Sequence[str],
) -> None:
    manifests = {Path(item).name for item in manifest_paths}
    existing_ids = {item["id"] for item in profile["exact_commands"]}

    def add(item: dict[str, Any], source_files: Sequence[str]) -> None:
        if item["id"] not in existing_ids:
            exact_sources = sorted(set(source_files))
            item["source_files"] = exact_sources
            item["source_definition_sha256"] = source_set_hash(repo, exact_sources)
            profile["exact_commands"].append(item)
            existing_ids.add(item["id"])

    if "pyproject.toml" in manifests or "requirements.txt" in manifests:
        add({"id":"python-pytest", "level":3, "argv":[sys.executable, "-m", "pytest"], "enabled":False,
             "source":"conventional candidate from Python manifest", "confidence":"inferred", "timeout_seconds":900,
             "resource_class":"heavy", "cwd":".", "include_globs":[], "exclude_globs":[]},
            [item for item in manifest_paths if Path(item).name in {"pyproject.toml", "requirements.txt"}])
    if "Cargo.toml" in manifests:
        add({"id":"cargo-check", "level":0, "argv":["cargo", "check", "--all-targets"], "enabled":False,
             "source":"conventional candidate from Cargo.toml", "confidence":"inferred", "timeout_seconds":600,
             "resource_class":"medium", "cwd":".", "include_globs":[], "exclude_globs":[]},
            [item for item in manifest_paths if Path(item).name == "Cargo.toml"])
        add({"id":"cargo-test", "level":3, "argv":["cargo", "test", "--all-targets"], "enabled":False,
             "source":"conventional candidate from Cargo.toml", "confidence":"inferred", "timeout_seconds":1200,
             "resource_class":"heavy", "cwd":".", "include_globs":[], "exclude_globs":[]},
            [item for item in manifest_paths if Path(item).name == "Cargo.toml"])
    if "go.mod" in manifests:
        add({"id":"go-test", "level":3, "argv":["go", "test", "./..."], "enabled":False,
             "source":"conventional candidate from go.mod", "confidence":"inferred", "timeout_seconds":900,
             "resource_class":"heavy", "cwd":".", "include_globs":[], "exclude_globs":[]},
            [item for item in manifest_paths if Path(item).name == "go.mod"])
    if any(name.endswith(".sln") or name.endswith(".csproj") for name in manifests):
        add({"id":"dotnet-test", "level":3, "argv":["dotnet", "test"], "enabled":False,
             "source":"conventional candidate from .NET manifest", "confidence":"inferred", "timeout_seconds":1200,
             "resource_class":"heavy", "cwd":".", "include_globs":[], "exclude_globs":[]},
            [item for item in manifest_paths if item.endswith((".sln", ".csproj"))])
    if terraform_paths or "terraform" in profile.get("repo_types", []):
        add({"id":"terraform-fmt", "level":0, "argv":["terraform", "fmt", "-check", "-recursive"], "enabled":False,
             "source":"conventional candidate from Terraform files", "confidence":"inferred", "timeout_seconds":180,
             "resource_class":"light", "cwd":".", "include_globs":["**/*.tf"], "exclude_globs":[]},
            terraform_paths)


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
            "ignored_skill_trees": sorted("/".join(parts) + "/" for parts in HOST_SKILL_TREE_PREFIXES),
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
    terraform_paths = sorted(rel(path, repo) for path in files if path.suffix.lower() == ".tf")
    add_conventional_commands(repo, profile, sorted(set(manifests)), terraform_paths)
    profile["exact_commands"] = sorted(profile["exact_commands"], key=lambda x: (x["level"], x["id"], x.get("cwd", ".")))

    # Normalize signals. Absence is unknown under a bounded scan, not verified false.
    for name in sorted(set(CONTENT_PATTERNS) | {"has_tests", "has_ci", "large_repo", "schema_validation_present", "architecture_tool_present", "mutation_tool_present", "property_tool_present"}):
        profile["signals"].setdefault(name, {"present": False, "evidence": []})
    profile["signals"] = {name: profile["signals"][name] for name in sorted(profile["signals"])}
    return profile


def calibration_dir(repo: Path) -> Path:
    canonical = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
    skill_dir = repo / ".agents" / "skills" / "anti-dark-code"
    if canonical.exists() or path_is_linklike(canonical) or skill_dir.exists() or path_is_linklike(skill_dir):
        return canonical
    return repo / ".anti-dark-code" / "calibration"


def safe_calibration_dir(repo: Path, purpose: str) -> Path:
    repo = repo.resolve()
    calibration = calibration_dir(repo)
    require_no_symlink_components(calibration, repo, purpose)
    nested = tree_symlinks(calibration)
    if nested:
        shown = ", ".join(rel(item, repo) for item in nested)
        raise SystemExit(f"Refused {purpose}: calibration contains link-like entries: {shown}")
    return calibration


def write_profile(repo: Path, profile: dict[str, Any]) -> Path:
    calibration = safe_calibration_dir(repo, "repository profile write")
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
            "source_files", "resource_class", "cwd", "include_globs", "exclude_globs", "inherit_env", "env"
        )
    }
    return normalized_json_hash(material)


def verify_gate_source(repo: Path, gate: dict[str, Any]) -> tuple[bool, str | None]:
    source = str(gate.get("source") or "")
    expected = gate.get("source_definition_sha256")
    source_files = gate.get("source_files")
    if source_files is not None:
        if not isinstance(source_files, list) or not source_files or not expected:
            return False, "source_files requires a nonempty string array and source_definition_sha256"
        if not all(isinstance(item, str) and item for item in source_files):
            return False, "source_files must be a nonempty string array"
        try:
            actual = source_set_hash(repo, source_files)
        except (OSError, ValueError) as exc:
            return False, str(exc)
        if actual != expected:
            return False, "conventional gate source files changed after approval"
        return True, None
    if source.startswith("conventional candidate"):
        return False, "conventional gate lacks a source-file binding; rerun the planner and review it"
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
    path = safe_calibration_dir(repo, "gate-plan update") / "gates.json"
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
        if ("#scripts." not in source and not gate.get("source_files")) or gate_id in current_ids:
            continue
        if str(gate.get("review_status", "")).lower() != "stale" or gate.get("enabled"):
            gate["enabled"] = False
            gate["review_status"] = "stale"
            gate["notes"] = "The deterministic source definition was not found in the latest profile. Reconfirm or remove this gate."
            changed += 1

    if changed:
        policy["owner_confirmed_safe_to_execute"] = False
        policy["notes"] = "Gate definitions changed. Review and approve individual gates, then reconfirm execution safety."

    gates.sort(key=lambda x: (gate_level(x) if isinstance(x, dict) else 99, str(x.get("id", "")) if isinstance(x, dict) else ""))
    write_json_atomic(path, data)
    return path, changed


def write_plan(repo: Path, profile: dict[str, Any], plan: dict[str, Any], add_gate_suggestions: bool = True) -> tuple[Path, Path | None, int]:
    path = safe_calibration_dir(repo, "verification-plan write") / "verification-plan.json"
    write_json_atomic(path, plan)
    gate_path = None
    added = 0
    if add_gate_suggestions:
        gate_path, added = merge_gate_suggestions(repo, profile)
    return path, gate_path, added


def managed_source_files(source: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for current, dirs, names in os.walk(source, followlinks=False):
        current_path = Path(current)
        rel_dir = current_path.relative_to(source)
        excluded_here = {"__pycache__", ".git"}
        if not rel_dir.parts:
            excluded_here.update({"calibration", "incoming"})
        dirs[:] = sorted(
            d for d in dirs
            if d not in excluded_here and not path_is_linklike(current_path / d)
        )
        if rel_dir.parts and rel_dir.parts[0] in {"calibration", "incoming"}:
            continue
        for name in sorted(names):
            if name in {".adc-managed.json", ".DS_Store"} or name.endswith(".pyc"):
                continue
            path = current_path / name
            if path_is_linklike(path):
                continue
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
    require_no_symlink_components(source, repo, "legacy calibration migration source")
    require_no_symlink_components(destination, repo, "legacy calibration migration destination")
    if not source.exists() or source.resolve() == destination.resolve():
        return migrated
    source_symlinks = tree_symlinks(source)
    destination_symlinks = tree_symlinks(destination)
    if source_symlinks or destination_symlinks:
        shown = ", ".join(rel(item, repo) for item in [*source_symlinks, *destination_symlinks])
        raise SystemExit(f"Refused legacy calibration migration through link-like entries: {shown}")
    destination.mkdir(parents=True, exist_ok=True)
    for item in sorted(source.iterdir()):
        if not item.is_file() or path_is_linklike(item):
            continue
        dest = destination / item.name
        require_no_symlink_components(dest, repo, "legacy calibration file migration")
        if dest.exists():
            continue
        copy_file_atomic(item, dest)
        migrated.append(dest.relative_to(target).as_posix())
    return migrated


def initialize_calibration(target: Path, template_dir: Path, version: str, digest: str) -> list[str]:
    if path_is_linklike(template_dir) or not template_dir.exists() or not template_dir.is_dir():
        raise SystemExit(f"Calibration templates not found or unsafe: {template_dir}")
    template_symlinks = tree_symlinks(template_dir)
    if template_symlinks:
        raise SystemExit(
            "Calibration templates contain link-like entries: "
            + ", ".join(rel(item, template_dir) for item in template_symlinks)
        )
    created: list[str] = []
    cal = target / "calibration"
    if path_is_linklike(cal) or tree_symlinks(cal):
        raise SystemExit(f"Refused calibration initialization through link-like entries: {cal}")
    cal.mkdir(parents=True, exist_ok=True)
    for template in sorted(template_dir.iterdir()):
        if not template.is_file() or path_is_linklike(template):
            continue
        dest = cal / template.name
        if path_is_linklike(dest):
            raise SystemExit(f"Refused calibration template copy through symlink or junction: {dest}")
        if not dest.exists():
            copy_file_atomic(template, dest)
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
    should_adapter = hosts == "all" or (hosts == "auto" and ((repo / ".claude").exists() or (repo / "CLAUDE.md").exists()))
    adapter = repo / ".claude" / "skills" / "anti-dark-code" / "SKILL.md"
    require_no_symlink_components(target, repo, "managed skill installation")
    require_no_symlink_components(fallback_calibration, repo, "legacy calibration migration")
    if should_adapter:
        require_no_symlink_components(adapter, repo, "Claude adapter installation")
    existing_target_symlinks = tree_symlinks(target)
    if existing_target_symlinks:
        shown = ", ".join(rel(item, repo) for item in existing_target_symlinks)
        raise SystemExit(
            "Refused managed skill installation: the existing repo-local skill contains link-like entries: "
            + shown
        )
    existing_fallback_symlinks = tree_symlinks(fallback_calibration)
    if existing_fallback_symlinks:
        shown = ", ".join(rel(item, repo) for item in existing_fallback_symlinks)
        raise SystemExit(
            "Refused legacy calibration migration: the fallback calibration contains link-like entries: "
            + shown
        )
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
    if source_inspection["fatal_issues"]:
        blocked_reasons.extend(f"invalid installation source: {item}" for item in source_inspection["fatal_issues"])
    if source_inspection["template_errors"]:
        blocked_reasons.extend(f"unsafe calibration template: {item}" for item in source_inspection["template_errors"])
    if source_inspection["unsafe_issues"] and not allow_unsafe_source:
        blocked_reasons.extend(
            f"untrusted installation source: {item}; use --allow-unsafe-source only after manual review"
            for item in source_inspection["unsafe_issues"]
        )
    if binding["status"] == "invalid":
        blocked_reasons.append(
            "existing calibration is invalid and cannot be accepted automatically: "
            + str(binding.get("binding_error") or "unknown validation error")
            + "; repair or quarantine it before migration"
        )
    if binding["status"] == "unbound" and not accept_unbound_calibration:
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
    require_no_symlink_components(manifest_path, repo, "managed-install manifest read/write")
    old_manifest = read_json(manifest_path, {}) if manifest_path.exists() else {}
    old_files = old_manifest.get("files", {}) if isinstance(old_manifest, dict) else {}
    conflicts: list[str] = []
    copies: list[str] = []
    removals: list[str] = []

    for r, src in source_files.items():
        dst = target / r
        require_no_symlink_components(dst, repo, "managed skill update")
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
        require_no_symlink_components(dst, repo, "managed skill removal")
        if dst.exists() and sha256_file(dst) == old_hash:
            removals.append(r)
        elif dst.exists():
            conflicts.append(r)

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
            "fatal_issues": source_inspection["fatal_issues"],
            "unsafe_override_requested": allow_unsafe_source,
        },
        "calibration_preserved": True,
        "calibration_binding": {
            "status": binding["status"],
            "binding_source": binding_source.relative_to(repo).as_posix(),
            "stored_repository_id": binding["stored_repository_id"],
            "current_repository_id": binding["current_repository_id"],
            "identity_method": binding["identity_method"],
            "requires_accept_unbound": binding["status"] == "unbound",
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

    require_no_symlink_components(target, repo, "managed skill installation apply")
    target.mkdir(parents=True, exist_ok=True)
    for r in removals:
        removal_path = target / r
        require_no_symlink_components(removal_path, repo, "managed skill removal apply")
        try:
            removal_path.unlink()
        except FileNotFoundError:
            pass
    for r, src in source_files.items():
        dst = target / r
        require_no_symlink_components(dst, repo, "managed skill update apply")
        if dst.exists() and r in conflicts and not force:
            continue
        copy_file_atomic(src, dst)

    installed_files = {r: sha256_file(target / r) for r in sorted(source_files)}
    version = plan["version"]
    migrated_cal: list[str] = []
    if fallback_action == "migrate-missing-files":
        migrated_cal = migrate_fallback_calibration(repo, target)
    require_no_symlink_components(target_calibration, repo, "calibration initialization apply")
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
        accepted_unbound=binding["status"] == "unbound",
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
    require_no_symlink_components(manifest_path, repo, "managed-install manifest apply")
    write_json_atomic(manifest_path, manifest)

    adapter_created = False
    if should_adapter:
        require_no_symlink_components(adapter, repo, "Claude adapter installation apply")
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
    require_no_symlink_components(root / ".gitignore", repo, "run-artifact setup")
    require_no_symlink_components(root / "runs", repo, "run-artifact setup")
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
    return sorted(path for path in combined if not is_tooling_relpath(path))


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


def redact_literal_values(text: str, literal_values: Sequence[str]) -> str:
    result = text
    for value in literal_values:
        if len(value) < 4 and value.isalnum():
            result = re.sub(
                rf"(?<![A-Za-z0-9]){re.escape(value)}(?![A-Za-z0-9])",
                "<redacted-env-value>",
                result,
            )
        else:
            result = result.replace(value, "<redacted-env-value>")
    return result


def redact_log_file(raw_path: Path, redacted_path: Path, literal_values: Sequence[str] = ()) -> None:
    redacted_path.parent.mkdir(parents=True, exist_ok=True)
    with raw_path.open("r", encoding="utf-8", errors="replace") as source, redacted_path.open("w", encoding="utf-8", newline="\n") as destination:
        for line in source:
            redacted = redact_line(line)
            destination.write(redact_literal_values(redacted, literal_values) + "\n")


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


def gate_popen_kwargs() -> dict[str, Any]:
    """Launch each gate in its own process group without an interactive stdin."""
    kwargs: dict[str, Any] = {"stdin": subprocess.DEVNULL}
    if os.name == "nt":
        kwargs["creationflags"] = int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    else:
        kwargs["start_new_session"] = True
    return kwargs


def terminate_gate_process_tree(proc: subprocess.Popen[Any], grace_seconds: float = 2.0) -> dict[str, Any]:
    """Best-effort termination of a timed-out gate and the children it spawned."""
    result: dict[str, Any] = {
        "strategy": "windows-process-group" if os.name == "nt" else "posix-process-group",
        "grace_seconds": grace_seconds,
        "graceful_signal_sent": False,
        "forced_kill_sent": False,
        "errors": [],
    }

    if os.name == "nt":
        break_event = getattr(signal, "CTRL_BREAK_EVENT", None)
        if break_event is not None and proc.poll() is None:
            try:
                proc.send_signal(break_event)
                result["graceful_signal_sent"] = True
            except (OSError, ValueError) as exc:
                result["errors"].append(f"CTRL_BREAK_EVENT failed: {exc}")
        try:
            proc.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            try:
                taskkill = subprocess.run(
                    ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10,
                    check=False,
                )
                result["forced_kill_sent"] = True
                result["taskkill_exit_code"] = taskkill.returncode
            except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
                result["errors"].append(f"taskkill failed: {exc}")
            if proc.poll() is None:
                try:
                    proc.kill()
                    result["forced_kill_sent"] = True
                except OSError as exc:
                    result["errors"].append(f"direct kill failed: {exc}")
        try:
            proc.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            result["errors"].append("process did not exit after forced termination")
        result["return_code_after_termination"] = proc.poll()
        return result

    pgid = proc.pid
    try:
        pgid = os.getpgid(proc.pid)
    except ProcessLookupError:
        pass
    except OSError as exc:
        result["errors"].append(f"could not resolve process group: {exc}")

    try:
        os.killpg(pgid, signal.SIGTERM)
        result["graceful_signal_sent"] = True
    except ProcessLookupError:
        pass
    except OSError as exc:
        result["errors"].append(f"SIGTERM process-group kill failed: {exc}")

    deadline = time.monotonic() + grace_seconds
    group_alive = True
    while time.monotonic() < deadline:
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            group_alive = False
            break
        except PermissionError:
            group_alive = True
            break
        time.sleep(0.05)

    if group_alive:
        try:
            os.killpg(pgid, signal.SIGKILL)
            result["forced_kill_sent"] = True
        except ProcessLookupError:
            pass
        except OSError as exc:
            result["errors"].append(f"SIGKILL process-group kill failed: {exc}")

    try:
        proc.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        result["errors"].append("process did not exit after process-group termination")
        try:
            proc.kill()
            proc.wait(timeout=grace_seconds)
            result["forced_kill_sent"] = True
        except (OSError, subprocess.TimeoutExpired) as exc:
            result["errors"].append(f"direct fallback kill failed: {exc}")
    result["return_code_after_termination"] = proc.poll()
    return result


def run_gates(repo: Path, level: int, allow_exec: bool, changed_from: str | None, keep_going: bool) -> int:
    repo = repo.resolve()
    config_path = safe_calibration_dir(repo, "gate configuration read") / "gates.json"
    if not config_path.exists():
        raise SystemExit(f"Gate config not found: {config_path}")
    config = read_json(config_path)
    if not isinstance(config, dict) or not isinstance(config.get("gates", []), list):
        raise SystemExit(f"Invalid gate config structure: {config_path}")

    binding = assess_repository_binding(repo, config_path.parent)
    if binding["status"] != "match":
        print(
            "BLOCKED: calibration is "
            f"{binding['status']} for this repository. Migrate, accept, or rebind it before trusting local gates."
        )
        print("REFUSED: gate planning and execution cannot use unbound, invalid, or foreign calibration.")
        return 2

    candidates = [
        g for g in config.get("gates", [])
        if isinstance(g, dict) and g.get("enabled") and gate_level(g) <= level
    ]
    changed = changed_files(repo, changed_from) if changed_from else None
    candidates = [g for g in candidates if gate_applies(g, changed)]
    blocked: list[tuple[dict[str, Any], str]] = []
    gates: list[dict[str, Any]] = []
    runtime_environments: dict[int, tuple[dict[str, str], dict[str, Any], list[str]]] = {}
    for gate in candidates:
        if str(gate.get("review_status", "")).lower() != "approved":
            blocked.append((gate, f"review_status={gate.get('review_status', 'missing')}"))
            continue
        source_ok, source_reason = verify_gate_source(repo, gate)
        if not source_ok:
            blocked.append((gate, source_reason or "source definition is stale"))
            continue
        try:
            runtime_environments[id(gate)] = gate_environment(gate)
        except ValueError as exc:
            blocked.append((gate, str(exc)))
            continue
        gates.append(gate)

    if blocked:
        print(f"BLOCKED: {len(blocked)} enabled gate(s) need review:")
        for gate, reason in blocked:
            print(f"  {gate.get('id', 'unnamed')}: {reason}")
        print("REFUSED: rerun the planner after source changes, then approve each command and reconfirm execution safety.")
        return 2

    if not gates:
        print(f"NO GATES: no approved, enabled, applicable gates at Level {level}. Review {config_path}")
        return 0

    print(f"GATE PLAN: {len(gates)} approved gate(s), Level <= {level}, execute={'yes' if allow_exec else 'no'}")
    for gate in gates:
        shown_argv = redact_argv(gate.get("argv", []) if isinstance(gate.get("argv"), list) else [])
        environment_identity = runtime_environments[id(gate)][1]
        print(
            f"  L{gate.get('level')} {gate.get('id')}: {json.dumps(shown_argv)} "
            f"cwd={gate.get('cwd', '.')} resource={gate.get('resource_class', 'unknown')} "
            f"env={environment_identity['fingerprint']} inherit={str(environment_identity['inherit_env']).lower()} "
            f"overlay_keys={json.dumps(environment_identity['overlay_keys'])}"
        )
    if not allow_exec:
        print("DRY RUN: add --allow-exec only after command behavior, repo ownership, and machine cost are reviewed.")
        return 0

    owner_confirmed = bool(config.get("execution_policy", {}).get("owner_confirmed_safe_to_execute"))
    if not owner_confirmed:
        print("REFUSED: gates.json does not record owner confirmation. Review commands, then set execution_policy.owner_confirmed_safe_to_execute to true.")
        return 2

    ensure_run_gitignore(repo)
    require_no_symlink_components(repo / ".anti-dark-code" / "runs", repo, "gate run creation")
    source_identity = current_source_identity(repo)
    gate_material = [
        {
            "id": g.get("id"),
            "definition": gate_definition_hash(g),
            "environment": runtime_environments[id(g)][1]["fingerprint"],
        }
        for g in gates
    ]
    input_hash = sha256_bytes(json.dumps({"level": level, "gates": gate_material, "source": source_identity, "changed": changed or []}, sort_keys=True).encode())[:10]
    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + input_hash
    run_dir = repo / ".anti-dark-code" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    failures: list[dict[str, Any]] = []
    passed = 0
    started_all = time.monotonic()

    def record_config_failure(gate_id: str, gate: dict[str, Any], message: str) -> None:
        environment_identity = runtime_environments.get(id(gate), ({}, {}, []))[1]
        core = {"gate": gate_id, "config_error": message, "source": source_identity, "environment": environment_identity.get("fingerprint")}
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
            "environment_identity": environment_identity or None,
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
        process_env, environment_identity, environment_redactions = runtime_environments[id(gate)]
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
        timeout_termination: dict[str, Any] | None = None
        proc: subprocess.Popen[Any] | None = None
        try:
            raw_path.touch(mode=0o600, exist_ok=False)
            with raw_path.open("w", encoding="utf-8", newline="\n") as raw_log:
                proc = subprocess.Popen(
                    argv,
                    cwd=cwd,
                    env=process_env,
                    stdout=raw_log,
                    stderr=subprocess.STDOUT,
                    text=True,
                    **gate_popen_kwargs(),
                )
                try:
                    exit_code = proc.wait(timeout=timeout_seconds)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    timeout_termination = terminate_gate_process_tree(proc)
                    exit_code = 124
                    raw_log.write(
                        f"\n[anti-dark-code] TIMEOUT after {timeout_seconds}s; "
                        f"termination={timeout_termination['strategy']}\n"
                    )
                except KeyboardInterrupt:
                    terminate_gate_process_tree(proc)
                    raise
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
                    redact_log_file(raw_path, log_path, environment_redactions)
                finally:
                    raw_path.unlink(missing_ok=True)

        duration = round(time.monotonic() - started, 3)
        if exit_code == 0:
            passed += 1
            print(f"PASS {gate_id} ({duration:.3f}s)")
            continue

        bounded = bounded_log(log_path)
        failure_core = {
            "gate": gate_id,
            "exit": exit_code,
            "source": source_identity,
            "environment": environment_identity["fingerprint"],
            "tail": bounded[-12:],
        }
        failure_id = "ADC-FAIL-" + sha256_bytes(json.dumps(failure_core, sort_keys=True).encode())[:12]
        shown_argv = redact_argv(argv)
        packet = {
            "schema_version": SCHEMA_VERSION,
            "failure_id": failure_id,
            "gate_id": gate_id,
            "level": gate.get("level"),
            "exit_code": exit_code,
            "timed_out": timed_out,
            "timeout_termination": timeout_termination,
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
            "environment_identity": environment_identity,
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
        "environment_identities": [
            {"gate_id": str(g.get("id") or "unnamed"), **runtime_environments[id(g)][1]}
            for g in gates
        ],
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
    calibration = safe_calibration_dir(repo, "flow-back calibration read/write")
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
    require_no_symlink_components(out_dir, repo, "flow-back proposal write")
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
        if parent_scope["fatal_issues"] or parent_scope["unsafe_issues"] or parent_scope["template_errors"]:
            raise SystemExit("Parent skill is not a clean universal core. Stage the proposal to a reviewed shared source instead.")
        incoming = parent / "incoming"
        destination = incoming / out_path.name
        require_no_symlink_components(destination, parent, "shared-core incoming proposal staging")
        incoming.mkdir(parents=True, exist_ok=True)
        copy_file_atomic(out_path, destination)

    if mark_staged:
        text = candidate_path.read_text(encoding="utf-8")
        for candidate in candidates:
            heading = re.escape(f"## {candidate['id']}: {candidate['title']}")
            pattern = rf"({heading}.*?^-\s+Status:\s*)ready\b"
            text = re.sub(pattern, rf"\1staged", text, flags=re.M | re.S | re.I)
        write_text_atomic(candidate_path, text)
    return out_path


def is_validation_runtime_path(path: Path, skill: Path, mode: str) -> bool:
    try:
        relative = path.relative_to(skill)
    except ValueError:
        return False
    if not relative.parts:
        return False
    top = relative.parts[0]
    if mode == "installed":
        return top in {"calibration", "incoming"} or relative.as_posix() == ".adc-managed.json"
    if mode == "universal":
        return top in {"calibration", "incoming"} or relative.as_posix() == ".adc-managed.json"
    return False


def resolve_validation_mode(skill: Path, requested: str = "auto") -> str:
    if requested == "source":
        requested = "universal"
    if requested not in VALIDATION_MODES:
        raise SystemExit(f"Unknown validation mode: {requested}")
    if requested != "auto":
        return requested
    lexical_skill = lexical_absolute(skill.expanduser())
    if (lexical_skill / ".adc-managed.json").exists():
        return "installed"
    if tuple(lexical_skill.parts[-3:]) == (".agents", "skills", "anti-dark-code"):
        # The canonical repo-local path is installed mode even when it is an
        # unsafe symlink. This lets validation report the symlink instead of
        # silently treating the target as a user-level universal alias.
        return "installed"
    return "universal"


def installed_repo_root(skill: Path) -> Path | None:
    if tuple(skill.parts[-3:]) == (".agents", "skills", "anti-dark-code"):
        return skill.parents[2]
    return None


def validate_installed_manifest(skill: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    manifest_path = skill / ".adc-managed.json"
    if not manifest_path.exists():
        return ["Installed validation requires .adc-managed.json"], warnings
    if path_is_linklike(manifest_path):
        return ["Installed manifest must not be a symlink or junction"], warnings
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Invalid installed manifest {manifest_path}: {exc}"], warnings
    if not isinstance(manifest, dict):
        return ["Installed manifest is not a JSON object"], warnings

    expected_files = manifest.get("files")
    if not isinstance(expected_files, dict) or not expected_files:
        errors.append("Installed manifest has no managed file map")
        expected_files = {}

    normalized_expected: dict[str, str] = {}
    for raw_name, raw_hash in expected_files.items():
        if not isinstance(raw_name, str) or not isinstance(raw_hash, str):
            errors.append("Installed manifest file entries must map string paths to SHA-256 strings")
            continue
        name = raw_name.replace("\\", "/")
        parts = tuple(part for part in name.split("/") if part)
        if raw_name.startswith(("/", "\\")) or not parts or any(part in {".", ".."} for part in parts):
            errors.append(f"Installed manifest contains unsafe managed path: {raw_name}")
            continue
        if not re.fullmatch(r"[0-9a-f]{64}", raw_hash):
            errors.append(f"Installed manifest contains invalid SHA-256 for {raw_name}")
            continue
        normalized_expected["/".join(parts)] = raw_hash

    actual_files = managed_source_files(skill)
    expected_names = set(normalized_expected)
    actual_names = set(actual_files)
    for name in sorted(expected_names - actual_names):
        errors.append(f"Managed installed file is missing: {name}")
    for name in sorted(actual_names - expected_names):
        errors.append(f"Unexpected unmanaged core file in installed skill: {name}")
    for name in sorted(expected_names & actual_names):
        path = actual_files[name]
        if path_is_linklike(path):
            errors.append(f"Managed installed file is a symlink or junction: {name}")
            continue
        actual_hash = sha256_file(path)
        if actual_hash != normalized_expected[name]:
            errors.append(f"Managed installed file checksum mismatch: {name}")

    if expected_names == actual_names and not any("checksum mismatch" in item for item in errors):
        expected_core = manifest.get("source_core_sha256")
        actual_core = core_digest(actual_files)
        if not isinstance(expected_core, str) or actual_core != expected_core:
            errors.append("Installed core digest does not match .adc-managed.json")

    version_path = skill / "VERSION"
    manifest_version = manifest.get("source_version")
    if version_path.exists() and isinstance(manifest_version, str):
        installed_version = version_path.read_text(encoding="utf-8").strip()
        if installed_version != manifest_version:
            errors.append("Installed VERSION does not match .adc-managed.json")

    marker_path = skill / SOURCE_SCOPE_FILENAME
    expected_marker_hash = manifest.get("source_scope_marker_sha256")
    if marker_path.exists() and isinstance(expected_marker_hash, str):
        if sha256_file(marker_path) != expected_marker_hash:
            errors.append(f"Installed {SOURCE_SCOPE_FILENAME} checksum mismatch")

    calibration = skill / "calibration"
    calibration_symlinks = ([calibration] if path_is_linklike(calibration) else []) + tree_symlinks(calibration)
    if calibration_symlinks:
        errors.append(
            "Installed calibration contains link-like entries: "
            + ", ".join(item.relative_to(skill).as_posix() for item in calibration_symlinks)
        )
    calibration_json_paths = (
        list(calibration.rglob("*.json"))
        if calibration.exists() and calibration.is_dir() and not path_is_linklike(calibration)
        else []
    )
    for json_path in calibration_json_paths:
        if path_is_linklike(json_path):
            errors.append(f"Installed calibration JSON must not be a symlink or junction: {json_path.relative_to(skill)}")
            continue
        try:
            json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Invalid installed calibration JSON {json_path.relative_to(skill)}: {exc}")

    repo = installed_repo_root(skill)
    if repo is None:
        warnings.append("Could not infer repository root for calibration-binding validation")
    else:
        binding = assess_repository_binding(repo, skill / "calibration")
        if binding["status"] != "match":
            errors.append(
                f"Installed calibration binding is {binding['status']} for repository {repo}"
            )
    return errors, warnings


def validate_skill(skill: Path, mode: str = "auto") -> tuple[list[str], list[str]]:
    requested_skill = skill.expanduser()
    skill_path_was_symlink = path_is_linklike(requested_skill)
    validation_mode = resolve_validation_mode(requested_skill, mode)
    skill = requested_skill.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    if skill_path_was_symlink:
        if validation_mode in {"distribution", "installed"}:
            errors.append(f"{validation_mode.capitalize()} skill root must not be a symlink or junction: {requested_skill}")
        else:
            warnings.append(f"Universal skill root is reached through a symlink alias: {requested_skill}")
    skill_md = skill / "SKILL.md"
    if not skill_md.exists():
        errors.append(f"Missing {skill_md}")
        return errors, warnings
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

    excluded_symlink_roots = {"calibration", "incoming"} if validation_mode in {"universal", "installed"} else set()
    core_symlinks = tree_symlinks(skill, excluded_top_level=excluded_symlink_roots)
    if core_symlinks:
        errors.append(
            "Core contains link-like entries: "
            + ", ".join(item.relative_to(skill).as_posix() for item in core_symlinks)
        )

    source_calibration = skill / "calibration"
    source_calibration_files = calibration_payload_files(source_calibration)
    source_calibration_symlinks = ([source_calibration] if path_is_linklike(source_calibration) else []) + tree_symlinks(source_calibration)
    incoming_path = skill / "incoming"
    incoming_entries = calibration_payload_files(incoming_path)
    incoming_symlinks = ([incoming_path] if path_is_linklike(incoming_path) else []) + tree_symlinks(incoming_path)

    if validation_mode in {"universal", "distribution"}:
        if (skill / ".adc-managed.json").exists():
            errors.append("Universal source contains a repo-local .adc-managed.json")
        if source_calibration_files or source_calibration_symlinks:
            entries = [item.relative_to(skill).as_posix() for item in source_calibration_files]
            entries.extend(item.relative_to(skill).as_posix() for item in source_calibration_symlinks)
            errors.append(
                "Universal core contains repo-owned top-level calibration: "
                + ", ".join(sorted(set(entries)))
            )
    if validation_mode == "distribution" and (incoming_path.exists() or path_is_linklike(incoming_path)):
        entries = [item.relative_to(skill).as_posix() for item in incoming_entries]
        entries.extend(item.relative_to(skill).as_posix() for item in incoming_symlinks)
        errors.append(
            "Distribution contains the runtime-only incoming/ inbox"
            + (": " + ", ".join(sorted(set(entries))) if entries else "")
        )
    elif validation_mode == "universal" and incoming_symlinks:
        errors.append(
            "Live universal incoming/ inbox contains link-like entries: "
            + ", ".join(item.relative_to(skill).as_posix() for item in incoming_symlinks)
        )
        if incoming_entries:
            warnings.append(
                f"Ignored {len(incoming_entries)} staged incoming item(s) while validating the live universal core"
            )
    elif validation_mode == "universal" and incoming_entries:
        warnings.append(
            f"Ignored {len(incoming_entries)} staged incoming item(s) while validating the live universal core"
        )
    elif validation_mode == "installed" and (incoming_path.exists() or path_is_linklike(incoming_path)):
        errors.append("Installed repo copy must not contain the shared-core incoming/ inbox")

    artifact_paths = [
        path.relative_to(skill).as_posix()
        for path in skill.rglob("*")
        if not is_validation_runtime_path(path, skill, validation_mode)
        and (path.name == "__pycache__" or path.suffix == ".pyc")
    ]
    if artifact_paths:
        message = "Generated Python artifacts found in skill tree: " + ", ".join(sorted(artifact_paths))
        if validation_mode == "distribution":
            errors.append(message)
        else:
            warnings.append(message + f"; ignored in {validation_mode} validation")

    for json_path in list(skill.rglob("*.json")):
        if is_validation_runtime_path(json_path, skill, validation_mode):
            continue
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
        if is_validation_runtime_path(path, skill, validation_mode) or path_is_linklike(path):
            continue
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
    if validation_mode == "installed":
        installed_errors, installed_warnings = validate_installed_manifest(skill)
        errors.extend(installed_errors)
        warnings.extend(installed_warnings)
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
    path = safe_calibration_dir(repo, "repository profile read") / "repo-profile.json"
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
    mode = resolve_validation_mode(skill, args.mode)
    errors, warnings = validate_skill(skill, mode=args.mode)
    for warning in warnings:
        print(f"WARN {warning}")
    for error in errors:
        print(f"ERROR {error}")
    if errors:
        print(f"INVALID ({mode}): {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"VALID ({mode}): 0 errors, {len(warnings)} warning(s)")
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

    p = sub.add_parser("validate", help="Validate a distribution, live universal core, or installed repo copy")
    p.add_argument("--skill")
    p.add_argument("--mode", choices=VALIDATION_MODES, default="auto")
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
