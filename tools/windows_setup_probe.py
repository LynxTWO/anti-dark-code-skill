"""Temporary CI observer for intermittent Windows ledger setup failures.

Observe the real subprocess call without retries or changing its arguments.
Only fixed classifications, durations and return codes leave the test process.
"""
from collections import Counter
import json
import subprocess
import time


_run = subprocess.run
_events = []


def _observed_run(args, *positional, **kwargs):
    env = kwargs.get("env", {})
    if (not isinstance(args, list) or not args
            or not str(args[0]).lower().endswith("powershell.exe")
            or "-NoLogo" not in args or kwargs.get("timeout") != 15
            or "ADC_PRIVACY_CHECK_PATH" not in env):
        return _run(args, *positional, **kwargs)
    script = args[-1]
    operation = ("stage" if "DirectorySecurity" in script else
                 "file-owner" if "$acl.SetOwner" in script else "check")
    event = {"operation": operation}
    start = time.monotonic()
    try:
        result = _run(args, *positional, **kwargs)
        event["returncode"] = result.returncode
        event["result"] = ("private" if result.returncode == 0 and
                           result.stdout.strip() == b"private" else "refused")
        # All values come from an allowlist. Never retain raw child output.
        error = result.stderr.decode("utf-8", errors="replace")
        event["error_types"] = [kind for kind in (
            "UnauthorizedAccessException", "CommandNotFoundException",
            "FileNotFoundException", "FileLoadException", "IOException",
            "OutOfMemoryException", "SecurityException", "PSInvalidOperationException",
        ) if kind in error]
        event["stderr_present"] = bool(result.stderr)
        event["stdout_class"] = ("private" if result.stdout.strip() == b"private" else
                                 "unverified" if result.stdout.strip() == b"unverified" else
                                 "empty" if not result.stdout.strip() else "other")
        return result
    except subprocess.TimeoutExpired:
        event["result"] = "timeout"
        raise
    except OSError as error:
        event["result"] = "launch-error"
        event["errno"] = error.errno
        event["winerror"] = getattr(error, "winerror", None)
        raise
    finally:
        event["seconds"] = round(time.monotonic() - start, 3)
        _events.append(event)


def pytest_configure(config):
    subprocess.run = _observed_run


def pytest_sessionfinish(session, exitstatus):
    subprocess.run = _run
    if hasattr(session.config, "workeroutput"):
        session.config.workeroutput["windows_setup_probe"] = _events


def pytest_testnodedown(node, error):
    _events.extend(node.workeroutput.get("windows_setup_probe", []))


def pytest_terminal_summary(terminalreporter):
    counts = Counter((event["operation"], event["result"]) for event in _events)
    report = {
        "calls": len(_events),
        "counts": [{"operation": op, "result": result, "count": count}
                   for (op, result), count in sorted(counts.items())],
        "slowest": sorted(_events, key=lambda event: event["seconds"], reverse=True)[:12],
        "refusals": [event for event in _events if event["result"] != "private"][:30],
    }
    terminalreporter.write_sep("=", "Windows setup diagnostics (no child output or paths)")
    terminalreporter.write_line(json.dumps(report, sort_keys=True))
