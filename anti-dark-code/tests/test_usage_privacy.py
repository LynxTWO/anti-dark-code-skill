"""Synthetic files exercise setup privacy, interruption, and data control."""
from contextlib import closing
import importlib.util
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "adc_usage.py"


class UsagePrivacyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "source"
        self.source.mkdir()
        self.ledger = self.root / "ledger"
        spec = importlib.util.spec_from_file_location("privacy_usage", SCRIPT)
        self.adc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.adc)

    def init(self):
        return self.adc.init_ledger(self.ledger, {"codex": self.source}, opt_in=True)

    @unittest.skipUnless(os.name == "posix", "POSIX mode and ownership checks")
    def test_existing_shared_directory_is_refused_without_writes(self):
        self.ledger.mkdir(mode=0o755)
        self.ledger.chmod(0o755)
        with self.assertRaisesRegex(ValueError, "private|0700"):
            self.init()
        self.assertEqual([], list(self.ledger.iterdir()))
        self.assertEqual(0o755, stat.S_IMODE(self.ledger.stat().st_mode))

    @unittest.skipUnless(os.name == "posix", "POSIX mode and ownership checks")
    def test_existing_private_directory_and_new_files_remain_private(self):
        self.ledger.mkdir(mode=0o700)
        previous = os.umask(0o022)
        try:
            self.init()
            self.assertEqual(0o700, stat.S_IMODE(self.ledger.stat().st_mode))
            for path in self.ledger.iterdir():
                self.assertEqual(0o600, stat.S_IMODE(path.stat().st_mode))
            self.adc.disable(self.ledger)
            self.assertEqual(0o600, stat.S_IMODE((self.ledger / "config.json").stat().st_mode))
        finally:
            os.umask(previous)

    @unittest.skipUnless(os.name == "posix", "POSIX owner API")
    def test_wrong_owner_is_refused_before_sensitive_writes(self):
        self.ledger.mkdir(mode=0o700)
        with patch.object(self.adc.os, "getuid", return_value=os.getuid() + 1):
            with self.assertRaisesRegex(ValueError, "owner"):
                self.init()
        self.assertEqual([], list(self.ledger.iterdir()))

    def test_database_failure_leaves_target_retryable_and_not_enabled(self):
        with patch.object(self.adc, "_connect", side_effect=OSError("synthetic failure")):
            with self.assertRaises(OSError):
                self.init()
        self.assertFalse((self.ledger / "config.json").exists())
        self.assertEqual("enabled", self.init()["status"])
        self.assertEqual(0, self.adc.summary(self.ledger)["events"])

    def test_unrelated_existing_content_is_never_removed(self):
        self.ledger.mkdir(mode=0o700)
        sentinel = self.ledger / "keep.txt"
        sentinel.write_text("keep", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.init()
        self.assertEqual("keep", sentinel.read_text(encoding="utf-8"))

    def test_failed_commit_does_not_publish_enabled_configuration(self):
        with patch.object(self.adc.os, "rename", side_effect=OSError("synthetic interruption")):
            with self.assertRaises(OSError):
                self.init()
        self.assertFalse((self.ledger / "config.json").exists())
        self.assertEqual("enabled", self.init()["status"])

    def test_redirection_is_refused_without_touching_destination(self):
        target = self.root / "target"
        target.mkdir(mode=0o700)
        try:
            self.ledger.symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest("host cannot create symlinks")
        with self.assertRaisesRegex(ValueError, "linked"):
            self.init()
        self.assertEqual([], list(target.iterdir()))

    def test_windows_acl_check_fails_closed_and_does_not_interpolate_path(self):
        path = self.root / "literal $name; and 'quotes'"
        for returncode, stdout, expected in ((0, b"private\n", True), (0, b"unverified\n", False),
                                              (1, b"private\n", False), (0, b"", False)):
            with self.subTest(stdout=stdout, returncode=returncode):
                with patch.object(self.adc.subprocess, "run", return_value=SimpleNamespace(returncode=returncode, stdout=stdout)) as run:
                    self.assertEqual(expected, self.adc._windows_private(path))
                    args, kwargs = run.call_args
                    self.assertNotIn(str(path), " ".join(args[0]))
                    self.assertEqual(str(path), kwargs["env"]["ADC_PRIVACY_CHECK_PATH"])
                    self.assertEqual(15, kwargs["timeout"])
        with patch.object(self.adc.subprocess, "run", side_effect=OSError()):
            self.assertFalse(self.adc._windows_private(path))

    def test_private_directory_is_checked_on_reopen(self):
        self.init()
        with patch.object(self.adc, "_check_private", side_effect=ValueError("privacy unverified")):
            with self.assertRaisesRegex(ValueError, "privacy"):
                self.adc.collect(self.ledger)

    def test_each_staged_file_failure_is_retryable_without_removing_unrelated_files(self):
        original = self.adc._private_create
        for failed_name in ("usage.sqlite3", ".gitignore", "config.json"):
            with self.subTest(phase=failed_name):
                self.ledger = self.root / ("ledger-" + failed_name.replace(".", "-"))
                def fail(path):
                    if path.name == failed_name:
                        (path.parent / "unrelated.txt").write_text("preserve", encoding="utf-8")
                        raise OSError("synthetic interruption")
                    return original(path)
                with patch.object(self.adc, "_private_create", side_effect=fail):
                    with self.assertRaises(OSError):
                        self.init()
                self.assertFalse((self.ledger / "config.json").exists())
                self.assertEqual("enabled", self.init()["status"])
        sentinels = list(self.root.glob(".adc-init-*/unrelated.txt"))
        self.assertEqual(3, len(sentinels))
        self.assertTrue(all(path.read_text(encoding="utf-8") == "preserve" for path in sentinels))

    def test_export_is_private_scoped_and_never_overwrites(self):
        self.init()
        export_root = self.root / "exports"
        export_root.mkdir(mode=0o700)
        if os.name == "nt":
            self.adc._secure_new_windows_stage(export_root)
        target = export_root / "summary.json"
        report = self.adc.export_summary(self.ledger, target)
        data = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual("exported", report["status"])
        self.assertEqual(0, data["events"])
        self.assertNotIn(str(self.source), target.read_text(encoding="utf-8"))
        self.assertNotIn("sources", data)
        if os.name == "posix":
            self.assertEqual(0o600, stat.S_IMODE(target.stat().st_mode))
        before = target.read_bytes()
        with self.assertRaises(FileExistsError):
            self.adc.export_summary(self.ledger, target)
        self.assertEqual(before, target.read_bytes())
        for output in (self.source / "export.json", self.ledger / "export.json"):
            with self.assertRaises(ValueError):
                self.adc.export_summary(self.ledger, output)
            self.assertFalse(output.exists())

    @unittest.skipUnless(os.name == "nt", "Windows ACL evidence requires Windows")
    def test_windows_acl_accepts_private_and_refuses_shared_directory(self):
        self.ledger.mkdir()
        # Test fixtures may inherit runner-specific grants. Set an owner-only ACL
        # on this disposable directory using the same OS API users configure.
        import subprocess
        script = r'''
$ErrorActionPreference = 'Stop'
$sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
$acl = New-Object System.Security.AccessControl.DirectorySecurity
$acl.SetOwner($sid)
$acl.SetAccessRuleProtection($true, $false)
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule($sid, 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow')
$acl.AddAccessRule($rule)
Set-Acl -LiteralPath $env:ADC_PRIVACY_CHECK_PATH -AclObject $acl
'''
        subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            env={**os.environ, "ADC_PRIVACY_CHECK_PATH": str(self.ledger)}, check=True, capture_output=True)
        self.assertTrue(self.adc._windows_private(self.ledger))
        shared = script.replace("$acl.AddAccessRule($rule)", "$acl.AddAccessRule($rule)\n"
            "$everyone = New-Object System.Security.Principal.SecurityIdentifier('S-1-1-0')\n"
            "$acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($everyone, 'Read', 'ContainerInherit,ObjectInherit', 'None', 'Allow')))")
        subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", shared],
            env={**os.environ, "ADC_PRIVACY_CHECK_PATH": str(self.ledger)}, check=True, capture_output=True)
        self.assertFalse(self.adc._windows_private(self.ledger))
        with self.assertRaisesRegex(ValueError, "privacy"):
            self.init()
        self.assertEqual([], list(self.ledger.iterdir()))


if __name__ == "__main__":
    unittest.main()
