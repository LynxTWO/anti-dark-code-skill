from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
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

    def test_skill_validates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clean_skill = self.copy_clean_skill(Path(tmp))
            errors, warnings = adc.validate_skill(clean_skill, mode="distribution")
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

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
                adc.flowback(repo, parent=parent, stage_to_parent=True, mark_staged=False)

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
                adc.flowback(repo, parent=parent, stage_to_parent=True, mark_staged=False)

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
                adc.flowback(repo, parent=parent, stage_to_parent=True, mark_staged=False)
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
                adc.flowback(repo, parent=parent, stage_to_parent=True, mark_staged=False)
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



if __name__ == "__main__":
    unittest.main()
