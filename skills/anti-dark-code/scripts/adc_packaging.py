#!/usr/bin/env python3
"""Generate/check inert plugin metadata; never install plugins or enable hooks."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess

CORE_PATH = Path("skills/anti-dark-code")
SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
REPOSITORY = "https://github.com/LynxTWO/anti-dark-code-skill"


def plugin_version(version: str) -> str:
    """Represent the canonical padded calendar version as strict SemVer."""
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(-unified\.(0|[1-9]\d*))?", version)
    if not match:
        raise ValueError("VERSION must be a three-part calendar version with optional -unified.N")
    return ".".join(str(int(match[i])) for i in (1, 2, 3)) + (match[4] or "")


def metadata(version: str) -> dict[str, dict]:
    shared = {
        "name": "anti-dark-code",
        "version": plugin_version(version),
        "description": "Evidence-based architecture review, code audits, verification, and authorized improvements.",
        "author": {"name": "LynxTWO", "url": "https://github.com/LynxTWO"},
        "homepage": REPOSITORY,
        "repository": REPOSITORY,
        "license": "FSL-1.1-MIT",
        "keywords": ["code-review", "architecture", "verification", "agent-skills"],
    }
    interface = {
        "displayName": "Anti-Dark-Code",
        "shortDescription": "Review and improve code from evidence.",
        "longDescription": "Map unfamiliar code, investigate supported findings, and verify authorized changes. Optional usage collection remains opt-in.",
        "developerName": "LynxTWO",
        "category": "Productivity",
        "capabilities": ["Read", "Write"],
        "websiteURL": REPOSITORY,
        "defaultPrompt": ["Use anti-dark-code to map this repository and identify the next useful checks."],
    }
    return {
        "plugin.json": {"$schema": SCHEMA, **shared, "extensions": {"com.openai": {"interface": interface}}},
        ".codex-plugin/plugin.json": {**shared, "skills": "./skills/", "interface": interface},
        ".claude-plugin/plugin.json": {**shared, "skills": ["./skills/"]},
        "gemini-extension.json": {key: shared[key] for key in ("name", "version", "description")},
        ".agents/plugins/marketplace.json": {
            "name": "anti-dark-code",
            "interface": {"displayName": "Anti-Dark-Code"},
            "plugins": [{
                "name": "anti-dark-code", "source": {"source": "local", "path": "./"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Productivity",
            }],
        },
        ".claude-plugin/marketplace.json": {
            "name": "anti-dark-code",
            "description": shared["description"],
            "owner": shared["author"],
            "plugins": [{"name": "anti-dark-code", "source": "./", "description": shared["description"]}],
        },
    }


def linklike(path: Path) -> bool:
    return path.is_symlink() or path.is_junction()


def validate_package(repo: Path) -> list[str]:
    repo = repo.resolve()
    errors = []
    core = repo / CORE_PATH
    if not (core / "SKILL.md").is_file():
        return ["missing discoverable skills/anti-dark-code/SKILL.md"]
    if (repo / "anti-dark-code").exists():
        errors.append("legacy anti-dark-code/ would duplicate the canonical core")
    if any(linklike(path) for path in (repo / "skills", core)):
        errors.append("plugin skill paths must be real directories")
    try:
        expected = metadata((core / "VERSION").read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return errors + ["missing or invalid canonical VERSION"]
    for relative, wanted in expected.items():
        path = repo / relative
        if linklike(path) or any(linklike(parent) for parent in path.parents if parent.is_relative_to(repo) and parent != repo):
            errors.append(f"{relative}: metadata path must not traverse links")
            continue
        try:
            actual = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            errors.append(f"{relative}: missing or invalid JSON")
            continue
        if actual != wanted:
            errors.append(f"{relative}: metadata differs from VERSION or the declared skill-only package")
    return errors


def check_hosts(repo: Path) -> list[dict]:
    """Run only explicitly requested, read-only validators that are available."""
    commands = [
        ("claude", ["plugin", "validate", "--strict", str(repo)]),
        ("skills-ref", ["validate", str(repo / CORE_PATH)]),
        ("gh", ["skill", "publish", str(repo), "--dry-run"]),
    ]
    results = []
    for name, args in commands:
        executable = shutil.which(name)
        if not executable:
            results.append({"host": name, "status": "capability_unavailable"})
            continue
        try:
            if name == "gh":
                help_result = subprocess.run([executable, "skill", "publish", "--help"],
                                             capture_output=True, text=True, timeout=30)
                if help_result.returncode or "--dry-run" not in help_result.stdout:
                    results.append({"host": name, "status": "capability_unavailable"})
                    continue
            result = subprocess.run([executable, *args], cwd=repo,
                                    capture_output=True, text=True, timeout=60)
            results.append({"host": name, "status": "passed" if result.returncode == 0 else "failed",
                            "exit_code": result.returncode,
                            "output": (result.stdout + result.stderr)[-8000:]})
        except (OSError, subprocess.TimeoutExpired) as error:
            results.append({"host": name, "status": "failed", "error": type(error).__name__})
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--write", action="store_true", help="Regenerate the six metadata files; no installation")
    parser.add_argument("--host-checks", action="store_true", help="Run available read-only host validators; report missing tools")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.write:
        core = repo / CORE_PATH
        expected = metadata((core / "VERSION").read_text(encoding="utf-8").strip())
        # Inspect every destination before touching any file.
        for relative in expected:
            path = repo / relative
            for part in (path, *path.parents):
                if part == repo:
                    break
                if linklike(part):
                    parser.error(f"refusing linked metadata destination: {relative}")
        for relative, value in expected.items():
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    errors = validate_package(repo)
    for error in errors:
        print(f"ERROR {error}")
    print(f"{'INVALID' if errors else 'VALID'} plugin package: {len(errors)} error(s)")
    host_results = check_hosts(repo) if args.host_checks and not errors else []
    for result in host_results:
        print(json.dumps(result))
    return int(bool(errors) or any(item["status"] == "failed" for item in host_results))


if __name__ == "__main__":
    raise SystemExit(main())
