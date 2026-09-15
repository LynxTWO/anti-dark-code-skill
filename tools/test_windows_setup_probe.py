"""The observer preserves subprocess behavior and cannot publish child payloads."""
import json
import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tools import windows_setup_probe as probe


class WindowsSetupProbeTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        observer = patch.object(probe, "_events", self.events)
        observer.start()
        self.addCleanup(observer.stop)
        self.argv = ["powershell.exe", "-NoLogo", "-Command", "DirectorySecurity"]
        self.options = {"timeout": 15, "capture_output": True, "check": False,
                        "env": {"ADC_PRIVACY_CHECK_PATH": "synthetic-private-path"}}

    def test_preserves_arguments_result_and_omits_private_payloads(self):
        result = SimpleNamespace(returncode=1, stdout=b"synthetic-private-output",
            stderr=b"FileNotFoundException: synthetic-private-error")
        with patch.object(probe, "_run", return_value=result) as run:
            self.assertIs(result, probe._observed_run(self.argv, **self.options))
        run.assert_called_once_with(self.argv, **self.options)
        event, = self.events
        self.assertEqual(("stage", "refused", 1),
                         (event["operation"], event["result"], event["returncode"]))
        self.assertEqual(["FileNotFoundException"], event["error_types"])
        self.assertEqual("other", event["stdout_class"])
        self.assertNotIn("synthetic-private", json.dumps(event))

    def test_timeout_is_reraised_without_retry_or_output_disclosure(self):
        error = subprocess.TimeoutExpired(self.argv, 15,
            output=b"synthetic-private-output", stderr=b"synthetic-private-error")
        with patch.object(probe, "_run", side_effect=error) as run:
            with self.assertRaises(subprocess.TimeoutExpired) as raised:
                probe._observed_run(self.argv, **self.options)
        self.assertIs(error, raised.exception)
        self.assertEqual(1, run.call_count)
        self.assertEqual("timeout", self.events[0]["result"])
        self.assertNotIn("synthetic-private", json.dumps(self.events))

    def test_launch_error_is_reraised_with_numeric_code_only(self):
        error = OSError(13, "synthetic-private-error", "synthetic-private-path")
        with patch.object(probe, "_run", side_effect=error) as run:
            with self.assertRaises(OSError) as raised:
                probe._observed_run(self.argv, **self.options)
        self.assertIs(error, raised.exception)
        self.assertEqual(1, run.call_count)
        self.assertEqual("launch-error", self.events[0]["result"])
        self.assertEqual(13, self.events[0]["errno"])
        self.assertNotIn("synthetic-private", json.dumps(self.events))

    def test_unrelated_processes_are_not_observed(self):
        with patch.object(probe, "_run", return_value="unchanged") as run:
            self.assertEqual("unchanged", probe._observed_run(["python", "script.py"]))
            self.assertEqual("unchanged", probe._observed_run(self.argv, timeout=15))
        self.assertEqual(2, run.call_count)
        self.assertEqual([], self.events)
