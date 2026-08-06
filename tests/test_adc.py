from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "adc.py"
spec = importlib.util.spec_from_file_location("adc", SCRIPT)
assert spec and spec.loader
adc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adc)


class AntiDarkCodeToolsTests(unittest.TestCase):
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
        errors, warnings = adc.validate_skill(Path(__file__).resolve().parents[1])
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

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
            repo = Path(tmp)
            source = Path(__file__).resolve().parents[1]
            result = adc.install_skill(repo, source, apply=True, force=False, hosts="all")
            self.assertTrue(result["applied"])
            target = repo / ".agents" / "skills" / "anti-dark-code"
            self.assertTrue((target / "SKILL.md").exists())
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


    def test_probe_ignores_installed_skill_and_keeps_github_ci(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.make_node_repo(repo)
            source = Path(__file__).resolve().parents[1]
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

    def test_gate_runner_refuses_unconfirmed_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            cal.mkdir(parents=True)
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
            self.assertIn("Exact command arrays", out.read_text(encoding="utf-8"))
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
            internal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            internal.mkdir(parents=True)
            (internal / "repo-profile.json").write_text("{}\n", encoding="utf-8")
            self.assertTrue(adc.profile_is_fresh(repo, profile))

    def test_installer_migrates_fallback_calibration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            fallback = repo / ".anti-dark-code" / "calibration"
            fallback.mkdir(parents=True)
            (fallback / "invariants.md").write_text("# Existing local truth\n", encoding="utf-8")
            result = adc.install_skill(repo, Path(__file__).resolve().parents[1], apply=True, force=False, hosts="none")
            target = repo / ".agents" / "skills" / "anti-dark-code" / "calibration" / "invariants.md"
            self.assertIn("calibration/invariants.md", result["calibration_migrated"])
            self.assertEqual(target.read_text(encoding="utf-8"), "# Existing local truth\n")

    def test_flowback_redacts_repo_paths_and_secret_like_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            cal = repo / ".agents" / "skills" / "anti-dark-code" / "calibration"
            cal.mkdir(parents=True)
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



if __name__ == "__main__":
    unittest.main()
