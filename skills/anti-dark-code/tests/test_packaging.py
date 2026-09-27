"""Exercise discovery, migration, metadata drift and tagged release validation."""
import json
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest
from unittest import mock
from types import SimpleNamespace

import test_adc

adc = test_adc.adc
packaging = adc.load_packaging_helper()


class PluginPackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name).resolve() / "package"
        self.fixture = test_adc.AntiDarkCodeToolsTests()
        self.old_version = "2026.09.15-unified.15"
        self.version = "2026.09.27-unified.16"
        self.core = self.fixture.make_skill_repo(
            self.repo, self.old_version, f"# Changelog\n\n## {self.old_version}\n\nFirst.\n")
        self.git("tag", "old-layout")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], text=True).strip()

    def move_core(self):
        (self.repo / "skills").mkdir()
        destination = self.repo / packaging.CORE_PATH
        self.core.rename(destination)
        self.core = destination
        (self.core / "VERSION").write_text(self.version + "\n", encoding="utf-8")
        (self.repo / "CHANGELOG.md").write_text(
            f"# Changelog\n\n## {self.version}\n\nMove the core to skills/anti-dark-code/.\n", encoding="utf-8")
        for relative, value in packaging.metadata(self.version).items():
            path = self.repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value) + "\n", encoding="utf-8")

    def test_tag_migration_keeps_unchanged_references_but_detects_changed_content(self):
        self.assertTrue(adc.release_check(self.repo, "old-layout")["ok"])
        self.move_core()
        self.fixture.commit_all(self.repo, "package the same skill")
        self.git("tag", "new-layout")
        result = adc.release_check(self.repo, "new-layout", previous_tag="old-layout")
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["packaging_valid"])
        self.assertEqual(result["undescribed_files"], [])
        ref = self.core / "references" / "14-deterministic-verification.md"
        ref.write_text(ref.read_text(encoding="utf-8") + "\nA substantive new rule.\n", encoding="utf-8")
        self.fixture.commit_all(self.repo, "change a moved reference without notes")
        self.git("tag", "changed-layout")
        result = adc.release_check(self.repo, "changed-layout", previous_tag="old-layout")
        self.assertFalse(result["ok"])
        self.assertIn("references/14-deterministic-verification.md", result["undescribed_files"])

    def test_incomplete_plugin_core_cannot_fall_back_to_a_legacy_duplicate(self):
        self.move_core()
        shutil.copytree(self.core, self.repo / "anti-dark-code")
        (self.core / "VERSION").unlink()
        self.fixture.commit_all(self.repo, "incomplete plugin with a valid legacy copy")
        self.git("tag", "incomplete-plugin")
        result = adc.release_check(self.repo, "incomplete-plugin", previous_tag="old-layout")
        self.assertFalse(result["ok"])
        self.assertIn("distributable core", " ".join(result["errors"]))

    def test_metadata_checks_treat_windows_junctions_as_redirects(self):
        self.move_core()
        redirect = self.repo / ".claude-plugin"
        with mock.patch.object(Path, "is_junction", lambda path: path == redirect):
            errors = packaging.validate_package(self.repo)
        self.assertTrue(any("metadata path must not traverse links" in error for error in errors))

    def test_tag_metadata_is_checked_instead_of_working_tree(self):
        self.move_core()
        path = self.repo / "plugin.json"
        wrong = json.loads(path.read_text(encoding="utf-8"))
        wrong["version"] = "0.0.0"
        path.write_text(json.dumps(wrong), encoding="utf-8")
        self.fixture.commit_all(self.repo, "stale manifest version")
        self.git("tag", "stale-metadata")
        path.write_text(json.dumps(packaging.metadata(self.version)["plugin.json"]), encoding="utf-8")
        self.assertEqual(packaging.validate_package(self.repo), [])
        result = adc.release_check(self.repo, "stale-metadata", previous_tag="old-layout")
        self.assertFalse(result["ok"])
        self.assertFalse(result["packaging_valid"])
        self.assertIn("plugin.json", result["packaging_errors"][0])

    def test_skill_is_discoverable_without_links_or_duplicate_source(self):
        self.move_core()
        discovered = [p.name for p in (self.repo / "skills").iterdir() if (p / "SKILL.md").is_file()]
        self.assertEqual(discovered, ["anti-dark-code"])
        self.assertEqual(packaging.validate_package(self.repo), [])
        (self.repo / "anti-dark-code").mkdir()
        self.assertIn("duplicate", " ".join(packaging.validate_package(self.repo)))

    def test_normalized_version_does_not_invent_a_second_version_source(self):
        self.assertEqual(packaging.plugin_version(self.version), "2026.9.27-unified.16")
        self.assertEqual(packaging.plugin_version("1.2.3"), "1.2.3")
        for invalid in ("latest", "1.2", "1.2.3-unified.016"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                packaging.plugin_version(invalid)

    def test_missing_or_redirected_artwork_is_rejected(self):
        self.move_core()
        path = self.core / "assets" / "brand" / "illuminated-code.png"
        with mock.patch.object(Path, "is_junction", lambda part: part == path.parent):
            self.assertIn("artwork path must not traverse links", " ".join(packaging.validate_package(self.repo)))
        path.unlink()
        self.assertIn("missing plugin artwork", " ".join(packaging.validate_package(self.repo)))

    def test_optional_host_checks_report_unavailable_and_failures(self):
        with mock.patch.object(packaging.shutil, "which", return_value=None):
            results = packaging.check_hosts(self.repo)
        self.assertEqual(len(results), 3)
        self.assertTrue(all(row["status"] == "capability_unavailable" for row in results))
        with mock.patch.object(packaging.shutil, "which", side_effect=lambda name: "/bin/claude" if name == "claude" else None), \
             mock.patch.object(packaging.subprocess, "run", return_value=SimpleNamespace(returncode=1, stdout="invalid", stderr="")) as run:
            results = packaging.check_hosts(self.repo)
        self.assertEqual(results[0]["status"], "failed")
        self.assertEqual(run.call_args.args[0], ["/bin/claude", "plugin", "validate", "--strict", str(self.repo)])

    def test_missing_manifest_and_automatic_hooks_are_rejected(self):
        self.move_core()
        path = self.repo / "gemini-extension.json"
        path.unlink()
        self.assertIn("gemini-extension.json", " ".join(packaging.validate_package(self.repo)))
        path.write_text(json.dumps(packaging.metadata(self.version)["gemini-extension.json"]), encoding="utf-8")
        path = self.repo / ".claude-plugin" / "plugin.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["hooks"] = "./automatic-collection.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        self.assertIn("declared skill-only package", " ".join(packaging.validate_package(self.repo)))


if __name__ == "__main__":
    unittest.main()
