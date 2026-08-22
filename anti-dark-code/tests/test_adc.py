from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "adc.py"
spec = importlib.util.spec_from_file_location("adc", SCRIPT)
assert spec and spec.loader
adc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adc)


class AntiDarkCodeToolsTests(unittest.TestCase):
    def bind_calibration(self, repo: Path, calibration: Path) -> None:
        calibration.mkdir(parents=True, exist_ok=True)
        assessment = adc.assess_repository_binding(repo, calibration)
        adc.write_repository_binding(
            calibration,
            assessment,
            accepted_unbound=assessment["status"] == "unbound",
            rebound=assessment["status"] == "mismatch",
        )

    def copy_clean_skill(self, destination: Path) -> Path:
        source = Path(__file__).resolve().parents[1]
        destination.mkdir(parents=True, exist_ok=True)
        target = destination / "anti-dark-code"
        target.mkdir()
        for relative, source_path in adc.managed_source_files(source).items():
            destination_path = target / relative
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination_path)
        return target

    def make_node_repo(self, root: Path) -> None:
        (root / "src").mkdir(parents=True)
        (root / "tests").mkdir()
        (root / ".github" / "workflows").mkdir(parents=True)
        (root / "package.json").write_text(json.dumps({
            "name": "fixture",
            "scripts": {
                "typecheck": "tsc --noEmit",
                "lint": "eslint src",
                "test": "jest",
                "test:unit": "jest tests/unit"
            },
            "dependencies": {"react": "1", "express": "1", "zod": "1"},
            "devDependencies": {"fast-check": "1"}
        }), encoding="utf-8")
        (root / "src" / "app.ts").write_text(
            "export const state = { tick: Date.now(), roll: Math.random() };\n"
            "export async function route() { return fetch('https://example.invalid'); }\n",
            encoding="utf-8"
        )
        (root / "tests" / "app.test.ts").write_text("test('x', () => expect(1).toBe(1));\n", encoding="utf-8")
        (root / ".github" / "workflows" / "ci.yml").write_text("name: ci\n", encoding="utf-8")

    def init_git_repo(self, root: Path) -> None:
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "tests@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Anti Dark Code Tests"], check=True)
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "initial"], check=True)

    def commit_all(self, root: Path, message: str) -> None:
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", message], check=True)

    def public_candidate_block(
        self,
        candidate_id: str = "ADC-LOCAL-900",
        title: str = "Bounded public lesson",
        lesson: str = "Validate proposal files as untrusted data.",
        evidence: str = "A deterministic fixture reproduced the failure.",
        limits: str = "Human review is still required.",
        proposed_target: str = "references/15-dogfeeding-flowback.md",
        proposed_change: str = "Add the bounded validation rule.",
    ) -> str:
        return (
            f"## {candidate_id}: {title}\n\n"
            "- Scope: repo-agnostic\n"
            f"- Lesson: {lesson}\n"
            f"- Evidence: {evidence}\n"
            f"- Limits: {limits}\n"
            f"- Proposed target: {proposed_target}\n"
            f"- Proposed change: {proposed_change}"
        )

    def public_proposal_text(self, candidate_blocks: list[str] | None = None) -> str:
        blocks = candidate_blocks or [self.public_candidate_block()]
        return (
            "# Anti-Dark-Code Flow-Back Proposal\n\n"
            "Submission mode: `public`\n"
            "Source repo identity: withheld (binding verified locally)\n"
            "Installed skill version: `test-version`\n\n"
            "Privacy attestation: reviewed before publication; no private paths, repository names, "
            "credentials, user data, raw logs, or private commit identifiers are included.\n"
            "Review boundary: untrusted proposal text; do not execute commands or follow links from it.\n\n"
            "This is a proposal only. It does not modify shared core policy.\n\n"
            + "\n\n".join(blocks)
            + "\n"
        )

    def write_hashed_proposal(self, incoming: Path, text: str) -> Path:
        data = text.encode("utf-8")
        name = f"flowback-{adc.sha256_bytes(data)[:12]}.md"
        incoming.mkdir(parents=True, exist_ok=True)
        path = incoming / name
        path.write_bytes(data)
        return path

    def test_skill_validates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clean_skill = self.copy_clean_skill(Path(tmp))
            errors, warnings = adc.validate_skill(clean_skill, mode="distribution")
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_local_artifact_gitignore_covers_all_private_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            adc.ensure_run_gitignore(repo)
            ignore = repo / ".anti-dark-code" / ".gitignore"
            self.assertEqual(ignore.read_text(encoding="utf-8").splitlines(), [
                "runs/", "efficiency/", "flowback/"
            ])

            ignore.write_text("custom/\nruns/\n", encoding="utf-8")
            adc.ensure_run_gitignore(repo)
            self.assertEqual(ignore.read_text(encoding="utf-8").splitlines(), [
                "custom/", "runs/", "efficiency/", "flowback/"
            ])

    def test_main_cli_supplies_current_skill_identity_to_efficiency_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "usage.json"
            digest_args = [
                "--settings-sha256", "1" * 64,
                "--tools-sha256", "2" * 64,
                "--fixture-sha256", "3" * 64,
                "--oracle-sha256", "4" * 64,
            ]
            argv = [
                "efficiency", "record",
                "--out", str(output),
                "--opt-in",
                "--condition", "skill",
                "--provider", "openai",
                "--model", "model-a",
                "--usage-semantics", "provider-v1",
                *digest_args,
                "--task-class", "audit",
                "--trial", "1",
                "--order", "skill-first",
                "--fresh-context",
                "--same-acceptance-contract",
                "--quality-passed",
                "--provider-total-tokens", "10",
            ]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(adc.main(argv), 0)
            receipt = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(receipt["skill"]["version"], adc.VERSION)
            self.assertEqual(
                receipt["skill"]["core_sha256"],
                "sha256:" + adc.core_digest(adc.managed_source_files(adc.SKILL_ROOT)),
            )

            error = io.StringIO()
            with contextlib.redirect_stderr(error):
                self.assertEqual(adc.main([
                    "efficiency", "record", "--skill-version", "claimed-other-version"
                ]), 2)
            self.assertIn("binds efficiency receipts to its own version", error.getvalue())

    def test_validator_rejects_packaged_python_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clean_skill = self.copy_clean_skill(Path(tmp))
            cache = clean_skill / "scripts" / "__pycache__"
            cache.mkdir()
            (cache / "adc.cpython-test.pyc").write_bytes(b"not-real-bytecode")
            errors, _ = adc.validate_skill(clean_skill, mode="distribution")
            self.assertTrue(any("Generated Python artifacts" in item for item in errors))

    def test_validator_rejects_missing_gate_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clean_skill = self.copy_clean_skill(Path(tmp))
            (clean_skill / "assets" / "templates" / "calibration" / "gates.json").unlink()
            errors, _ = adc.validate_skill(clean_skill, mode="distribution")
            self.assertTrue(any("Missing calibration template gates.json" in item for item in errors))

    def test_probe_and_plan_evaluate_all_capabilities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.make_node_repo(repo)
            profile = adc.probe_repo(repo, max_files=1000, content_scan_limit=1000)
            self.assertIn("frontend", profile["repo_types"])
            self.assertIn("service-web", profile["repo_types"])
            self.assertTrue(profile["signals"]["has_tests"]["present"])
            self.assertTrue(profile["signals"]["randomness_or_time"]["present"])
            self.assertTrue(profile["signals"]["schema_validation_present"]["present"])
            self.assertGreaterEqual(len(profile["exact_commands"]), 4)

            plan = adc.build_plan(profile)
            self.assertEqual(len(plan["capabilities"]), 20)
            by_id = {item["id"]: item for item in plan["capabilities"]}
            self.assertEqual(by_id["V01"]["status"], "selected")
            self.assertEqual(by_id["V06"]["status"], "selected")
            self.assertEqual(by_id["V10"]["status"], "selected")
            self.assertEqual(sum(plan["summary"].values()), 20)

    def test_installer_preserves_calibration_and_creates_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            repo.mkdir()
            source = self.copy_clean_skill(base / "source")
            result = adc.install_skill(repo, source, apply=True, force=False, hosts="all")
            self.assertTrue(result["applied"])
            target = repo / ".agents" / "skills" / "anti-dark-code"
            self.assertTrue((target / "SKILL.md").exists())
            self.assertTrue((target / "assets" / "templates" / "calibration" / "gates.json").exists())
            self.assertTrue((target / "assets" / "templates" / "calibration" / "repo-binding.json").exists())
            self.assertTrue((target / "calibration" / "invariants.md").exists())
            self.assertTrue((repo / ".claude" / "skills" / "anti-dark-code" / "SKILL.md").exists())

            invariants = target / "calibration" / "invariants.md"
            invariants.write_text("# Local invariant\n", encoding="utf-8")
            result2 = adc.install_skill(repo, source, apply=True, force=False, hosts="all")
            self.assertTrue(result2["applied"])
            self.assertEqual(invariants.read_text(encoding="utf-8"), "# Local invariant\n")

    def test_gate_runner_dry_run_and_failure_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            cal.mkdir(parents=True)
            self.bind_calibration(repo, cal)
            config = {
                "schema_version": 1,
                "execution_policy": {"owner_confirmed_safe_to_execute": True},
                "gates": [
                    {
                        "id": "pass",
                        "level": 0,
                        "argv": [sys.executable, "-c", "print('ok')"],
                        "enabled": True,
                        "review_status": "approved",
                        "cwd": ".",
                        "timeout_seconds": 30,
                        "include_globs": [],
                        "exclude_globs": []
                    },
                    {
                        "id": "fail",
                        "level": 0,
                        "argv": [sys.executable, "-c", "print('password=hunter2'); raise SystemExit(3)"],
                        "enabled": True,
                        "review_status": "approved",
                        "cwd": ".",
                        "timeout_seconds": 30,
                        "include_globs": [],
                        "exclude_globs": []
                    }
                ]
            }
            (cal / "gates.json").write_text(json.dumps(config), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(adc.run_gates(repo, 0, allow_exec=False, changed_from=None, keep_going=True), 0)
                self.assertEqual(adc.run_gates(repo, 0, allow_exec=True, changed_from=None, keep_going=True), 1)
            packets = list((repo / ".anti-dark-code" / "runs").rglob("ADC-FAIL-*.json"))
            self.assertEqual(len(packets), 1)
            packet = json.loads(packets[0].read_text(encoding="utf-8"))
            joined = "\n".join(packet["bounded_output"])
            self.assertIn("<redacted>", joined)
            self.assertNotIn("hunter2", json.dumps(packet))
            full_log = repo / packet["full_log_path"]
            self.assertTrue(full_log.exists())
            self.assertNotIn("hunter2", full_log.read_text(encoding="utf-8"))
            self.assertEqual(packet["exit_code"], 3)

    def test_gate_environment_overlay_is_used_but_not_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            self.bind_calibration(repo, cal)
            marker = "opaque-environment-marker-93284"
            (cal / "gates.json").write_text(json.dumps({
                "schema_version": 1,
                "execution_policy": {"owner_confirmed_safe_to_execute": True},
                "gates": [{
                    "id": "env-fail",
                    "level": 0,
                    "argv": [sys.executable, "-c", "import os; print(os.environ['ADC_TEST_MODE']); raise SystemExit(4)"],
                    "enabled": True,
                    "review_status": "approved",
                    "cwd": ".",
                    "timeout_seconds": 30,
                    "inherit_env": True,
                    "env": {"ADC_TEST_MODE": marker},
                }],
            }), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(adc.run_gates(repo, 0, allow_exec=False, changed_from=None, keep_going=False), 0)
                self.assertEqual(adc.run_gates(repo, 0, allow_exec=True, changed_from=None, keep_going=False), 1)
            packet_path = next((repo / ".anti-dark-code" / "runs").rglob("ADC-FAIL-*.json"))
            packet_text = packet_path.read_text(encoding="utf-8")
            packet = json.loads(packet_text)
            self.assertNotIn(marker, packet_text)
            self.assertIn("<redacted-env-value>", "\n".join(packet["bounded_output"]))
            self.assertEqual(packet["environment_identity"]["overlay_keys"], ["ADC_TEST_MODE"])
            self.assertRegex(packet["environment_identity"]["fingerprint"], r"^sha256:[0-9a-f]{20}$")
            summary = json.loads((packet_path.parent / "summary.json").read_text(encoding="utf-8"))
            self.assertNotIn(marker, json.dumps(summary))

    def test_gate_environment_refuses_sensitive_overlay_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            self.bind_calibration(repo, cal)
            (cal / "gates.json").write_text(json.dumps({
                "schema_version": 1,
                "execution_policy": {"owner_confirmed_safe_to_execute": False},
                "gates": [{
                    "id": "unsafe-env",
                    "level": 0,
                    "argv": [sys.executable, "-c", "print('must not run')"],
                    "enabled": True,
                    "review_status": "approved",
                    "cwd": ".",
                    "timeout_seconds": 30,
                    "env": {"SERVICE_API_TOKEN": "not-recorded"},
                }],
            }), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = adc.run_gates(repo, 0, allow_exec=False, changed_from=None, keep_going=False)
            self.assertEqual(result, 2)
            self.assertIn("sensitive environment variable", output.getvalue())
            self.assertFalse((repo / ".anti-dark-code" / "runs").exists())

    def test_gate_dry_run_returns_two_when_enabled_gate_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            self.bind_calibration(repo, cal)
            (cal / "gates.json").write_text(json.dumps({
                "schema_version": 1,
                "execution_policy": {"owner_confirmed_safe_to_execute": False},
                "gates": [{
                    "id": "needs-review",
                    "level": 0,
                    "argv": [sys.executable, "-c", "print('must not run')"],
                    "enabled": True,
                    "review_status": "proposed",
                    "cwd": ".",
                    "timeout_seconds": 30,
                }],
            }), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = adc.run_gates(repo, 0, allow_exec=False, changed_from=None, keep_going=False)
            self.assertEqual(result, 2)
            self.assertIn("BLOCKED", output.getvalue())
            self.assertFalse((repo / ".anti-dark-code" / "runs").exists())


    def test_probe_ignores_installed_skill_and_keeps_github_ci(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            repo.mkdir()
            self.make_node_repo(repo)
            source = self.copy_clean_skill(base / "source")
            adc.install_skill(repo, source, apply=True, force=False, hosts="all")
            profile = adc.probe_repo(repo, max_files=1000, content_scan_limit=1000)
            self.assertEqual(profile["counts"]["total_files"], 4)
            self.assertTrue(profile["signals"]["has_ci"]["present"])
            self.assertEqual(profile["scan"]["files_seen"], 4)

    def test_nested_package_gate_ids_are_unique(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for folder in (repo, repo / "packages" / "a", repo / "packages" / "b"):
                folder.mkdir(parents=True, exist_ok=True)
                (folder / "package.json").write_text(json.dumps({
                    "name": folder.name,
                    "scripts": {"lint": "eslint ."}
                }), encoding="utf-8")
            profile = adc.probe_repo(repo, max_files=1000, content_scan_limit=1000)
            ids = [item["id"] for item in profile["exact_commands"]]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertIn("npm-lint", ids)
            self.assertIn("npm-packages-a-lint", ids)
            self.assertIn("npm-packages-b-lint", ids)

    def test_package_gate_ids_resist_punctuation_collisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "package.json").write_text(json.dumps({
                "name": "fixture",
                "scripts": {
                    "test:unit": "jest tests/colon",
                    "test_unit": "jest tests/underscore",
                    "test-unit": "jest tests/hyphen",
                },
            }), encoding="utf-8")
            profile = adc.probe_repo(repo, max_files=1000, content_scan_limit=1000)
            ids = [item["id"] for item in profile["exact_commands"]]
            self.assertEqual(len(ids), 3)
            self.assertEqual(len(ids), len(set(ids)))
            self.assertIn("npm-test-unit", ids)
            self.assertEqual(sum(item.startswith("npm-test-unit-") for item in ids), 2)

    def test_conventional_gate_is_bound_to_manifest_contents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            manifest = repo / "pyproject.toml"
            manifest.write_text("[project]\nname = 'fixture'\n", encoding="utf-8")
            profile = adc.probe_repo(repo, max_files=1000, content_scan_limit=1000)
            gate = next(item for item in profile["exact_commands"] if item["id"] == "python-pytest")
            self.assertEqual(gate["source_files"], ["pyproject.toml"])
            self.assertEqual(adc.verify_gate_source(repo, gate), (True, None))
            unbound = dict(gate)
            unbound.pop("source_files")
            unbound.pop("source_definition_sha256")
            source_ok, reason = adc.verify_gate_source(repo, unbound)
            self.assertFalse(source_ok)
            self.assertIn("lacks a source-file binding", reason or "")
            manifest.write_text("[project]\nname = 'changed'\n", encoding="utf-8")
            source_ok, reason = adc.verify_gate_source(repo, gate)
            self.assertFalse(source_ok)
            self.assertIn("changed after approval", reason or "")

    def test_plan_write_refreshes_a_stale_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "app.py").write_text("value = 1\n", encoding="utf-8")
            self.init_git_repo(repo)
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            self.bind_calibration(repo, cal)
            stale = adc.probe_repo(repo, max_files=1000, content_scan_limit=1000)
            stale["source_identity"]["git_commit"] = "0" * 40
            stale["repo_types"] = ["stale-marker"]
            (cal / "repo-profile.json").write_text(json.dumps(stale), encoding="utf-8")
            args = argparse.Namespace(repo=str(repo), write=True, json=False, no_gate_suggestions=True)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(adc.command_plan(args), 0)
            refreshed = json.loads((cal / "repo-profile.json").read_text(encoding="utf-8"))
            self.assertNotEqual(refreshed["repo_types"], ["stale-marker"])
            self.assertEqual(
                refreshed["source_identity"]["git_commit"],
                adc.current_source_identity(repo)["git_commit"],
            )

    def test_gate_runner_refuses_unconfirmed_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            cal.mkdir(parents=True)
            self.bind_calibration(repo, cal)
            (cal / "gates.json").write_text(json.dumps({
                "schema_version": 1,
                "execution_policy": {"owner_confirmed_safe_to_execute": False},
                "gates": [{
                    "id": "must-not-run",
                    "level": 0,
                    "argv": [sys.executable, "-c", "raise SystemExit(99)"],
                    "enabled": True,
                    "review_status": "approved",
                    "cwd": ".",
                    "timeout_seconds": 30
                }]
            }), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = adc.run_gates(repo, 0, allow_exec=True, changed_from=None, keep_going=False)
            self.assertEqual(result, 2)
            self.assertIn("REFUSED", output.getvalue())
            self.assertFalse((repo / ".anti-dark-code" / "runs").exists())

    def make_skill_repo(self, root: Path, version: str, changelog_body: str) -> Path:
        """A minimal release repository: a distributable core plus a root CHANGELOG."""
        root.mkdir(parents=True, exist_ok=True)
        core = self.copy_clean_skill(root)
        (core / "VERSION").write_text(f"{version}\n", encoding="utf-8")
        (root / "CHANGELOG.md").write_text(changelog_body, encoding="utf-8")
        self.init_git_repo(root)
        return core

    def test_source_provenance_classifies_tag_untagged_dirty_and_non_git(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            core = self.make_skill_repo(root, "1.0.0-test", "# Changelog\n\n## 1.0.0-test\n\nNotes.\n")

            untagged = adc.assess_source_provenance(core)
            self.assertEqual(untagged["kind"], "git-untagged")
            self.assertIsNone(untagged["tag"])
            self.assertEqual(len(untagged["core_digest"]), 64)

            subprocess.run(["git", "-C", str(root), "tag", "v1.0.0-test"], check=True)
            tagged = adc.assess_source_provenance(core)
            self.assertEqual(tagged["kind"], "git-tag")
            self.assertEqual(tagged["tag"], "v1.0.0-test")
            self.assertEqual(tagged["core_digest"], untagged["core_digest"])

            (core / "SKILL.md").write_text("dirtied\n", encoding="utf-8")
            dirty = adc.assess_source_provenance(core)
            self.assertEqual(dirty["kind"], "git-dirty")
            self.assertTrue(dirty["dirty"])
            self.assertNotEqual(dirty["core_digest"], tagged["core_digest"])

            extract = Path(tmp) / "extract"
            extract.mkdir()
            subprocess.run(
                f"git -C {shlex.quote(str(root))} archive v1.0.0-test | tar -x -C {shlex.quote(str(extract))}",
                shell=True, check=True,
            )
            plain = adc.assess_source_provenance(extract / "anti-dark-code")
            self.assertEqual(plain["kind"], "non-git")
            self.assertEqual(plain["core_digest"], tagged["core_digest"])

    def test_install_refuses_an_untagged_or_dirty_source_without_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            core = self.make_skill_repo(root, "1.0.0-test", "# Changelog\n\n## 1.0.0-test\n\nNotes.\n")
            repo = Path(tmp) / "consumer"
            repo.mkdir()
            (repo / "README.md").write_text("consumer\n", encoding="utf-8")
            self.init_git_repo(repo)

            with self.assertRaises(SystemExit) as refused:
                adc.install_skill(repo, core, apply=True, force=False, hosts="none")
            self.assertIn("not at a release tag", str(refused.exception))

            plan = adc.install_skill(
                repo, core, apply=True, force=False, hosts="none", allow_untagged_source=True
            )
            self.assertFalse(plan["blocked"])
            self.assertEqual(plan["source_provenance"]["kind"], "git-untagged")

    def test_install_verifies_an_expected_core_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            core = self.make_skill_repo(root, "1.0.0-test", "# Changelog\n\n## 1.0.0-test\n\nNotes.\n")
            subprocess.run(["git", "-C", str(root), "tag", "v1.0.0-test"], check=True)
            repo = Path(tmp) / "consumer"
            repo.mkdir()
            (repo / "README.md").write_text("consumer\n", encoding="utf-8")
            self.init_git_repo(repo)
            actual = adc.assess_source_provenance(core)["core_digest"]

            with self.assertRaises(SystemExit) as refused:
                adc.install_skill(
                    repo, core, apply=True, force=False, hosts="none", expect_core_digest="0" * 64
                )
            self.assertIn("does not match the expected release digest", str(refused.exception))

            plan = adc.install_skill(
                repo, core, apply=True, force=False, hosts="none", expect_core_digest=actual
            )
            self.assertFalse(plan["blocked"])
            self.assertTrue(plan["source_provenance"]["digest_expected_match"])

    def test_release_check_requires_the_tag_to_reproduce_the_published_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            core = self.make_skill_repo(root, "1.0.0-test", "# Changelog\n\n## 1.0.0-test\n\nNotes.\n")
            subprocess.run(["git", "-C", str(root), "tag", "v1.0.0-test"], check=True)
            tagged_digest = adc.assess_source_provenance(core)["core_digest"]

            # The exact defect this gate exists for: the branch moves past the tag.
            (core / "SKILL.md").write_text("post-tag drift\n", encoding="utf-8")
            self.commit_all(root, "post-tag change to the distributed core")
            self.assertNotEqual(adc.assess_source_provenance(core)["core_digest"], tagged_digest)

            matching = adc.release_check(root, "v1.0.0-test", expect_core_digest=tagged_digest)
            self.assertTrue(matching["digest_match"])
            self.assertEqual(matching["core_digest"], tagged_digest)

            drifted = adc.release_check(
                root, "v1.0.0-test", expect_core_digest=adc.assess_source_provenance(core)["core_digest"]
            )
            self.assertFalse(drifted["digest_match"])
            self.assertFalse(drifted["ok"])

    def test_release_check_names_reference_changes_the_notes_never_describe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            core = self.make_skill_repo(root, "1.0.0-test", "# Changelog\n\n## 1.0.0-test\n\nFirst.\n")
            subprocess.run(["git", "-C", str(root), "tag", "v1.0.0-test"], check=True)

            # A silently shipped lesson: a reference changes, the notes never say so.
            reference = core / "references" / "14-deterministic-verification.md"
            reference.write_text(reference.read_text(encoding="utf-8") + "\nA new rule.\n", encoding="utf-8")
            (core / "VERSION").write_text("1.1.0-test\n", encoding="utf-8")
            (root / "CHANGELOG.md").write_text(
                "# Changelog\n\n## 1.1.0-test\n\nRoutine maintenance.\n\n## 1.0.0-test\n\nFirst.\n",
                encoding="utf-8",
            )
            self.commit_all(root, "promote a lesson without describing it")
            subprocess.run(["git", "-C", str(root), "tag", "v1.1.0-test"], check=True)

            silent = adc.release_check(root, "v1.1.0-test")
            self.assertIn("references/14-deterministic-verification.md", silent["undescribed_files"])
            self.assertFalse(silent["ok"])

            (root / "CHANGELOG.md").write_text(
                "# Changelog\n\n## 1.1.0-test\n\nAdds a rule to "
                "`references/14-deterministic-verification.md`.\n\n## 1.0.0-test\n\nFirst.\n",
                encoding="utf-8",
            )
            self.commit_all(root, "describe the promotion")
            subprocess.run(["git", "-C", str(root), "tag", "-f", "v1.1.0-test"], check=True)
            described = adc.release_check(root, "v1.1.0-test")
            self.assertEqual(described["undescribed_files"], [])
            self.assertTrue(described["ok"])

    def test_release_check_ignores_mechanical_version_churn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            core = self.make_skill_repo(root, "1.0.0-test", "# Changelog\n\n## 1.0.0-test\n\nFirst.\n")
            catalog = core / "assets" / "verification-capabilities.json"
            catalog.write_text(json.dumps({"catalog_version": "1.0.0-test"}, indent=2) + "\n", encoding="utf-8")
            self.commit_all(root, "seed catalog")
            subprocess.run(["git", "-C", str(root), "tag", "v1.0.0-test"], check=True)

            # Only the version string moves: the notes owe the reader nothing.
            catalog.write_text(json.dumps({"catalog_version": "1.1.0-test"}, indent=2) + "\n", encoding="utf-8")
            (core / "VERSION").write_text("1.1.0-test\n", encoding="utf-8")
            (root / "CHANGELOG.md").write_text(
                "# Changelog\n\n## 1.1.0-test\n\nRoutine.\n\n## 1.0.0-test\n\nFirst.\n", encoding="utf-8"
            )
            self.commit_all(root, "bump")
            subprocess.run(["git", "-C", str(root), "tag", "v1.1.0-test"], check=True)
            self.assertEqual(adc.release_check(root, "v1.1.0-test")["undescribed_files"], [])

            # A substantive change to the same file is still reported.
            catalog.write_text(
                json.dumps({"catalog_version": "1.2.0-test", "capabilities": ["new"]}, indent=2) + "\n",
                encoding="utf-8",
            )
            (core / "VERSION").write_text("1.2.0-test\n", encoding="utf-8")
            (root / "CHANGELOG.md").write_text(
                "# Changelog\n\n## 1.2.0-test\n\nRoutine.\n\n## 1.1.0-test\n\nRoutine.\n", encoding="utf-8"
            )
            self.commit_all(root, "add a capability without describing it")
            subprocess.run(["git", "-C", str(root), "tag", "v1.2.0-test"], check=True)
            self.assertIn(
                "assets/verification-capabilities.json",
                adc.release_check(root, "v1.2.0-test")["undescribed_files"],
            )

    def test_flowback_is_proposal_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            cal.mkdir(parents=True)
            self.bind_calibration(repo, cal)
            (cal / "upstream-candidates.md").write_text(
                "# Upstream Candidates\n\n"
                "## ADC-LOCAL-001: Exact gates\n\n"
                "- Status: ready\n"
                "- Scope: repo-agnostic\n"
                "- Lesson: Exact command arrays reduce rediscovery.\n"
                "- Evidence: tests/gates.test.py\n"
                "- Limits: Commands still require review.\n"
                "- Proposed target: references/14-deterministic-verification.md\n"
                "- Proposed change: Add the gate-array rule.\n",
                encoding="utf-8"
            )
            out = adc.flowback(repo, parent=None, stage_to_parent=False, mark_staged=False)
            self.assertTrue(out.exists())
            proposal_text = out.read_text(encoding="utf-8")
            self.assertIn("Exact command arrays", proposal_text)
            self.assertEqual(proposal_text.count("## ADC-LOCAL-001: Exact gates"), 1)
            self.assertFalse((repo / "SKILL.md").exists())

    def test_parse_candidates_preserves_wrapped_field_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "upstream-candidates.md"
            path.write_text(
                "# Upstream Candidates\n\n"
                "## ADC-LOCAL-001: Wrapped lesson survives staging\n\n"
                "- Status: ready\n"
                "- Scope: repo-agnostic\n"
                "- Lesson: A revert-mutation proof restores the code by checkout, and\n"
                "  an uncommitted unit is silently destroyed when the checkout runs,\n"
                "  so the proof must start from a committed baseline.\n"
                "- Evidence: three proofs on one module, each recorded\n"
                "  with its closing green run.\n"
                "- Limits: one incident.\n"
                "- Proposed target: references/11-remediation-loop.md\n"
                "- Proposed change: require a committed baseline\n"
                "  before any revert-mutation proof.\n\n"
                "Valid statuses: `observing`, `ready`, `staged`, `promoted`, `rejected`.\n",
                encoding="utf-8"
            )
            candidate = adc.parse_candidates(path)[0]
            self.assertIn("committed baseline", candidate["lesson"])
            self.assertIn("silently destroyed", candidate["lesson"])
            self.assertIn("closing green run", candidate["evidence"])
            self.assertIn("before any revert-mutation proof", candidate["proposed_change"])
            self.assertNotIn("Valid statuses", candidate["proposed_change"])
            self.assertNotIn("\n", candidate["lesson"])

    def test_binding_mismatch_detail_names_failed_component(self) -> None:
        assessment = {
            "binding": {
                "identity_components": {
                    "origin_sha256": "aaa",
                    "root_commits_sha256": "rrr"
                }
            },
            "current": {
                "identity_components": {
                    "origin_sha256": "bbb",
                    "root_commits_sha256": "rrr"
                }
            }
        }
        detail = adc.binding_mismatch_detail(assessment)
        self.assertIn("remote identity: differ", detail)
        self.assertIn("root commits: match", detail)
        self.assertIn("move, fork, or rename", detail)
        assessment["current"]["identity_components"]["root_commits_sha256"] = "zzz"
        detail = adc.binding_mismatch_detail(assessment)
        self.assertIn("root commits: differ", detail)
        self.assertNotIn("move, fork, or rename", detail)

    def test_pnpm_runner_and_plain_export_does_not_signal_generated_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "package.json").write_text(json.dumps({
                "name": "pnpm-fixture",
                "packageManager": "pnpm@10.0.0",
                "scripts": {"lint": "eslint src"}
            }), encoding="utf-8")
            (repo / "src" / "value.ts").write_text("export const value = 1;\n", encoding="utf-8")
            profile = adc.probe_repo(repo, max_files=1000, content_scan_limit=1000)
            self.assertEqual(profile["exact_commands"][0]["argv"], ["pnpm", "run", "lint"])
            self.assertEqual(profile["exact_commands"][0]["id"], "pnpm-lint")
            self.assertFalse(profile["signals"]["generated_or_serialized_output"]["present"])

    def test_gate_suggestions_require_approval_and_script_changes_invalidate_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.make_node_repo(repo)
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            self.bind_calibration(repo, cal)
            profile = adc.probe_repo(repo, max_files=1000, content_scan_limit=1000)
            gate_path, changed = adc.merge_gate_suggestions(repo, profile)
            self.assertGreater(changed, 0)
            config = json.loads(gate_path.read_text(encoding="utf-8"))
            self.assertFalse(config["execution_policy"]["owner_confirmed_safe_to_execute"])
            self.assertTrue(all(not gate["enabled"] for gate in config["gates"]))
            self.assertTrue(all(gate["review_status"] == "proposed" for gate in config["gates"]))

            lint_gate = next(gate for gate in config["gates"] if gate["id"] == "npm-lint")
            lint_gate["enabled"] = True
            lint_gate["review_status"] = "approved"
            config["execution_policy"]["owner_confirmed_safe_to_execute"] = True
            gate_path.write_text(json.dumps(config), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(adc.run_gates(repo, 0, allow_exec=False, changed_from=None, keep_going=False), 0)

            package = json.loads((repo / "package.json").read_text(encoding="utf-8"))
            package["scripts"]["lint"] = "eslint src --max-warnings=0"
            (repo / "package.json").write_text(json.dumps(package), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(adc.run_gates(repo, 0, allow_exec=True, changed_from=None, keep_going=False), 2)
            self.assertIn("source package script changed", output.getvalue())

            profile2 = adc.probe_repo(repo, max_files=1000, content_scan_limit=1000)
            _, changed2 = adc.merge_gate_suggestions(repo, profile2)
            self.assertGreater(changed2, 0)
            config2 = json.loads(gate_path.read_text(encoding="utf-8"))
            lint_gate2 = next(gate for gate in config2["gates"] if gate["id"] == "npm-lint")
            self.assertFalse(lint_gate2["enabled"])
            self.assertEqual(lint_gate2["review_status"], "proposed")
            self.assertFalse(config2["execution_policy"]["owner_confirmed_safe_to_execute"])

    def test_repo_owned_source_bound_gate_survives_profile_refresh_until_sources_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_file = repo / "eng" / "verify.ps1"
            source_file.parent.mkdir(parents=True)
            source_file.write_text("Write-Output 'verified'\n", encoding="utf-8")
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            self.bind_calibration(repo, cal)
            gate_path = cal / "gates.json"
            gate_path.write_text(json.dumps({
                "schema_version": 1,
                "execution_policy": {
                    "owner_confirmed_safe_to_execute": True,
                    "notes": "Reviewed repo-owned gate.",
                },
                "gates": [{
                    "id": "repo-contract",
                    "level": 0,
                    "argv": ["pwsh", "-NoProfile", "-File", "eng/verify.ps1"],
                    "enabled": True,
                    "review_status": "approved",
                    "source": "reviewed repo-specific verification contract",
                    "source_definition_sha256": adc.source_set_hash(repo, ["eng/verify.ps1"]),
                    "source_files": ["eng/verify.ps1"],
                    "timeout_seconds": 30,
                    "cwd": ".",
                }],
            }), encoding="utf-8")

            profile = adc.probe_repo(repo, max_files=1000, content_scan_limit=1000)
            _, unchanged = adc.merge_gate_suggestions(repo, profile)
            self.assertEqual(unchanged, 0)
            preserved = json.loads(gate_path.read_text(encoding="utf-8"))
            self.assertTrue(preserved["execution_policy"]["owner_confirmed_safe_to_execute"])
            self.assertTrue(preserved["gates"][0]["enabled"])
            self.assertEqual(preserved["gates"][0]["review_status"], "approved")

            source_file.write_text("Write-Output 'changed'\n", encoding="utf-8")
            _, changed = adc.merge_gate_suggestions(repo, profile)
            self.assertEqual(changed, 1)
            invalidated = json.loads(gate_path.read_text(encoding="utf-8"))
            self.assertFalse(invalidated["execution_policy"]["owner_confirmed_safe_to_execute"])
            self.assertFalse(invalidated["gates"][0]["enabled"])
            self.assertEqual(invalidated["gates"][0]["review_status"], "stale")
            self.assertIn("source binding no longer verifies", invalidated["gates"][0]["notes"])

    def test_disappeared_auto_discovered_gate_is_still_invalidated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            manifest = repo / "pyproject.toml"
            manifest.write_text("[project]\nname = 'fixture'\n", encoding="utf-8")
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            self.bind_calibration(repo, cal)

            profile = adc.probe_repo(repo, max_files=1000, content_scan_limit=1000)
            gate_path, _ = adc.merge_gate_suggestions(repo, profile)
            config = json.loads(gate_path.read_text(encoding="utf-8"))
            gate = next(item for item in config["gates"] if item["id"] == "python-pytest")
            gate["enabled"] = True
            gate["review_status"] = "approved"
            config["execution_policy"]["owner_confirmed_safe_to_execute"] = True
            gate_path.write_text(json.dumps(config), encoding="utf-8")

            # A bounded probe may omit a still-present gate. Its exact source
            # binding is stronger evidence than absence from the bounded scan.
            _, omitted_but_valid = adc.merge_gate_suggestions(repo, {"exact_commands": []})
            self.assertEqual(omitted_but_valid, 0)
            preserved = json.loads(gate_path.read_text(encoding="utf-8"))
            preserved_gate = next(item for item in preserved["gates"] if item["id"] == "python-pytest")
            self.assertTrue(preserved_gate["enabled"])
            self.assertEqual(preserved_gate["review_status"], "approved")

            manifest.unlink()
            refreshed = adc.probe_repo(repo, max_files=1000, content_scan_limit=1000)
            _, changed = adc.merge_gate_suggestions(repo, refreshed)
            self.assertEqual(changed, 1)
            invalidated = json.loads(gate_path.read_text(encoding="utf-8"))
            stale_gate = next(item for item in invalidated["gates"] if item["id"] == "python-pytest")
            self.assertFalse(stale_gate["enabled"])
            self.assertEqual(stale_gate["review_status"], "stale")
            self.assertFalse(invalidated["execution_policy"]["owner_confirmed_safe_to_execute"])

    def test_package_runner_switch_retires_superseded_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.make_node_repo(repo)
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            self.bind_calibration(repo, cal)
            profile = adc.probe_repo(repo, max_files=1000, content_scan_limit=1000)
            gate_path, _ = adc.merge_gate_suggestions(repo, profile)
            config = json.loads(gate_path.read_text(encoding="utf-8"))
            old_gate = next(item for item in config["gates"] if item["id"] == "npm-lint")
            old_gate["enabled"] = True
            old_gate["review_status"] = "approved"
            config["execution_policy"]["owner_confirmed_safe_to_execute"] = True
            gate_path.write_text(json.dumps(config), encoding="utf-8")

            package = json.loads((repo / "package.json").read_text(encoding="utf-8"))
            package["packageManager"] = "pnpm@10.0.0"
            (repo / "package.json").write_text(json.dumps(package), encoding="utf-8")
            refreshed = adc.probe_repo(repo, max_files=1000, content_scan_limit=1000)
            details: list[dict[str, str]] = []
            _, changed = adc.merge_gate_suggestions(repo, refreshed, change_details=details)

            self.assertGreaterEqual(changed, 2)
            updated = json.loads(gate_path.read_text(encoding="utf-8"))
            retired = next(item for item in updated["gates"] if item["id"] == "npm-lint")
            replacement = next(item for item in updated["gates"] if item["id"] == "pnpm-lint")
            self.assertFalse(retired["enabled"])
            self.assertEqual(retired["review_status"], "stale")
            self.assertIn("superseded by current gate pnpm-lint", retired["notes"])
            self.assertFalse(replacement["enabled"])
            self.assertEqual(replacement["review_status"], "proposed")
            self.assertTrue(any(item["gate_id"] == "npm-lint" for item in details))
            self.assertFalse(updated["execution_policy"]["owner_confirmed_safe_to_execute"])

    def test_absent_bound_proposed_gate_is_disabled_even_when_source_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_file = repo / "eng" / "verify.ps1"
            source_file.parent.mkdir(parents=True)
            source_file.write_text("Write-Output 'verified'\n", encoding="utf-8")
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            self.bind_calibration(repo, cal)
            gate_path = cal / "gates.json"
            gate_path.write_text(json.dumps({
                "schema_version": 1,
                "execution_policy": {"owner_confirmed_safe_to_execute": True},
                "gates": [{
                    "id": "repo-contract",
                    "level": 0,
                    "argv": ["pwsh", "-File", "eng/verify.ps1"],
                    "enabled": True,
                    "review_status": "proposed",
                    "source": "reviewed repo-specific verification contract",
                    "source_definition_sha256": adc.source_set_hash(repo, ["eng/verify.ps1"]),
                    "source_files": ["eng/verify.ps1"],
                    "timeout_seconds": 30,
                    "cwd": ".",
                }],
            }), encoding="utf-8")

            _, changed = adc.merge_gate_suggestions(repo, {"exact_commands": []})

            self.assertEqual(changed, 1)
            updated = json.loads(gate_path.read_text(encoding="utf-8"))
            self.assertFalse(updated["gates"][0]["enabled"])
            self.assertEqual(updated["gates"][0]["review_status"], "proposed")
            self.assertFalse(updated["execution_policy"]["owner_confirmed_safe_to_execute"])

    def test_gate_source_bindings_refuse_linked_parent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            real = repo / "real"
            real.mkdir()
            (real / "verify.ps1").write_text("Write-Output 'verified'\n", encoding="utf-8")
            command = "pytest -q"
            (real / "package.json").write_text(
                json.dumps({"scripts": {"test": command}}),
                encoding="utf-8",
            )
            linked = repo / "linked"
            try:
                linked.symlink_to(real, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"directory symlink creation unavailable: {exc}")

            with self.assertRaisesRegex(ValueError, "link-like component"):
                adc.source_set_hash(repo, ["linked/verify.ps1"])
            source_ok, reason = adc.verify_gate_source(repo, {
                "source": "linked/package.json#scripts.test",
                "source_definition_sha256": adc.sha256_bytes(command.encode("utf-8")),
            })
            self.assertFalse(source_ok)
            self.assertIn("link-like component", reason or "")

    def test_duplicate_gate_ids_are_rejected_before_merge_migration_or_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            self.bind_calibration(repo, cal)
            gate_path = cal / "gates.json"
            gate = {
                "id": "duplicate",
                "level": 0,
                "argv": ["tool", "--check"],
                "enabled": True,
                "review_status": "approved",
                "source": "reviewed repo contract",
                "timeout_seconds": 30,
                "cwd": ".",
            }
            gate_path.write_text(json.dumps({
                "schema_version": 1,
                "execution_policy": {"owner_confirmed_safe_to_execute": True},
                "gates": [gate, dict(gate)],
            }), encoding="utf-8")

            inspection = adc.inspect_gate_config_for_migration(gate_path)
            self.assertFalse(inspection["valid"])
            self.assertIn("duplicate ids", inspection["error"] or "")
            with self.assertRaisesRegex(SystemExit, "duplicate ids"):
                adc.merge_gate_suggestions(repo, {"exact_commands": []})
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = adc.run_gates(repo, level=0, allow_exec=False, changed_from=None, keep_going=False)
            self.assertEqual(result, 2)
            self.assertIn("duplicate gate ids", output.getvalue())

    def test_gate_preview_reports_changes_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_file = repo / "eng" / "verify.ps1"
            source_file.parent.mkdir(parents=True)
            source_file.write_text("Write-Output 'current'\n", encoding="utf-8")
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            self.bind_calibration(repo, cal)
            gate_path = cal / "gates.json"
            gate_path.write_text(json.dumps({
                "schema_version": 1,
                "execution_policy": {"owner_confirmed_safe_to_execute": True},
                "gates": [{
                    "id": "repo-contract",
                    "level": 0,
                    "argv": ["pwsh", "-File", "eng/verify.ps1"],
                    "enabled": True,
                    "review_status": "approved",
                    "source": "reviewed repo-specific verification contract",
                    "source_definition_sha256": "0" * 64,
                    "source_files": ["eng/verify.ps1"],
                    "timeout_seconds": 30,
                    "cwd": ".",
                }],
            }), encoding="utf-8")
            before = gate_path.read_bytes()
            profile = adc.probe_repo(repo, max_files=1000, content_scan_limit=1000)

            preview_path, changes = adc.merge_gate_suggestions(repo, profile, write=False)

            self.assertEqual(preview_path, gate_path)
            self.assertEqual(changes, 1)
            self.assertEqual(gate_path.read_bytes(), before)

    def test_bootstrap_dry_run_surfaces_gate_reset_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = self.copy_clean_skill(base / "source")
            repo = base / "repo"
            repo.mkdir()
            adc.install_skill(repo, source, apply=True, force=False, hosts="none")
            source_file = repo / "eng" / "verify.ps1"
            source_file.parent.mkdir(parents=True)
            source_file.write_text("Write-Output 'current'\n", encoding="utf-8")
            gate_path = repo / ".agents" / "skills" / "anti-dark-code" / "calibration" / "gates.json"
            gate_path.write_text(json.dumps({
                "schema_version": 1,
                "execution_policy": {"owner_confirmed_safe_to_execute": True},
                "gates": [{
                    "id": "repo-contract",
                    "level": 0,
                    "argv": ["pwsh", "-File", "eng/verify.ps1"],
                    "enabled": True,
                    "review_status": "approved",
                    "source": "reviewed repo-specific verification contract",
                    "source_definition_sha256": "0" * 64,
                    "source_files": ["eng/verify.ps1"],
                    "timeout_seconds": 30,
                    "cwd": ".",
                }],
            }), encoding="utf-8")
            before = gate_path.read_bytes()
            args = argparse.Namespace(
                repo=str(repo),
                source_skill=str(source),
                apply=False,
                force=False,
                hosts="none",
                allow_unsafe_source=False,
                accept_unbound_calibration=False,
                rebind_calibration=False,
                max_files=1000,
                content_scan_limit=1000,
            )
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                self.assertEqual(adc.command_bootstrap(args), 0)

            report = output.getvalue()
            self.assertIn('"gate_change_count": 1', report)
            self.assertIn('"owner_confirmation_will_reset": true', report)
            self.assertIn('"writes_performed": false', report)
            self.assertIn('"gate_id": "repo-contract"', report)
            self.assertIn('"action": "marked_stale"', report)
            self.assertEqual(gate_path.read_bytes(), before)

    def test_fresh_bootstrap_previews_canonical_template_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = self.copy_clean_skill(base / "source")
            repo = base / "repo"
            repo.mkdir()
            args = argparse.Namespace(
                repo=str(repo), source_skill=str(source), apply=False, force=False,
                hosts="none", allow_unsafe_source=False, accept_unbound_calibration=False,
                rebind_calibration=False, max_files=1000, content_scan_limit=1000,
            )
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                self.assertEqual(adc.command_bootstrap(args), 0)

            report = output.getvalue()
            self.assertIn('"gate_config": ".agents/skills/anti-dark-code/calibration/gates.json"', report)
            self.assertIn('"baseline": "source-template"', report)
            self.assertIn('"migration_approval_reset_required": false', report)
            self.assertFalse((repo / ".agents").exists())
            self.assertFalse((repo / ".anti-dark-code").exists())

    def test_fallback_bootstrap_preview_models_migration_reset_before_merge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = self.copy_clean_skill(base / "source")
            repo = base / "repo"
            repo.mkdir()
            fallback = repo / ".anti-dark-code" / "calibration"
            fallback.mkdir(parents=True)
            gates_path = fallback / "gates.json"
            gates_path.write_text(json.dumps({
                "schema_version": 1,
                "execution_policy": {"owner_confirmed_safe_to_execute": True},
                "gates": [{
                    "id": "legacy-contract",
                    "level": 0,
                    "argv": ["tool", "--check"],
                    "enabled": True,
                    "review_status": "approved",
                    "source": "reviewed legacy contract",
                    "timeout_seconds": 30,
                    "cwd": ".",
                }],
            }), encoding="utf-8")
            before = gates_path.read_bytes()
            args = argparse.Namespace(
                repo=str(repo), source_skill=str(source), apply=False, force=False,
                hosts="none", allow_unsafe_source=False, accept_unbound_calibration=True,
                rebind_calibration=False, max_files=1000, content_scan_limit=1000,
            )
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                self.assertEqual(adc.command_bootstrap(args), 0)

            report = output.getvalue()
            self.assertIn('"baseline": "migrated-fallback"', report)
            self.assertIn('"migration_approval_reset_required": true', report)
            self.assertIn('"migration_reset_gate_count": 1', report)
            self.assertIn('"owner_confirmation_will_reset": true', report)
            self.assertEqual(gates_path.read_bytes(), before)
            self.assertFalse((repo / ".agents").exists())

    def test_managed_subtree_keeps_lf_and_valid_digest_with_autocrlf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            clean_source = self.copy_clean_skill(base / "clean-source")
            source_repo = base / "source-repo"
            source_repo.mkdir()
            subprocess.run(["git", "init", "-q", str(source_repo)], check=True)
            subprocess.run(["git", "-C", str(source_repo), "config", "user.email", "tests@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(source_repo), "config", "user.name", "Anti Dark Code Tests"], check=True)
            subprocess.run(["git", "-C", str(source_repo), "config", "core.autocrlf", "true"], check=True)
            subprocess.run([
                "git", "-C", str(source_repo), "remote", "add", "origin",
                "https://example.invalid/managed-install.git",
            ], check=True)
            adc.install_skill(source_repo, clean_source, apply=True, force=False, hosts="none")
            self.commit_all(source_repo, "install managed skill")

            checkout = base / "checkout"
            checkout.mkdir()
            subprocess.run(["git", "init", "-q", str(checkout)], check=True)
            subprocess.run(["git", "-C", str(checkout), "config", "core.autocrlf", "true"], check=True)
            subprocess.run(["git", "-C", str(checkout), "remote", "add", "source", str(source_repo)], check=True)
            subprocess.run(["git", "-C", str(checkout), "fetch", "-q", "source", "HEAD"], check=True)
            subprocess.run(["git", "-C", str(checkout), "checkout", "-q", "-f", "FETCH_HEAD"], check=True)
            subprocess.run([
                "git", "-C", str(checkout), "remote", "add", "origin",
                "https://example.invalid/managed-install.git",
            ], check=True)

            installed = checkout / ".agents" / "skills" / "anti-dark-code"
            script_bytes = (installed / "scripts" / "adc.py").read_bytes()
            self.assertIn(b"\n", script_bytes)
            self.assertNotIn(b"\r\n", script_bytes)
            errors, warnings = adc.validate_skill(installed, mode="installed")
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_changed_files_includes_worktree_and_untracked_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "tracked.txt").write_text("one\n", encoding="utf-8")
            self.init_git_repo(repo)
            (repo / "tracked.txt").write_text("two\n", encoding="utf-8")
            (repo / "untracked.txt").write_text("new\n", encoding="utf-8")
            internal = repo / ".agents" / "skills" / "anti-dark-code"
            internal.mkdir(parents=True)
            (internal / "SKILL.md").write_text("internal\n", encoding="utf-8")
            changed = adc.changed_files(repo, "HEAD")
            self.assertEqual(changed, ["tracked.txt", "untracked.txt"])

    def test_profile_freshness_detects_worktree_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "app.py").write_text("value = 1\n", encoding="utf-8")
            self.init_git_repo(repo)
            profile = adc.probe_repo(repo, max_files=1000, content_scan_limit=1000)
            self.assertTrue(adc.profile_is_fresh(repo, profile))
            (repo / "app.py").write_text("value = 2\n", encoding="utf-8")
            self.assertFalse(adc.profile_is_fresh(repo, profile))

    def test_profile_identity_ignores_anti_dark_code_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "app.py").write_text("value = 1\n", encoding="utf-8")
            self.init_git_repo(repo)
            profile = adc.probe_repo(repo, max_files=1000, content_scan_limit=1000)
            for internal in (
                repo / ".agents" / "skills" / "anti-dark-code" / "calibration",
                repo / ".claude" / "skills" / "other-skill",
                repo / ".gemini" / "skills" / "other-skill",
                repo / ".codex" / "skills" / "other-skill",
            ):
                internal.mkdir(parents=True)
                (internal / "runtime-artifact.json").write_text("{}\n", encoding="utf-8")
            self.assertTrue(adc.profile_is_fresh(repo, profile))

    def test_installer_migrates_fallback_calibration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            repo.mkdir()
            fallback = repo / ".anti-dark-code" / "calibration"
            fallback.mkdir(parents=True)
            (fallback / "invariants.md").write_text("# Existing local truth\n", encoding="utf-8")
            (fallback / "gates.json").write_text(json.dumps({
                "schema_version": 1,
                "execution_policy": {"owner_confirmed_safe_to_execute": True},
                "gates": [{
                    "id": "legacy-approved",
                    "level": 0,
                    "argv": [sys.executable, "-c", "print('legacy')"],
                    "enabled": True,
                    "review_status": "approved",
                    "cwd": ".",
                    "timeout_seconds": 30,
                }],
            }), encoding="utf-8")
            source = self.copy_clean_skill(base / "source")
            result = adc.install_skill(
                repo,
                source,
                apply=True,
                force=False,
                hosts="none",
                accept_unbound_calibration=True,
            )
            target_calibration = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            target = target_calibration / "invariants.md"
            self.assertIn("calibration/invariants.md", result["calibration_migrated"])
            self.assertEqual(target.read_text(encoding="utf-8"), "# Existing local truth\n")
            migrated_gates = json.loads((target_calibration / "gates.json").read_text(encoding="utf-8"))
            self.assertFalse(migrated_gates["execution_policy"]["owner_confirmed_safe_to_execute"])
            self.assertFalse(migrated_gates["gates"][0]["enabled"])
            self.assertEqual(migrated_gates["gates"][0]["review_status"], "proposed")
            self.assertTrue(result["migrated_gate_approvals"]["reset"])

    def test_flowback_redacts_repo_paths_and_secret_like_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            cal.mkdir(parents=True)
            self.bind_calibration(repo, cal)
            (cal / "upstream-candidates.md").write_text(
                "# Upstream Candidates\n\n"
                "## ADC-LOCAL-002: Redacted lesson\n\n"
                "- Status: ready\n"
                "- Scope: repo-agnostic\n"
                f"- Lesson: Keep evidence in {repo}; password=hunter2\n"
                "- Evidence: local test\n"
                "- Limits: none\n"
                "- Proposed target: references/14-deterministic-verification.md\n"
                "- Proposed change: Add token=abc123 to an example only after redaction.\n",
                encoding="utf-8"
            )
            out = adc.flowback(repo, parent=None, stage_to_parent=False, mark_staged=False)
            text = out.read_text(encoding="utf-8")
            self.assertIn("<repo>", text)
            self.assertNotIn("hunter2", text)
            self.assertNotIn("abc123", text)
            self.assertIn("<redacted>", text)

    def test_public_flowback_validates_and_withholds_source_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_name = "Chron" + "icle Engine"
            repo = Path(tmp) / project_name
            repo.mkdir()
            (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
            self.init_git_repo(repo)
            head = adc.git_output(repo, ["rev-parse", "HEAD"])
            self.assertIsNotNone(head)

            calibration = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            self.bind_calibration(repo, calibration)
            slash_variant = str(repo).replace("\\", "/").upper()
            (calibration / "upstream-candidates.md").write_text(
                "# Upstream Candidates\n\n"
                "## ADC-CHRONICLE-900: " + project_name + " proposal boundary\n\n"
                "- Status: ready\n"
                "- Scope: repo-agnostic\n"
                f"- Lesson: Replace {project_name} and private roots such as {slash_variant}; password=hunter2\n"
                f"- Evidence: {project_name} deterministic local fixture\n"
                "- Limits: human review remains required\n"
                "- Proposed target: references/15-dogfeeding-flowback.md\n"
                "- Proposed change: Document the public proposal boundary.\n",
                encoding="utf-8",
            )

            out = adc.flowback(
                repo,
                parent=None,
                stage_to_parent=False,
                mark_staged=False,
                public=True,
            )
            text = out.read_text(encoding="utf-8")
            self.assertEqual(adc.validate_flowback_proposal(out, public_only=True), [])
            self.assertIn("Submission mode: `public`", text)
            self.assertIn("Source repo identity: withheld", text)
            self.assertNotIn(str(head), text)
            self.assertNotIn(str(repo).lower(), text.lower())
            self.assertNotIn(project_name.lower(), text.lower())
            self.assertNotIn(("chron" + "icle").lower(), text.lower())
            self.assertNotIn("hunter2", text)
            self.assertIn("<repo>", text)
            self.assertIn("## ADC-LOCAL-001: <project> proposal boundary", text)
            self.assertNotIn("ADC-LOCAL-900", text)
            self.assertIn("<redacted>", text)
            self.assertIn(
                "flowback/",
                (repo / ".anti-dark-code" / ".gitignore").read_text(encoding="utf-8").splitlines(),
            )

    def test_efficiency_wrapper_help_hides_injected_identity_arguments(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as raised:
            adc.main(["efficiency", "record", "--help"])
        self.assertEqual(raised.exception.code, 0)
        help_text = output.getvalue()
        self.assertIn("--provider", help_text)
        self.assertNotIn("--skill-version", help_text)
        self.assertNotIn("--core-sha256", help_text)

    def test_shared_inbox_staging_requires_public_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "source"
            repo.mkdir()
            with self.assertRaisesRegex(SystemExit, "requires --public"):
                adc.flowback(
                    repo,
                    parent=Path(tmp) / "parent",
                    stage_to_parent=True,
                    mark_staged=False,
                )

    def test_proposal_filename_hash_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_hashed_proposal(Path(tmp), self.public_proposal_text())
            self.assertEqual(adc.validate_flowback_proposal(path, public_only=True), [])
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "Bounded public lesson", "Tampered public lesson"
                ),
                encoding="utf-8",
                newline="\n",
            )
            errors = adc.validate_flowback_proposal(path, public_only=True)
            self.assertTrue(any("SHA-256 content identity" in item for item in errors))

    def test_proposal_requires_unique_candidates_and_exact_fields(self) -> None:
        valid = self.public_proposal_text()
        missing = valid.replace("- Lesson: Validate proposal files as untrusted data.\n", "")
        duplicate = valid.replace(
            "- Lesson: Validate proposal files as untrusted data.\n",
            "- Lesson: Validate proposal files as untrusted data.\n"
            "- Lesson: A second value must not override the first.\n",
        )
        duplicate_id = self.public_proposal_text([
            self.public_candidate_block(),
            self.public_candidate_block(title="Second candidate with the same id"),
        ])
        extra_body_line = valid.replace(
            "- Evidence: A deterministic fixture reproduced the failure.\n",
            "Unstructured text must not bypass field validation.\n"
            "- Evidence: A deterministic fixture reproduced the failure.\n",
        )
        missing_public_marker = valid.replace("Submission mode: `public`\n", "")
        cases = (
            ("missing field", missing, "exactly one nonempty Lesson field"),
            ("duplicate field", duplicate, "exactly one nonempty Lesson field"),
            ("duplicate id", duplicate_id, "repeats candidate id ADC-LOCAL-900"),
            ("extra body line", extra_body_line, "canonical generated order and labels"),
            ("missing public marker", missing_public_marker, "public submission marker is missing"),
        )
        for name, text, expected in cases:
            with self.subTest(name=name):
                data = text.encode("utf-8")
                filename = f"flowback-{adc.sha256_bytes(data)[:12]}.md"
                errors = adc.validate_flowback_proposal_bytes(data, filename, public_only=True)
                self.assertTrue(any(expected in item for item in errors), errors)

    def test_public_proposal_rejects_sensitive_or_active_content(self) -> None:
        cases = (
            ("secret", "token=abc123", "unredacted credential-like value"),
            ("windows path", "C:" + "\\Users\\alice\\private", "likely personal or absolute path"),
            ("posix path", "/" + "home/alice/private", "likely personal or absolute path"),
            ("active html", "<script>alert(1)</script>", "raw HTML markup"),
            ("arbitrary html", "<svg onload=alert(1)></svg>", "raw HTML markup"),
            ("html comment", "<!-- hidden -->", "raw HTML markup"),
            ("html declaration", "<!DOCTYPE html>", "raw HTML markup"),
            ("processing instruction", "<?xml version='1.0'?>", "raw HTML markup"),
            ("image", "![tracking](https://example.invalid/pixel.png)", "Markdown image embed"),
            ("unsafe scheme", "javascript:alert(1)", "disallowed URI scheme"),
            ("credential url", "https://alice:secret@example.invalid/evidence", "credential-bearing URL"),
            ("abbreviated commit", "abcdef1", "raw commit-like identifier"),
            ("raw commit", "a" * 40, "raw commit-like identifier"),
            ("control", "unsafe\x07content", "control or invisible formatting character"),
            ("bidi", "unsafe\u202econtent", "control or invisible formatting character"),
            ("nul", "unsafe\x00content", "NUL byte"),
        )
        for name, lesson, expected in cases:
            with self.subTest(name=name):
                text = self.public_proposal_text([
                    self.public_candidate_block(lesson=lesson),
                ])
                data = text.encode("utf-8")
                filename = f"flowback-{adc.sha256_bytes(data)[:12]}.md"
                errors = adc.validate_flowback_proposal_bytes(data, filename, public_only=True)
                self.assertTrue(any(expected in item for item in errors), errors)
                self.assertNotIn("abc123", "\n".join(errors))
                self.assertNotIn("alice", "\n".join(errors))

        crlf = self.public_proposal_text().replace("\n", "\r\n").encode("utf-8")
        crlf_name = f"flowback-{adc.sha256_bytes(crlf)[:12]}.md"
        errors = adc.validate_flowback_proposal_bytes(crlf, crlf_name, public_only=True)
        self.assertTrue(any("canonical LF newlines" in item for item in errors), errors)

    def test_proposal_diagnostics_escape_untrusted_ids_and_filenames(self) -> None:
        unsafe_id = "ADC-LOCAL-\x1b[31m"
        text = self.public_proposal_text([
            self.public_candidate_block(candidate_id=unsafe_id, title="Bad id"),
        ])
        data = text.encode("utf-8")
        filename = f"flowback-{adc.sha256_bytes(data)[:12]}.md"
        direct_errors = adc.validate_flowback_proposal_bytes(data, filename, public_only=True)
        self.assertNotIn("\x1b", "\n".join(direct_errors))

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            skill = repo / "anti-dark-code"
            incoming = skill / "incoming"
            incoming.mkdir(parents=True)
            unsafe_file = incoming / "flowback-\x1b[31m.md"
            errors, _ = adc.validate_incoming(
                repo,
                skill,
                changed_from=None,
                proposal_only=False,
                public_only=True,
                explicit_files=[unsafe_file],
            )
            diagnostics = "\n".join(errors)
            self.assertNotIn("\x1b", diagnostics)
            self.assertIn("\\u001b", diagnostics)

    def test_proposal_enforces_bounded_sizes(self) -> None:
        cases: list[tuple[str, str, str]] = []
        cases.append((
            "bytes",
            self.public_proposal_text() + ("x" * adc.FLOWBACK_MAX_BYTES),
            f"exceeds {adc.FLOWBACK_MAX_BYTES} bytes",
        ))
        cases.append((
            "lines",
            self.public_proposal_text() + ("\n" * (adc.FLOWBACK_MAX_LINES + 1)),
            f"exceeds {adc.FLOWBACK_MAX_LINES} lines",
        ))
        long_field = "x" * (adc.FLOWBACK_MAX_FIELD_CHARS + 1)
        cases.append((
            "field",
            self.public_proposal_text([self.public_candidate_block(lesson=long_field)]),
            f"field Lesson exceeds {adc.FLOWBACK_MAX_FIELD_CHARS} characters",
        ))
        many_candidates = [
            self.public_candidate_block(candidate_id=f"ADC-LOCAL-{index:03d}")
            for index in range(adc.FLOWBACK_MAX_CANDIDATES + 1)
        ]
        cases.append((
            "candidates",
            self.public_proposal_text(many_candidates),
            f"exceeds {adc.FLOWBACK_MAX_CANDIDATES} candidates",
        ))
        for name, text, expected in cases:
            with self.subTest(name=name):
                data = text.encode("utf-8")
                filename = f"flowback-{adc.sha256_bytes(data)[:12]}.md"
                errors = adc.validate_flowback_proposal_bytes(data, filename, public_only=True)
                self.assertTrue(any(expected in item for item in errors), errors)

        with tempfile.TemporaryDirectory() as tmp:
            oversized = Path(tmp) / "flowback-000000000000.md"
            oversized.write_bytes(b"x" * (adc.FLOWBACK_MAX_BYTES + 1))
            errors = adc.validate_flowback_proposal(oversized, public_only=True)
            self.assertEqual(errors, [f"proposal exceeds {adc.FLOWBACK_MAX_BYTES} bytes"])

    def test_proposal_rejects_unsafe_targets(self) -> None:
        for target in ("../SKILL.md", "/etc/passwd", "C:\\private\\policy.md", "https://example.invalid/policy"):
            with self.subTest(target=target):
                text = self.public_proposal_text([
                    self.public_candidate_block(proposed_target=target),
                ])
                data = text.encode("utf-8")
                filename = f"flowback-{adc.sha256_bytes(data)[:12]}.md"
                errors = adc.validate_flowback_proposal_bytes(data, filename, public_only=True)
                self.assertTrue(any("proposed target must be a safe relative path" in item for item in errors), errors)

    def test_public_scope_is_repo_agnostic_or_an_approved_generic_shape(self) -> None:
        valid = self.public_proposal_text().replace(
            "- Scope: repo-agnostic", "- Scope: repo-shape:native-wrapper"
        )
        valid_data = valid.encode("utf-8")
        valid_name = f"flowback-{adc.sha256_bytes(valid_data)[:12]}.md"
        self.assertEqual(adc.validate_flowback_proposal_bytes(valid_data, valid_name, public_only=True), [])

        private_shape = self.public_proposal_text().replace(
            "- Scope: repo-agnostic", "- Scope: repo-shape:private-product-name"
        )
        private_data = private_shape.encode("utf-8")
        private_name = f"flowback-{adc.sha256_bytes(private_data)[:12]}.md"
        errors = adc.validate_flowback_proposal_bytes(private_data, private_name, public_only=True)
        self.assertTrue(any("approved generic repo-shape" in item for item in errors), errors)

    def test_proposal_validator_refuses_link_like_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = self.public_proposal_text().encode("utf-8")
            name = f"flowback-{adc.sha256_bytes(data)[:12]}.md"
            target = root / "target.md"
            target.write_bytes(data)
            link = root / name
            try:
                link.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            errors = adc.validate_flowback_proposal(link, public_only=True)
            self.assertTrue(any("link-like" in item for item in errors), errors)

    def test_changed_from_accepts_one_public_proposal_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            skill = repo / "anti-dark-code"
            skill.mkdir()
            (skill / "SKILL.md").write_text("trusted base\n", encoding="utf-8")
            self.init_git_repo(repo)
            base = adc.git_output(repo, ["rev-parse", "HEAD"])
            self.assertIsNotNone(base)

            proposal = self.write_hashed_proposal(skill / "incoming", self.public_proposal_text())
            self.commit_all(repo, "add public proposal")
            errors, paths = adc.validate_incoming(
                repo,
                skill,
                str(base),
                proposal_only=True,
                public_only=True,
            )
            self.assertEqual(errors, [])
            self.assertEqual(paths, [proposal])

    def test_changed_from_without_a_merge_base_fails_closed_and_names_the_remedy(self) -> None:
        # A bounded checkout depth can leave the candidate shallow with no merge
        # base. These comparisons are three-dot, so they fail rather than falling
        # back to two-dot, and the workflows' fetch-depth bound depends on that
        # being understood: an earlier comment claimed a two-dot fallback covered
        # this case, and no such fallback exists on this path.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            skill = repo / "anti-dark-code"
            skill.mkdir()
            (skill / "SKILL.md").write_text("trusted base\n", encoding="utf-8")
            self.init_git_repo(repo)
            self.write_hashed_proposal(skill / "incoming", self.public_proposal_text())
            self.commit_all(repo, "add public proposal")

            # A commit id that is well formed and simply not reachable stands in
            # for a branch point outside the fetch window.
            unreachable = "0" * 40
            errors, paths = adc.validate_incoming(
                repo,
                skill,
                unreachable,
                proposal_only=True,
                public_only=True,
            )
            self.assertEqual(paths, [])
            self.assertEqual(len(errors), 1)
            self.assertIn("could not compare candidate repository", errors[0])
            self.assertIn("no merge base", errors[0])
            self.assertIn("Rebase", errors[0])

    def test_changed_from_uses_merge_base_when_contributor_branch_is_behind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            skill = repo / "anti-dark-code"
            skill.mkdir()
            (skill / "SKILL.md").write_text("trusted base\n", encoding="utf-8")
            self.init_git_repo(repo)
            base_branch = adc.git_output(repo, ["rev-parse", "--abbrev-ref", "HEAD"])
            self.assertIsNotNone(base_branch)
            subprocess.run(["git", "-C", str(repo), "branch", "contributor"], check=True)

            (repo / "maintainer-note.md").write_text("new on base\n", encoding="utf-8")
            self.commit_all(repo, "advance base branch")
            subprocess.run(["git", "-C", str(repo), "checkout", "-q", "contributor"], check=True)

            proposal = self.write_hashed_proposal(skill / "incoming", self.public_proposal_text())
            self.commit_all(repo, "add public proposal from older base")
            errors, paths = adc.validate_incoming(
                repo,
                skill,
                str(base_branch),
                proposal_only=True,
                public_only=True,
            )
            self.assertEqual(errors, [])
            self.assertEqual(paths, [proposal])

    def test_changed_from_rejects_proposal_with_unrelated_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            skill = repo / "anti-dark-code"
            skill.mkdir()
            (skill / "SKILL.md").write_text("trusted base\n", encoding="utf-8")
            (repo / "README.md").write_text("base\n", encoding="utf-8")
            self.init_git_repo(repo)
            base = adc.git_output(repo, ["rev-parse", "HEAD"])
            self.assertIsNotNone(base)

            self.write_hashed_proposal(skill / "incoming", self.public_proposal_text())
            (repo / "README.md").write_text("unrelated change\n", encoding="utf-8")
            self.commit_all(repo, "mix proposal and unrelated change")
            errors, paths = adc.validate_incoming(
                repo,
                skill,
                str(base),
                proposal_only=True,
                public_only=True,
            )
            self.assertEqual(paths, [])
            self.assertTrue(any("exactly one incoming proposal file and change nothing else" in item for item in errors), errors)

    def test_public_proposal_shape_rejects_a_change_without_a_new_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            skill = repo / "anti-dark-code"
            skill.mkdir()
            (skill / "SKILL.md").write_text("trusted base\n", encoding="utf-8")
            self.init_git_repo(repo)
            base = adc.git_output(repo, ["rev-parse", "HEAD"])
            self.assertIsNotNone(base)

            workflow = repo / ".github" / "workflows" / "proposal-intake.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("name: changed intake\n", encoding="utf-8")
            self.commit_all(repo, "change workflow without proposal")
            errors, paths = adc.validate_incoming(
                repo,
                skill,
                str(base),
                proposal_only=True,
                public_only=True,
            )
            self.assertEqual(paths, [])
            self.assertTrue(any("must add exactly one incoming proposal" in item for item in errors), errors)

    def test_changed_from_allows_retiring_an_existing_proposal_by_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            skill = repo / "anti-dark-code"
            skill.mkdir()
            proposal = self.write_hashed_proposal(skill / "incoming", self.public_proposal_text())
            (skill / "SKILL.md").write_text("base policy\n", encoding="utf-8")
            self.init_git_repo(repo)
            base = adc.git_output(repo, ["rev-parse", "HEAD"])
            self.assertIsNotNone(base)

            proposal.unlink()
            (skill / "SKILL.md").write_text("promoted policy\n", encoding="utf-8")
            self.commit_all(repo, "promote reviewed proposal")
            errors, paths = adc.validate_incoming(
                repo,
                skill,
                str(base),
                proposal_only=False,
                public_only=True,
            )
            self.assertEqual(errors, [])
            self.assertEqual(paths, [])

    def test_changed_from_rejects_modifying_an_existing_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            skill = repo / "anti-dark-code"
            skill.mkdir()
            proposal = self.write_hashed_proposal(skill / "incoming", self.public_proposal_text())
            self.init_git_repo(repo)
            base = adc.git_output(repo, ["rev-parse", "HEAD"])
            self.assertIsNotNone(base)

            proposal.write_text(
                proposal.read_text(encoding="utf-8") + "unreviewed mutation\n",
                encoding="utf-8",
                newline="\n",
            )
            self.commit_all(repo, "mutate existing proposal")
            errors, paths = adc.validate_incoming(
                repo,
                skill,
                str(base),
                proposal_only=True,
                public_only=True,
            )
            self.assertEqual(paths, [])
            self.assertTrue(any("immutable" in item for item in errors), errors)

    def test_fresh_install_creates_matching_repo_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            repo.mkdir()
            source = self.copy_clean_skill(base / "source")
            result = adc.install_skill(
                repo,
                source,
                apply=True,
                force=False,
                hosts="none",
            )
            binding_path = repo / ".agents" / "skills" / "anti-dark-code" / "calibration" / "repo-binding.json"
            self.assertTrue(binding_path.exists())
            assessment = adc.assess_repository_binding(repo, binding_path.parent)
            self.assertEqual(assessment["status"], "match")
            self.assertEqual(result["calibration_binding_written"], "calibration/repo-binding.json")

    def test_local_git_binding_stays_stable_across_first_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            source = self.copy_clean_skill(base / "source")
            adc.install_skill(repo, source, apply=True, force=False, hosts="none")
            calibration = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            before = json.loads((calibration / "repo-binding.json").read_text(encoding="utf-8"))["repository_id"]

            (repo / "app.py").write_text("value = 1\n", encoding="utf-8")
            self.init_git_repo(repo)
            plan = adc.install_skill(repo, source, apply=False, force=False, hosts="none")
            after = adc.compute_repository_binding(repo)["repository_id"]
            self.assertEqual(before, after)
            self.assertEqual(plan["calibration_binding"]["status"], "match")

    def test_remote_git_binding_is_stable_across_first_commit_and_protocol(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run([
                "git", "-C", str(repo), "remote", "add", "origin",
                "git@github.com:Example/Repository.git",
            ], check=True)
            before = adc.compute_repository_binding(repo)

            (repo / "app.py").write_text("value = 1\n", encoding="utf-8")
            self.init_git_repo(repo)
            after_commit = adc.compute_repository_binding(repo)
            self.assertEqual(before["repository_id"], after_commit["repository_id"])

            subprocess.run([
                "git", "-C", str(repo), "remote", "set-url", "origin",
                "https://github.com/Example/Repository.git",
            ], check=True)
            after_protocol_change = adc.compute_repository_binding(repo)
            self.assertEqual(before["repository_id"], after_protocol_change["repository_id"])
            self.assertEqual(after_protocol_change["identity_method"], "git-origin-sha256")

    def test_unbound_legacy_calibration_requires_explicit_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            repo.mkdir()
            calibration = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            calibration.mkdir(parents=True)
            (calibration / "invariants.md").write_text("# Same repo legacy facts\n", encoding="utf-8")
            source = self.copy_clean_skill(base / "source")

            plan = adc.install_skill(
                repo,
                source,
                apply=False,
                force=False,
                hosts="none",
            )
            self.assertTrue(plan["blocked"])
            self.assertEqual(plan["calibration_binding"]["status"], "unbound")
            with self.assertRaises(SystemExit):
                adc.install_skill(
                    repo,
                    source,
                    apply=True,
                    force=False,
                    hosts="none",
                )

            result = adc.install_skill(
                repo,
                source,
                apply=True,
                force=False,
                hosts="none",
                accept_unbound_calibration=True,
            )
            self.assertTrue(result["applied"])
            self.assertEqual(adc.assess_repository_binding(repo, calibration)["status"], "match")
            self.assertIn("Same repo legacy facts", (calibration / "invariants.md").read_text(encoding="utf-8"))

    def test_foreign_calibration_is_rejected_until_explicit_rebind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo_a = base / "repo-a"
            repo_b = base / "repo-b"
            repo_a.mkdir()
            repo_b.mkdir()
            source = self.copy_clean_skill(base / "source")
            adc.install_skill(repo_a, source, apply=True, force=False, hosts="none")
            cal_a = repo_a / ".agents" / "skills" / "anti-dark-code" / "calibration"
            cal_b = repo_b / ".agents" / "skills" / "anti-dark-code" / "calibration"
            cal_b.parent.mkdir(parents=True)
            shutil.copytree(cal_a, cal_b)

            plan = adc.install_skill(repo_b, source, apply=False, force=False, hosts="none")
            self.assertEqual(plan["calibration_binding"]["status"], "mismatch")
            self.assertTrue(plan["blocked"])
            with self.assertRaises(SystemExit):
                adc.install_skill(repo_b, source, apply=True, force=False, hosts="none")

            result = adc.install_skill(
                repo_b,
                source,
                apply=True,
                force=False,
                hosts="none",
                rebind_calibration=True,
            )
            self.assertTrue(result["applied"])
            assessment = adc.assess_repository_binding(repo_b, cal_b)
            self.assertEqual(assessment["status"], "match")
            rebound = json.loads((cal_b / "repo-binding.json").read_text(encoding="utf-8"))
            self.assertEqual(len(rebound["previous_repository_ids"]), 1)

    def test_repo_local_source_is_blocked_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            source = self.copy_clean_skill(repo / "tools")
            plan = adc.install_skill(repo, source, apply=False, force=False, hosts="none")
            self.assertTrue(plan["blocked"])
            self.assertTrue(plan["source_scope"]["source_inside_target_repo"])
            with self.assertRaises(SystemExit):
                adc.install_skill(repo, source, apply=True, force=False, hosts="none")

    def test_managed_repo_copy_is_blocked_as_cross_repo_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = self.copy_clean_skill(base / "source")
            (source / ".adc-managed.json").write_text("{}\n", encoding="utf-8")
            repo = base / "target"
            repo.mkdir()
            plan = adc.install_skill(repo, source, apply=False, force=False, hosts="none")
            self.assertTrue(plan["blocked"])
            self.assertTrue(plan["source_scope"]["source_has_managed_install_manifest"])

    def test_source_calibration_is_never_copied_even_with_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = self.copy_clean_skill(base / "source")
            foreign = source / "calibration"
            foreign.mkdir()
            (foreign / "invariants.md").write_text("# FOREIGN REPO SECRET ASSUMPTION\n", encoding="utf-8")
            incoming = source / "incoming"
            incoming.mkdir(exist_ok=True)
            (incoming / "private-proposal.md").write_text("# Local proposal from another repo\n", encoding="utf-8")
            repo = base / "target"
            repo.mkdir()

            blocked = adc.install_skill(repo, source, apply=False, force=False, hosts="none")
            self.assertTrue(blocked["blocked"])
            self.assertIn("invariants.md", blocked["source_scope"]["source_calibration_ignored"])

            result = adc.install_skill(
                repo,
                source,
                apply=True,
                force=False,
                hosts="none",
                allow_unsafe_source=True,
            )
            target_invariants = repo / ".agents" / "skills" / "anti-dark-code" / "calibration" / "invariants.md"
            self.assertTrue(result["applied"])
            self.assertNotIn("FOREIGN REPO", target_invariants.read_text(encoding="utf-8"))
            self.assertFalse((repo / ".agents" / "skills" / "anti-dark-code" / "incoming").exists())

    def test_contaminated_calibration_templates_cannot_be_overridden(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = self.copy_clean_skill(base / "source")
            gates_path = source / "assets" / "templates" / "calibration" / "gates.json"
            gates = json.loads(gates_path.read_text(encoding="utf-8"))
            gates["execution_policy"]["owner_confirmed_safe_to_execute"] = True
            gates_path.write_text(json.dumps(gates), encoding="utf-8")
            repo = base / "target"
            repo.mkdir()

            plan = adc.install_skill(
                repo,
                source,
                apply=False,
                force=False,
                hosts="none",
                allow_unsafe_source=True,
            )
            self.assertTrue(plan["blocked"])
            self.assertTrue(any("unsafe calibration template" in item for item in plan["blocked_reasons"]))
            with self.assertRaises(SystemExit):
                adc.install_skill(
                    repo,
                    source,
                    apply=True,
                    force=False,
                    hosts="none",
                    allow_unsafe_source=True,
                )

    def test_gate_execution_refuses_foreign_calibration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo_a = base / "repo-a"
            repo_b = base / "repo-b"
            repo_a.mkdir()
            repo_b.mkdir()
            cal_a = repo_a / ".agents" / "skills" / "anti-dark-code" / "calibration"
            self.bind_calibration(repo_a, cal_a)
            (cal_a / "gates.json").write_text(json.dumps({
                "schema_version": 1,
                "execution_policy": {"owner_confirmed_safe_to_execute": True},
                "gates": [{
                    "id": "must-not-run",
                    "level": 0,
                    "argv": [sys.executable, "-c", "raise SystemExit(99)"],
                    "enabled": True,
                    "review_status": "approved",
                    "cwd": ".",
                    "timeout_seconds": 30,
                }],
            }), encoding="utf-8")
            cal_b = repo_b / ".agents" / "skills" / "anti-dark-code" / "calibration"
            cal_b.parent.mkdir(parents=True)
            shutil.copytree(cal_a, cal_b)

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = adc.run_gates(repo_b, 0, allow_exec=True, changed_from=None, keep_going=False)
            self.assertEqual(result, 2)
            self.assertIn("calibration is mismatch", output.getvalue())
            self.assertFalse((repo_b / ".anti-dark-code" / "runs").exists())

    def test_flowback_refuses_foreign_calibration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo_a = base / "repo-a"
            repo_b = base / "repo-b"
            repo_a.mkdir()
            repo_b.mkdir()
            cal_a = repo_a / ".agents" / "skills" / "anti-dark-code" / "calibration"
            self.bind_calibration(repo_a, cal_a)
            (cal_a / "upstream-candidates.md").write_text(
                "# Upstream Candidates\n\n"
                "## ADC-LOCAL-003: Local lesson\n\n"
                "- Status: ready\n"
                "- Scope: repo-agnostic\n"
                "- Lesson: Keep local evidence local.\n"
                "- Evidence: local test\n"
                "- Limits: none\n"
                "- Proposed target: references/15-dogfeeding-flowback.md\n"
                "- Proposed change: Add the rule.\n",
                encoding="utf-8",
            )
            cal_b = repo_b / ".agents" / "skills" / "anti-dark-code" / "calibration"
            cal_b.parent.mkdir(parents=True)
            shutil.copytree(cal_a, cal_b)
            with self.assertRaises(SystemExit):
                adc.flowback(repo_b, parent=None, stage_to_parent=False, mark_staged=False)

    def test_flowback_refuses_repo_calibrated_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            repo.mkdir()
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            self.bind_calibration(repo, cal)
            (cal / "upstream-candidates.md").write_text(
                "# Upstream Candidates\n\n"
                "## ADC-LOCAL-004: Parent check\n\n"
                "- Status: ready\n"
                "- Scope: repo-agnostic\n"
                "- Lesson: Stage only to a clean parent.\n"
                "- Evidence: local test\n"
                "- Limits: none\n"
                "- Proposed target: references/15-dogfeeding-flowback.md\n"
                "- Proposed change: Add the parent check.\n",
                encoding="utf-8",
            )
            parent = self.copy_clean_skill(base / "parent")
            parent_cal = parent / "calibration"
            parent_cal.mkdir()
            (parent_cal / "invariants.md").write_text("# Repo-local parent\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                adc.flowback(repo, parent=parent, stage_to_parent=True, mark_staged=False, public=True)

    def test_flowback_refuses_managed_parent_without_calibration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            repo.mkdir()
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            self.bind_calibration(repo, cal)
            (cal / "upstream-candidates.md").write_text(
                "# Upstream Candidates\n\n"
                "## ADC-LOCAL-005: Managed parent check\n\n"
                "- Status: ready\n"
                "- Scope: repo-agnostic\n"
                "- Lesson: A managed repo copy is not a shared parent.\n"
                "- Evidence: local test\n"
                "- Limits: none\n"
                "- Proposed target: references/15-dogfeeding-flowback.md\n"
                "- Proposed change: Add the managed-parent check.\n",
                encoding="utf-8",
            )
            parent = self.copy_clean_skill(base / "parent")
            (parent / ".adc-managed.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                adc.flowback(repo, parent=parent, stage_to_parent=True, mark_staged=False, public=True)

    def test_general_path_validator_rejects_personal_user_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clean_skill = self.copy_clean_skill(Path(tmp))
            template = clean_skill / "assets" / "templates" / "calibration" / "README.md"
            personal_path = "/" + "home/" + "alice/private/repo"
            template.write_text(template.read_text(encoding="utf-8") + f"\nUse {personal_path}.\n", encoding="utf-8")
            errors, _ = adc.validate_skill(clean_skill, mode="distribution")
            self.assertTrue(any("personal absolute paths" in item for item in errors))

    def test_legacy_codex_calibration_is_reported_without_auto_migration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            legacy = repo / ".codex" / "skills" / "anti-dark-code" / "calibration"
            legacy.mkdir(parents=True)
            (legacy / "invariants.md").write_text("# Same-repo legacy fact\n", encoding="utf-8")
            target = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            found = adc.legacy_calibration_locations(repo, target)
            item = next(entry for entry in found if entry["path"].startswith(".codex/"))
            self.assertFalse(item["auto_migration"])
            self.assertEqual(item["binding_status"], "unbound")

    def test_source_validation_ignores_flowback_incoming(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clean_skill = self.copy_clean_skill(Path(tmp))
            incoming = clean_skill / "incoming"
            incoming.mkdir()
            personal_path = "/" + "home/" + "alice/private"
            (incoming / "proposal.md").write_text(
                f"# Local proposal\n\nUse {personal_path} and an em dash \u2014 here.\n",
                encoding="utf-8",
            )
            errors, warnings = adc.validate_skill(clean_skill, mode="universal")
            self.assertEqual(errors, [])
            self.assertTrue(any("staged incoming" in item for item in warnings))

    def test_distribution_validation_rejects_runtime_incoming_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clean_skill = self.copy_clean_skill(Path(tmp))
            incoming = clean_skill / "incoming"
            incoming.mkdir()
            (incoming / "proposal.md").write_text("# Runtime proposal\n", encoding="utf-8")
            errors, _ = adc.validate_skill(clean_skill, mode="distribution")
            self.assertTrue(any("runtime-only incoming" in item for item in errors))

    def test_universal_validation_rejects_symlinked_incoming_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            clean_skill = self.copy_clean_skill(base / "source")
            victim = base / "foreign-incoming"
            victim.mkdir()
            try:
                (clean_skill / "incoming").symlink_to(victim, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            errors, _ = adc.validate_skill(clean_skill, mode="universal")
            self.assertTrue(any("incoming/ inbox contains link-like" in item for item in errors))

    def test_installed_validation_uses_managed_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = self.copy_clean_skill(base / "source")
            repo = base / "repo"
            repo.mkdir()
            adc.install_skill(repo, source, apply=True, force=False, hosts="none")
            installed = repo / ".agents" / "skills" / "anti-dark-code"

            errors, warnings = adc.validate_skill(installed, mode="auto")
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

            (installed / "SKILL.md").write_text(
                (installed / "SKILL.md").read_text(encoding="utf-8") + "\nLocal mutation.\n",
                encoding="utf-8",
            )
            errors, _ = adc.validate_skill(installed, mode="installed")
            self.assertTrue(any("checksum mismatch" in item for item in errors))

    def test_installed_validation_rejects_nested_calibration_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = self.copy_clean_skill(base / "source")
            repo = base / "repo"
            repo.mkdir()
            adc.install_skill(repo, source, apply=True, force=False, hosts="none")
            installed = repo / ".agents" / "skills" / "anti-dark-code"
            victim = base / "foreign-notes.md"
            victim.write_text("foreign\n", encoding="utf-8")
            try:
                (installed / "calibration" / "foreign-notes.md").symlink_to(victim)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            errors, _ = adc.validate_skill(installed, mode="installed")
            self.assertTrue(any("calibration contains link-like entries" in item for item in errors))

    def test_installer_refuses_repo_skill_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = self.copy_clean_skill(base / "source")
            repo = base / "repo"
            victim = base / "shared-core"
            (repo / ".agents" / "skills").mkdir(parents=True)
            victim.mkdir()
            try:
                (repo / ".agents" / "skills" / "anti-dark-code").symlink_to(victim, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")

            with self.assertRaises(SystemExit):
                adc.install_skill(repo, source, apply=False, force=False, hosts="none")
            with self.assertRaises(SystemExit):
                adc.install_skill(repo, source, apply=True, force=False, hosts="none")
            errors, _ = adc.validate_skill(repo / ".agents" / "skills" / "anti-dark-code", mode="auto")
            self.assertTrue(any("skill root must not be a symlink or junction" in item for item in errors))
            self.assertFalse((victim / "SKILL.md").exists())

    def test_installer_refuses_nested_managed_file_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = self.copy_clean_skill(base / "source")
            repo = base / "repo"
            target = repo / ".agents" / "skills" / "anti-dark-code"
            target.mkdir(parents=True)
            victim = base / "victim-skill.md"
            victim.write_text("unchanged\n", encoding="utf-8")
            try:
                (target / "SKILL.md").symlink_to(victim)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")

            with self.assertRaises(SystemExit):
                adc.install_skill(repo, source, apply=False, force=False, hosts="none")
            with self.assertRaises(SystemExit):
                adc.install_skill(repo, source, apply=True, force=False, hosts="none")
            self.assertEqual(victim.read_text(encoding="utf-8"), "unchanged\n")

    def test_profile_write_refuses_symlinked_calibration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            skill = repo / ".agents" / "skills" / "anti-dark-code"
            victim = base / "foreign-calibration"
            skill.mkdir(parents=True)
            victim.mkdir()
            try:
                (skill / "calibration").symlink_to(victim, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaises(SystemExit):
                adc.write_profile(repo, {"schema_version": 1})
            self.assertFalse((victim / "repo-profile.json").exists())

    def test_flowback_refuses_symlinked_parent_incoming(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            repo.mkdir()
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            self.bind_calibration(repo, cal)
            (cal / "upstream-candidates.md").write_text(
                "# Upstream Candidates\n\n"
                "## ADC-LOCAL-003: Safe staging\n\n"
                "- Status: ready\n"
                "- Scope: repo-agnostic\n"
                "- Lesson: Refuse redirected proposal inboxes.\n"
                "- Evidence: local test\n"
                "- Limits: symlink-capable filesystems\n"
                "- Proposed target: references/15-dogfeeding-flowback.md\n"
                "- Proposed change: Document physical path isolation.\n",
                encoding="utf-8",
            )
            parent = self.copy_clean_skill(base / "parent")
            victim = base / "foreign-incoming"
            victim.mkdir()
            try:
                (parent / "incoming").symlink_to(victim, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")

            with self.assertRaises(SystemExit):
                adc.flowback(repo, parent=parent, stage_to_parent=True, mark_staged=False, public=True)
            self.assertEqual(list(victim.iterdir()), [])

    def test_probe_ignores_all_host_sibling_skill_trees(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "src" / "app.py").write_text("print('product')\n", encoding="utf-8")
            for root in (
                repo / ".agents" / "skills" / "other-skill",
                repo / ".claude" / "skills" / "other-skill",
                repo / ".gemini" / "skills" / "other-skill",
                repo / ".codex" / "skills" / "other-skill",
            ):
                root.mkdir(parents=True)
                (root / "noise.py").write_text(
                    "async worker payment simulation Date.now fetch router component database\n",
                    encoding="utf-8",
                )

            profile = adc.probe_repo(repo, max_files=1000, content_scan_limit=1000)
            self.assertEqual(profile["counts"]["source_files"], 1)
            evidence = [
                item
                for signal in profile["signals"].values()
                for item in signal.get("evidence", [])
            ]
            self.assertFalse(any("other-skill" in item for item in evidence))

    def test_source_identity_and_changed_slice_ignore_all_host_skill_trees(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "ADC Test"], check=True)
            (repo / "src").mkdir()
            (repo / "src" / "app.py").write_text("print('product')\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "src/app.py"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "baseline"], check=True)

            before = adc.current_source_identity(repo)
            for root in (
                repo / ".agents" / "skills" / "other-skill",
                repo / ".claude" / "skills" / "other-skill",
                repo / ".gemini" / "skills" / "other-skill",
                repo / ".codex" / "skills" / "other-skill",
            ):
                root.mkdir(parents=True)
                (root / "noise.py").write_text("print('tooling')\n", encoding="utf-8")

            after_skill_only = adc.current_source_identity(repo)
            self.assertEqual(
                before["worktree_status_sha256"],
                after_skill_only["worktree_status_sha256"],
            )
            self.assertEqual(adc.changed_files(repo, "HEAD"), [])

            (repo / "src" / "new.py").write_text("print('changed')\n", encoding="utf-8")
            changed = adc.changed_files(repo, "HEAD")
            self.assertEqual(changed, ["src/new.py"])

    def test_universal_validation_allows_user_level_symlink_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            clean_skill = self.copy_clean_skill(base / "source")
            alias = base / "alias"
            try:
                alias.symlink_to(clean_skill, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")

            errors, warnings = adc.validate_skill(alias, mode="universal")
            self.assertEqual(errors, [])
            self.assertTrue(any("symlink alias" in item for item in warnings))

            distribution_errors, _ = adc.validate_skill(alias, mode="distribution")
            self.assertTrue(any("root must not be a symlink" in item for item in distribution_errors))

    def test_timeout_terminates_gate_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            self.bind_calibration(repo, cal)
            marker = repo / "grandchild-survived.txt"
            child = repo / "child.py"
            parent = repo / "parent.py"
            child.write_text(
                "import pathlib, time\n"
                "time.sleep(2.0)\n"
                f"pathlib.Path({str(marker)!r}).write_text('survived', encoding='utf-8')\n",
                encoding="utf-8",
            )
            parent.write_text(
                "import subprocess, sys, time\n"
                f"subprocess.Popen([sys.executable, {str(child)!r}])\n"
                "time.sleep(10.0)\n",
                encoding="utf-8",
            )
            (cal / "gates.json").write_text(json.dumps({
                "schema_version": 1,
                "execution_policy": {"owner_confirmed_safe_to_execute": True},
                "gates": [{
                    "id": "timeout-tree",
                    "level": 0,
                    "argv": [sys.executable, str(parent)],
                    "enabled": True,
                    "review_status": "approved",
                    "cwd": ".",
                    "timeout_seconds": 1,
                }],
            }), encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()):
                result = adc.run_gates(repo, 0, allow_exec=True, changed_from=None, keep_going=False)
            self.assertEqual(result, 1)
            time.sleep(2.5)
            self.assertFalse(marker.exists())
            packets = list((repo / ".anti-dark-code" / "runs").rglob("ADC-FAIL-*.json"))
            self.assertEqual(len(packets), 1)
            packet = json.loads(packets[0].read_text(encoding="utf-8"))
            self.assertTrue(packet["timed_out"])
            self.assertIn(packet["timeout_termination"]["strategy"], {
                "posix-process-group", "windows-process-group"
            })

    def test_flowback_refuses_symlinked_parent_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            repo.mkdir()
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            self.bind_calibration(repo, cal)
            (cal / "upstream-candidates.md").write_text(
                "# Upstream Candidates\n\n"
                "## ADC-LOCAL-006: Destination safety\n\n"
                "- Status: ready\n"
                "- Scope: repo-agnostic\n"
                "- Lesson: Refuse proposal writes through symlinks.\n"
                "- Evidence: local test\n"
                "- Limits: none\n"
                "- Proposed target: references/15-dogfeeding-flowback.md\n"
                "- Proposed change: Document the fail-closed rule.\n",
                encoding="utf-8",
            )
            proposal = adc.flowback(repo, parent=None, stage_to_parent=False, mark_staged=False)
            parent = self.copy_clean_skill(base / "parent")
            incoming = parent / "incoming"
            incoming.mkdir()
            victim = base / "victim.md"
            victim.write_text("unchanged\n", encoding="utf-8")
            try:
                (incoming / proposal.name).symlink_to(victim)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaises(SystemExit):
                adc.flowback(repo, parent=parent, stage_to_parent=True, mark_staged=False, public=True)
            self.assertEqual(victim.read_text(encoding="utf-8"), "unchanged\n")

    def test_operational_guidance_contains_no_project_specific_migration(self) -> None:
        skill_root = Path(__file__).resolve().parents[1]
        package_root = skill_root.parent
        paths = [
            skill_root / "SKILL.md",
            skill_root / "references" / "13-calibrated-local-mode.md",
            skill_root / "references" / "15-dogfeeding-flowback.md",
        ]
        paths.extend(path for path in (package_root / "MIGRATION.md", package_root / "README.md") if path.exists())
        forbidden_project_name = "chron" + "icle"
        for path in paths:
            self.assertNotIn(forbidden_project_name, path.read_text(encoding="utf-8").lower(), str(path))

    def test_pdf_normalization_collapses_only_generation_timestamps(self) -> None:
        # Fixture pair: identical documents rendered at different wall-clock times.
        # Raw bytes differ, normalized bytes must not. If normalize_pdf_bytes were
        # reverted to the identity function, the second assertion goes red.
        render_a = (
            b"%PDF-1.4\n<</Producer (Skia/PDF m151)\n"
            b"/CreationDate (D:20260822110333+00'00')\n"
            b"/ModDate (D:20260822110333+00'00')>>\nbody bytes\n"
        )
        render_b = render_a.replace(b"20260822110333", b"20260101000000")
        self.assertNotEqual(render_a, render_b)
        self.assertEqual(adc.normalize_pdf_bytes(render_a), adc.normalize_pdf_bytes(render_b))

        # Content differences must still survive normalization, or the digest
        # would be satisfied by any document at all.
        altered = render_a.replace(b"body bytes", b"other bytes")
        self.assertNotEqual(adc.normalize_pdf_bytes(render_a), adc.normalize_pdf_bytes(altered))
        self.assertNotIn(b"20260822110333", adc.normalize_pdf_bytes(render_a))

    def test_source_release_surfaces_match_canonical_version(self) -> None:
        skill_root = Path(__file__).resolve().parents[1]
        package_root = skill_root.parent
        changelog = package_root / "CHANGELOG.md"
        readme = package_root / "README.md"
        if not changelog.exists() and not readme.exists():
            self.skipTest("outer release documents are intentionally absent from a deployed skill copy")

        version = (skill_root / "VERSION").read_text(encoding="utf-8").strip()
        release_date = version.split("-", 1)[0].replace(".", "-")
        brief = package_root / "brief" / "anti-dark-code-brief.html"
        pdf = package_root / "brief" / "anti-dark-code-brief.pdf"
        pdf_provenance = package_root / "brief" / "anti-dark-code-brief.pdf.provenance.json"
        website = package_root / "docs" / "index.html"
        catalog = json.loads(
            (skill_root / "assets" / "verification-capabilities.json").read_text(encoding="utf-8")
        )

        self.assertIn(f"**Version**: `{version}`", readme.read_text(encoding="utf-8"))
        self.assertIn(f"## {version}", changelog.read_text(encoding="utf-8"))
        self.assertEqual(catalog["catalog_version"], version)
        for path in (brief, website):
            text = path.read_text(encoding="utf-8")
            self.assertIn(version, text, str(path))
            self.assertIn(f"updated {release_date}", text, str(path))
            self.assertIn('<span class="id">16</span>', text, str(path))
        self.assertTrue(pdf.read_bytes().startswith(b"%PDF-"), str(pdf))
        provenance = json.loads(pdf_provenance.read_text(encoding="utf-8"))
        self.assertEqual(provenance["version"], version)
        self.assertEqual(provenance["source_sha256"], adc.sha256_file(brief))
        self.assertEqual(provenance["pdf_sha256"], adc.sha256_file(pdf))
        # pdf_sha256 identifies this exact artifact and can never be reproduced,
        # because every render restamps the timestamps. The normalized digest is
        # the reproducibility claim: a re-render of this brief must match it.
        # Both are integrity checks over committed bytes. Neither proves the PDF
        # was regenerated from the current HTML; only an actual re-render does.
        self.assertEqual(provenance["normalized_pdf_sha256"], adc.normalized_pdf_sha256(pdf))



if __name__ == "__main__":
    unittest.main()
