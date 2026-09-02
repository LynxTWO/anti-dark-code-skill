#!/usr/bin/env python3
"""Replay the router mutation matrix.

The previous matrix stored a name, a verdict, and a pytest line. That is a
claim, not a record: reproducing it meant guessing the transformation from the
name, which is what a reviewer had to do and what made the claim unverifiable.

Each row here carries the exact source path, the text replaced, and the
replacement. This script applies one row at a time against a restored source,
runs the router suite, and reports whether the mutant was caught.

Usage, from the repository root:

    python design/routing/mutants/replay.py            # replay every row
    python design/routing/mutants/replay.py M07 M33    # replay named rows
    python design/routing/mutants/replay.py --write    # replay and rewrite verdicts

A mutant is caught when the suite fails. A mutant that survives is a finding:
it names a guarantee the code claims and the tests do not hold it to.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

MATRIX = Path(__file__).with_name("matrix.json")
OUTCOME_PLUGIN_MODULE = "design.routing.mutants.exact_nodeid_plugin"


def host_identity() -> dict:
    """Facts that change what a replay can observe.

    A mutant attacking symlink handling survives on a host that cannot create
    symlinks, because the test skips. That is a fact about the host, not about
    the code, and one unqualified verdict cannot carry both it and the answer
    from a host that can. Every result records where it came from.
    """
    try:
        git = subprocess.run(["git", "--version"], capture_output=True,
                             text=True).stdout.strip()
    except OSError:
        git = "unknown"
    return {
        "platform": platform.system(),
        "release": platform.release(),
        "python": platform.python_version(),
        "git": git,
    }
REPO_ROOT = Path(__file__).resolve().parents[3]
# The router file by default. A row may name its own suite, because a mutant
# in one module proves nothing when the tests that hold it are never run, and
# replaying every module for every row costs minutes per mutant to learn that.
DEFAULT_SUITE = ("anti-dark-code/tests/test_route.py",)
# A worker runs its suite one directory above the owned clone root. Some real
# tests deliberately launch detached helpers; inheriting a clone cwd would
# leave a live handle that prevents the coordinator from proving clone cleanup.
_WORKER_SUITE_CWD: Path | None = None
_WORKER_TEMP_ROOT: Path | None = None


# The matrix integrity tests compare the tree against the matrix, and during a
# replay the tree is deliberately wrong. They are deselected rather than
# skipped: a skip counts toward the per-host skip total, and that total decides
# whether an uncaught row reads as SURVIVED or as "nobody could check this". A
# guard that always skips would have quietly relabelled every real survivor.
INTEGRITY_FILTER = "not MutationMatrixIntegrity"
PYTEST_OUTCOME = (
    r"\d+ (?:failed|passed|skipped|deselected|xfailed|xpassed|warnings?|"
    r"errors?|subtests passed)"
)
PYTEST_SUMMARY = re.compile(
    rf"^{PYTEST_OUTCOME}(?:, {PYTEST_OUTCOME})* in \d+(?:\.\d+)?s"
    r"(?: \(\d+:(?:[0-5]\d):(?:[0-5]\d)\))?$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def suite_command(paths) -> list[str]:
    return [sys.executable, "-m", "pytest", "-p", OUTCOME_PLUGIN_MODULE,
            *paths, "-q", "-k", INTEGRITY_FILTER]


class SuiteBroken(RuntimeError):
    """The suite did not run, so the mutant proved nothing either way."""


class SuiteOutcome(tuple):
    """Backward-compatible pytest tuple with exact failed/skip identities."""

    def __new__(cls, exit_code: int, summary: str, skipped: int,
                failed_nodeids=(), skipped_nodeids=()):
        outcome = super().__new__(cls, (exit_code, summary, skipped))
        outcome.failed_nodeids = tuple(failed_nodeids)
        outcome.skipped_nodeids = tuple(skipped_nodeids)
        return outcome


def sha256_bytes(contents: bytes) -> str:
    """Return the exact byte digest used to prove mutation restoration."""
    return hashlib.sha256(contents).hexdigest()


def commit_identity(repo_root: Path) -> str:
    """Record the committed source that a row exercised."""
    try:
        done = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True,
            text=True, check=False)
    except OSError:
        return "unknown"
    return done.stdout.strip() if done.returncode == 0 else "unknown"


def worktree_status(repo_root: Path) -> tuple[str, ...]:
    """Return exact porcelain rows or refuse an unreadable repository."""
    try:
        done = subprocess.run(
            ["git", "status", "--porcelain=v1"], cwd=repo_root,
            capture_output=True, check=False)
    except OSError as caught:
        raise RuntimeError(f"git status could not start: {caught}") from caught
    if done.returncode:
        raise RuntimeError("git status failed: the worktree is not a readable repository")
    return tuple(line for line in
                 done.stdout.decode("utf-8", "replace").splitlines()
                 if line.strip())


def _summary_is_anchored(summary: str) -> bool:
    return PYTEST_SUMMARY.fullmatch(summary) is not None


def _skipped_from_summary(summary: str) -> int:
    """Extract the reported skip count only from an anchored pytest summary."""
    for index, token in enumerate(summary.split()):
        if token.startswith("skipped") and index:
            try:
                return int(summary.split()[index - 1])
            except ValueError:
                return 0
    return 0


def _exact_outcomes(contents: str | None, exit_code: int,
                    skipped: int) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Read and validate the tracked plugin's exact per-node outcome record."""
    try:
        payload = json.loads(contents) if contents is not None else None
    except (TypeError, json.JSONDecodeError) as caught:
        raise SuiteBroken(f"pytest exact outcome evidence is unreadable: {caught}") from caught
    if not isinstance(payload, dict):
        raise SuiteBroken("pytest exact outcome evidence is unreadable")
    collected = payload.get("collect_nodeids")
    outcomes = payload.get("outcomes")
    if payload.get("exitstatus") != exit_code or not isinstance(collected, list) or \
            not all(isinstance(nodeid, str) for nodeid in collected) or \
            len(collected) != len(set(collected)) or not isinstance(outcomes, dict) or \
            set(outcomes) != set(collected) or not all(
                outcome in {"passed", "failed", "error", "skipped", "missing"}
                for outcome in outcomes.values()):
        raise SuiteBroken("pytest exact outcome evidence does not match the suite")
    if payload.get("missing"):
        raise SuiteBroken("pytest exact outcome evidence has missing test reports")
    failed_nodeids = tuple(
        nodeid for nodeid in collected if outcomes[nodeid] in {"failed", "error"})
    skipped_nodeids = tuple(
        nodeid for nodeid in collected if outcomes[nodeid] == "skipped")
    if len(skipped_nodeids) != skipped:
        raise SuiteBroken("pytest exact skipped identities do not match its summary")
    return failed_nodeids, skipped_nodeids


def run_suite(paths=DEFAULT_SUITE, repo_root: Path = REPO_ROOT) -> SuiteOutcome:
    """Return the pytest exit, exact summary line, and skipped count.

    A mutant is caught when tests fail. It is not caught when they pass. A
    suite that could not collect, crashed, or was interrupted says nothing
    about the mutant, and treating that as either verdict would put a false
    row in the record. Those raise instead.
    """
    execution_cwd = _WORKER_SUITE_CWD or repo_root
    command_paths = paths
    environment = dict(os.environ)
    if _WORKER_SUITE_CWD is not None:
        command_paths = tuple(
            str(path if Path(path).is_absolute() else repo_root / path)
            for path in paths)
    command = suite_command(command_paths)
    if _WORKER_SUITE_CWD is not None:
        # Without an explicit rootdir, pytest takes the common ancestor of the
        # invocation directory and the absolute suite path. A coordinator that
        # lives beneath the host temp directory then puts the machine-wide temp
        # directory at the top of the collection tree, and collection dies the
        # moment any other process removes a temp entry mid-scan. Measured on
        # this host: 59 rows inconclusive in one run, each "FileNotFoundError
        # ... J:\TEMP\tmpXXXX", pytest exit 2, while a serial replay ran in
        # another clone. The clone is the only directory a worker owns, so it
        # is the only acceptable root. See D-098.
        command.append(f"--rootdir={repo_root}")
        # A rootdir contains conftest discovery, not pytest's environment or
        # Python import path. Measured before D-101: PYTEST_ADDOPTS loaded a
        # plugin from the coordinator through PYTHONPATH while the clone-owned
        # suite passed. Workers accept only their explicit command and frozen
        # clone, so caller plugin controls and import paths do not cross this
        # boundary.
    for name in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTEST_DEBUG",
                 "PYTHONPATH"):
        environment.pop(name, None)
    for name in ("PYTHONUSERBASE", "PYTHONSTARTUP", "PYTHONHOME",
                 "PYTHONEXECUTABLE", "PYTHONINSPECT"):
        environment.pop(name, None)
    # Flags that change what a test means rather than where code comes from.
    # Measured after D-105, through this function: PYTHONWARNINGS=error turned
    # a passing probe into a failure, and PYTHONOPTIMIZE=2 stripped an
    # assertion. A surviving mutant recorded as caught because the host set a
    # warning filter is the D-095 class again. See D-111.
    for name in ("PYTHONWARNINGS", "PYTHONOPTIMIZE", "PYTHONBREAKPOINT",
                 "PYTHONPYCACHEPREFIX", "PYTHONDEBUG", "PYTHONDEVMODE",
                 "PYTHONPROFILEIMPORTTIME", "PYTHONTRACEMALLOC",
                 "PYTHONFAULTHANDLER", "PYTHONMALLOC", "PYTHONASYNCIODEBUG",
                 "PYTHONINTMAXSTRDIGITS", "PYTHONNODEBUGRANGES",
                 "PYTHONPLATLIBDIR", "PYTHONCASEOK", "PYTHONHASHSEED",
                 "PYTHONVERBOSE", "PYTHONPERFSUPPORT"):
        environment.pop(name, None)
    # The suite's own fixtures run git with this environment. Measured after
    # D-105: a GIT_CONFIG_GLOBAL file carrying core.hooksPath ran a hook from
    # outside the clone during a fixture-shaped commit, and a host's global
    # git-lfs driver decided M08's verdict on three hosts while a host without
    # one saw the mutant survive. The worker's git reads only configuration
    # this run wrote; the file, template, and XDG directories are created
    # below, beside the pinned pytest configuration. See D-112.
    for name in [key for key in environment
                 if key.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_"))] + [
            "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG",
            "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
            "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
            "GIT_CEILING_DIRECTORIES", "GIT_NAMESPACE", "GIT_EXEC_PATH",
            "GIT_SSH", "GIT_SSH_COMMAND", "GIT_ASKPASS", "GIT_EDITOR",
            "GIT_SEQUENCE_EDITOR", "GIT_PAGER", "GIT_PROXY_COMMAND",
            "GIT_EXTERNAL_DIFF", "GIT_DIFF_OPTS"]:
        environment.pop(name, None)
    # The interpreter runs site initialization before pytest reads one option.
    # Measured after D-101: a caller's PYTHONUSERBASE pointed the worker at a
    # user site-packages whose usercustomize.py and .pth import line both ran
    # inside the suite while it reported "1 passed". No user site at all is
    # the only boundary that does not depend on which files exist there.
    # See D-105.
    environment.update({"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
                        "PYTHONNOUSERSITE": "1",
                        "PYTHONSAFEPATH": "1",
                        "PYTHONPATH": str(repo_root)})
    if _WORKER_TEMP_ROOT is not None:
        pytest_root = _WORKER_TEMP_ROOT / "pytest"
        command.append(f"--basetemp={pytest_root}")
        environment.update({"TMP": str(_WORKER_TEMP_ROOT),
                            "TEMP": str(_WORKER_TEMP_ROOT),
                            "TMPDIR": str(_WORKER_TEMP_ROOT)})
    if _WORKER_SUITE_CWD is None:
        # Serial replay runs from the repository root with relative paths, so
        # its rootdir was already the root by inference. It is pinned here so
        # the configuration pin below cannot move it, and node ids keep the
        # same rootdir-relative spelling on every host and in both modes.
        command.append("--rootdir=" + str(repo_root))
    with tempfile.TemporaryDirectory(
            prefix="adc-pytest-outcomes-", dir=_WORKER_TEMP_ROOT) as raw_outcomes:
        # pytest searches for pytest.ini, tox.ini, setup.cfg and pyproject.toml
        # from the common ancestor of the invocation directory and the
        # arguments upward, and a rootdir does not stop that search. For a
        # worker that ancestor is the host temp directory; for serial replay
        # it is every parent of the repository. Measured after D-101: an
        # ancestor pytest.ini's addopts reached the worker and turned its row
        # inconclusive. An empty configuration file owned by this run ends the
        # search. See D-105.
        pinned_config = Path(raw_outcomes) / "pytest.ini"
        pinned_config.write_text("[pytest]\n", encoding="utf-8")
        command.extend(["-c", str(pinned_config)])
        # D-112: every git the suite runs reads this empty global file, no
        # system file, no system attributes, an empty template directory, and
        # an XDG directory that holds no attributes or ignore file.
        git_config = Path(raw_outcomes) / "gitconfig"
        git_config.write_text("", encoding="utf-8")
        git_template = Path(raw_outcomes) / "git-template"
        git_template.mkdir()
        xdg_home = Path(raw_outcomes) / "xdg"
        (xdg_home / "git").mkdir(parents=True)
        environment.update({"GIT_CONFIG_GLOBAL": str(git_config),
                            "GIT_CONFIG_NOSYSTEM": "1",
                            "GIT_ATTR_NOSYSTEM": "1",
                            "GIT_TEMPLATE_DIR": str(git_template),
                            "XDG_CONFIG_HOME": str(xdg_home)})
        outcome_target = Path(raw_outcomes) / "outcomes.json"
        environment["ADC_EVIDENCE_OUTCOMES"] = str(outcome_target)
        done = subprocess.run(command, cwd=execution_cwd, env=environment,
                              capture_output=True, text=True)
        try:
            outcome_contents = outcome_target.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            outcome_contents = None
    tail = (done.stdout or done.stderr).strip().splitlines()
    summary = tail[-1] if tail else "no output"
    diagnostic = ((done.stdout or "") + (done.stderr or "")).strip()
    diagnostic = diagnostic.replace(str(repo_root), "<repo>")[-4000:]
    if not _summary_is_anchored(summary):
        raise SuiteBroken(
            f"pytest produced no test summary (exit {done.returncode}): {summary}; "
            f"output: {diagnostic}")
    # pytest exit codes are exact, and text is not. A collection error, an
    # internal error, or no tests collected all print something that reads like
    # a result, and an earlier version of this check read a syntax error as a
    # caught mutant. 1 means tests failed, 0 means they passed, everything else
    # means the suite did not answer the question.
    # A skip means the host could not exercise the guarantee, which is a fact
    # about the host and not about the mutant.
    skipped = _skipped_from_summary(summary)
    if done.returncode not in (0, 1):
        raise SuiteBroken(f"pytest exit {done.returncode}: {summary}; output: {diagnostic}")
    failed_nodeids, skipped_nodeids = _exact_outcomes(
        outcome_contents, done.returncode, skipped)
    return SuiteOutcome(done.returncode, summary, skipped,
                        failed_nodeids, skipped_nodeids)


def _row_evidence(row: dict, host: dict, worker: str, commit: str,
                  started: float, before: str | None = None) -> dict:
    """Start a JSON-compatible result before a row can mutate a source."""
    return {
        "id": row["id"], "status": "inconclusive", "verdict": "INCONCLUSIVE",
        "caught": None, "exit_code": None, "pytest": None, "skipped": 0,
        "failed_nodeids": [], "skipped_nodeids": [],
        "source_hash_before": before, "source_hash_after": before,
        "source_after_state": "unknown",
        "restored": False, "commit": commit, "worker": worker,
        "host": host, "duration": 0.0,
    }


def run_row(repo_root: Path, row: dict, host: dict, worker: str) -> dict:
    """Run exactly one row, restoring its raw source bytes before returning."""
    started = time.perf_counter()
    commit = commit_identity(repo_root)
    source = repo_root / row["source"]
    original = source.read_bytes()
    before = sha256_bytes(original)
    result = _row_evidence(row, host, worker, commit, started, before)
    old = row["old"].encode("utf-8")
    new = row["new"].encode("utf-8")
    target_count = original.count(old)
    if target_count != 1:
        result["status"] = "target-missing" if target_count == 0 else "target-ambiguous"
        result["error"] = f"target occurs {target_count} times"
        result["source_hash_after"] = before
        result["restored"] = True
        result["duration"] = time.perf_counter() - started
        return result

    try:
        source.write_bytes(original.replace(old, new, 1))
        try:
            suite_outcome = run_suite(
                tuple(row.get("suite", DEFAULT_SUITE)), repo_root)
            exit_code, summary, skipped = suite_outcome
            result["pytest"] = summary
            result["skipped"] = skipped
            result["failed_nodeids"] = list(
                getattr(suite_outcome, "failed_nodeids", ()))
            result["skipped_nodeids"] = list(
                getattr(suite_outcome, "skipped_nodeids", ()))
            result["exit_code"] = exit_code
            if not PYTEST_SUMMARY.fullmatch(summary):
                raise SuiteBroken(
                    f"pytest produced no test summary (exit {exit_code}): {summary}")
            if exit_code not in (0, 1):
                raise SuiteBroken(f"pytest exit {exit_code}: {summary}")
            result["status"] = "completed"
            result["caught"] = exit_code == 1
            result["verdict"] = "caught" if result["caught"] else "SURVIVED"
        except SuiteBroken as broken:
            result["error"] = str(broken)
    except BaseException:
        # KeyboardInterrupt and SystemExit derive from BaseException. The
        # finally block restores the source before this interruption escapes.
        raise
    finally:
        restore_error: OSError | None = None
        after_error: OSError | None = None
        try:
            source.write_bytes(original)
        except OSError as caught:
            restore_error = caught
        try:
            after = sha256_bytes(source.read_bytes())
            result["source_hash_after"] = after
            result["source_after_state"] = "readable"
        except OSError as caught:
            after = None
            after_error = caught
            result["source_hash_after"] = None
            result["source_after_state"] = "unreadable"
        result["restored"] = (
            restore_error is None and after_error is None and after == before)
        result["duration"] = time.perf_counter() - started
        if not result["restored"]:
            errors = [result["error"]] if "error" in result else []
            if restore_error is not None:
                errors.append(f"source restoration write failed: {restore_error}")
            if after_error is not None:
                errors.append(f"source unreadable after restoration: {after_error}")
            if after is not None and after != before:
                errors.append("source restoration hash mismatch")
            result.update({
                "status": "inconclusive", "verdict": "INCONCLUSIVE",
                "caught": None,
                "error": "; ".join(errors),
            })
    return result


def _superseded_result(row: dict, repo_root: Path, host: dict,
                       commit: str) -> dict:
    """The one canonical record shape for a matrix-superseded mutation."""
    source = repo_root / row["source"]
    digest = sha256_bytes(source.read_bytes()) if source.is_file() else None
    result = _row_evidence(row, host, "serial", commit,
                           time.perf_counter(), digest)
    result.update({"status": "superseded", "verdict": "superseded",
                   "source_hash_after": digest, "restored": True})
    return result


def run_serial(rows: list[dict], repo_root: Path) -> list[dict]:
    """Execute rows in canonical matrix order on the one authoritative tree."""
    host = host_identity()
    commit = commit_identity(repo_root)
    results: list[dict] = []
    for row in rows:
        if row.get("superseded_by"):
            results.append(_superseded_result(row, repo_root, host, commit))
            continue
        results.append(run_row(repo_root, row, host, "serial"))
    return results


def partition_rows(rows: list[dict], workers: int) -> list[list[tuple[int, dict]]]:
    """Assign rows round-robin while retaining their canonical matrix index."""
    if workers < 1:
        raise ValueError("workers must be positive")
    partitions: list[list[tuple[int, dict]]] = [[] for _ in range(workers)]
    for index, row in enumerate(rows):
        partitions[index % workers].append((index, row))
    return partitions


def _strict_child(path: Path, parent: Path) -> bool:
    """Whether resolved *path* is below, rather than equal to, *parent*."""
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return path != parent


def _blob_at_commit(repo_root: Path, commit: str, relative: Path) -> bytes:
    """Read one committed blob without letting a path reach a shell."""
    done = subprocess.run(
        ["git", "cat-file", "blob", f"{commit}:{relative.as_posix()}"],
        cwd=repo_root, capture_output=True, check=False)
    if done.returncode:
        raise RuntimeError(f"committed blob could not be read: {relative.as_posix()}")
    return done.stdout


def _verify_working_sources(repo_root: Path, commit: str,
                            relatives: set[Path]) -> None:
    """Reject a coordinator or clone whose mutable bytes differ from HEAD."""
    root = repo_root.resolve(strict=True)
    for relative in sorted(relatives, key=lambda item: item.as_posix()):
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError("mutable source is not a safe relative path")
        try:
            target = (root / relative).resolve(strict=True)
        except OSError as caught:
            raise RuntimeError(
                f"mutable source is unresolved: {relative.as_posix()}") from caught
        if not _strict_child(target, root):
            raise RuntimeError("mutable source escapes its repository")
        if target.read_bytes() != _blob_at_commit(root, commit, relative):
            raise RuntimeError(
                f"mutable source differs from frozen commit: {relative.as_posix()}")


def _active_matrix_sources(matrix_path: Path) -> set[Path]:
    """Return the distinct active mutation targets, rejecting unsafe entries."""
    try:
        rows = json.loads(matrix_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as caught:
        raise RuntimeError(f"matrix could not be read: {caught}") from caught
    if not isinstance(rows, list):
        raise RuntimeError("matrix is not a list")
    sources: set[Path] = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("superseded_by"):
            continue
        raw_source = row.get("source")
        if not isinstance(raw_source, str):
            raise RuntimeError("matrix active row has no source")
        source = Path(raw_source)
        if source.is_absolute() or ".." in source.parts:
            raise RuntimeError("matrix source is not a safe relative path")
        sources.add(source)
    return sources


def _verify_clean_worktree(repo_root: Path) -> None:
    """Refuse a coordinator whose working tree is not exactly its HEAD.

    Every clone is built from the committed HEAD, so a parallel verdict
    describes the commit. The serial path replays whatever is on disk. On a
    clean tree those are one tree, which is what the round-sixteen identity
    comparison measured. On a dirty tree they are two, and nothing in either
    report says which one a verdict describes. Measured: with one uncommitted
    edit that removed the only test holding M57, the serial replay reported
    SURVIVED here and the parallel replay reported caught, both exit 0. The
    frozen-source check in _verify_coordinator_sources catches a dirty
    mutation target; it cannot see a dirty suite, policy, or fixture, and the
    suite reads all of them. Fail closed on any difference, untracked files
    included, because an untracked conftest.py changes the suite as surely as
    a tracked edit. See D-096.
    """
    dirty = worktree_status(repo_root)
    if dirty:
        raise RuntimeError(
            f"working tree differs from HEAD in {len(dirty)} path(s); commit or "
            "remove them before a parallel replay, whose clones are built from HEAD")


def _verify_coordinator_sources(repo_root: Path, commit: str) -> None:
    """Freeze the coordinator bytes before it creates any clone or worker."""
    _verify_clean_worktree(repo_root)
    try:
        matrix_relative = MATRIX.resolve().relative_to(REPO_ROOT.resolve())
        replay_relative = Path(__file__).resolve().relative_to(REPO_ROOT.resolve())
        plugin_relative = Path(__file__).with_name(
            "exact_nodeid_plugin.py").resolve().relative_to(REPO_ROOT.resolve())
    except ValueError as caught:
        raise RuntimeError("replay authority paths are outside the coordinator") from caught
    matrix_path = repo_root / matrix_relative
    _verify_working_sources(
        repo_root, commit, {matrix_relative, replay_relative, plugin_relative})
    _verify_working_sources(
        repo_root, commit, _active_matrix_sources(matrix_path))


def _frozen_row_source_hashes(repo_root: Path, commit: str,
                              rows: list[dict]) -> dict[Path, str]:
    """Cache each replay target's SHA-256 from its frozen committed blob."""
    digests: dict[Path, str] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("source"), str):
            raise RuntimeError("parallel row has no source")
        source = Path(row["source"])
        if source.is_absolute() or ".." in source.parts:
            raise RuntimeError("parallel row source is not a safe relative path")
        if source not in digests:
            digests[source] = sha256_bytes(_blob_at_commit(repo_root, commit, source))
    return digests


def _verify_active_clone_sources(clone: Path, commit: str) -> None:
    """Fail closed unless every active mutable target is byte-identical to HEAD.

    ``core.autocrlf=false`` prevents host policy from changing ordinary text
    during checkout.  Deliberate ``.gitattributes`` eol rules remain in force;
    if one makes a mutable target differ from its committed blob, this check
    rejects the clone instead of silently overriding the repository's rule.
    """
    try:
        matrix_relative = MATRIX.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError as caught:
        raise RuntimeError("clone matrix path is outside the coordinator") from caught
    matrix_path = clone / matrix_relative
    _verify_working_sources(clone, commit, _active_matrix_sources(matrix_path))


def prepare_clone(source: Path, destination: Path, commit: str) -> None:
    """Create an isolated, detached local clone at precisely ``commit``."""
    source = source.resolve(strict=True)
    destination = destination.resolve(strict=False)
    if destination.exists():
        raise RuntimeError(f"clone destination already exists: {destination.name}")
    if not destination.parent.is_dir():
        destination.parent.mkdir(parents=True, exist_ok=False)
    try:
        cloned = subprocess.run(
            ["git", "-c", "core.autocrlf=false", "clone", "--no-hardlinks",
             str(source), str(destination)],
            capture_output=True, text=True, check=False)
    except OSError as caught:
        raise RuntimeError(f"git clone could not start: {caught}") from caught
    if cloned.returncode:
        raise RuntimeError(f"git clone failed: {cloned.stderr.strip()}")
    try:
        detached = subprocess.run(
            ["git", "-c", "core.autocrlf=false", "checkout", "--detach", commit], cwd=destination,
            capture_output=True, text=True, check=False)
    except OSError as caught:
        raise RuntimeError(f"git checkout could not start: {caught}") from caught
    if detached.returncode:
        raise RuntimeError(f"git checkout failed: {detached.stderr.strip()}")
    actual = commit_identity(destination)
    if actual != commit:
        raise RuntimeError(f"clone HEAD mismatch: expected {commit}, got {actual}")
    _verify_active_clone_sources(destination, commit)


def run_clone_partition(clone: Path, indexed_rows: list[tuple[int, dict]],
                        worker: str) -> list[dict]:
    """Run one owned partition sequentially, retiring on restoration doubt."""
    global _WORKER_SUITE_CWD, _WORKER_TEMP_ROOT
    host = host_identity()
    results: list[dict] = []
    retired = False
    previous_cwd = _WORKER_SUITE_CWD
    previous_temp_root = _WORKER_TEMP_ROOT
    _WORKER_SUITE_CWD = REPO_ROOT
    _WORKER_TEMP_ROOT = clone.parent / f"{clone.name}-pytest"
    _WORKER_TEMP_ROOT.mkdir(parents=True, exist_ok=False)
    try:
        for index, row in indexed_rows:
            if retired:
                break
            result = run_row(clone, row, host, worker)
            result["matrix_index"] = index
            result["clone_retired"] = not result.get("restored", False)
            results.append(result)
            retired = result["clone_retired"]
    finally:
        _WORKER_SUITE_CWD = previous_cwd
        _WORKER_TEMP_ROOT = previous_temp_root
    return results


def _cleanup_clone(owned_root: Path, target: Path, worker: str,
                   repo_root: Path) -> dict:
    """Remove only a resolved child clone and return path-safe evidence."""
    record = {"worker": worker, "clone": "<unresolved>",
              "removed": False, "error": None}
    try:
        root = owned_root.resolve(strict=True)
    except OSError as caught:
        record["error"] = f"owned temp root unresolved ({type(caught).__name__})"
        return record
    try:
        resolved = target.resolve(strict=True)
    except OSError as caught:
        record["error"] = f"clone target unresolved ({type(caught).__name__})"
        return record
    if _strict_child(resolved, root):
        record["clone"] = resolved.relative_to(root).as_posix()
    else:
        record["clone"] = "<outside-owned-root>"
    try:
        workspace = repo_root.resolve(strict=True)
        home = Path.home().resolve(strict=True)
    except OSError as caught:
        record["error"] = f"safety boundary unresolved ({type(caught).__name__})"
        return record
    if not _strict_child(resolved, root):
        record["error"] = "cleanup target is not a strict child of owned temp root"
        return record
    if resolved in (root, workspace, home):
        record["error"] = "cleanup target is a protected directory"
        return record
    try:
        shutil.rmtree(resolved)
    except OSError as caught:
        code = getattr(caught, "winerror", None)
        suffix = f" WinError {code}" if code is not None else ""
        record["error"] = f"clone removal failed ({type(caught).__name__}{suffix})"
        return record
    if resolved.exists():
        record["error"] = "clone removal did not remove target"
        return record
    record["removed"] = True
    return record


def _parallel_inconclusive(row: dict, index: int, worker: str, commit: str,
                           error: str) -> dict:
    """Create one canonical placeholder when parallel evidence is incomplete."""
    result = _row_evidence(row, host_identity(), worker, commit,
                           time.perf_counter())
    result.update({"matrix_index": index, "clone_retired": True,
                   "error": error})
    return result


def _parallel_error(prefix: str, caught: BaseException, owned_root: Path) -> str:
    """Retain failure text without exposing an operator-specific temp path."""
    detail = str(caught).replace(str(owned_root), "<owned-temp>")
    return f"{prefix}: {detail}"


def _terminal_safe_diagnostic(value: str, limit: int = 2000) -> str:
    """Render untrusted text as one bounded line without terminal controls."""
    rendered: list[str] = []
    remaining = limit
    for character in value:
        category = unicodedata.category(character)
        token = (character.encode("unicode_escape").decode("ascii")
                 if category in {"Cc", "Cf", "Zl", "Zp"} else character)
        if len(token) > remaining:
            break
        rendered.append(token)
        remaining -= len(token)
        if remaining == 0:
            break
    return "".join(rendered)


WORKER_RESULT_FIELDS = frozenset({
    "id", "status", "verdict", "caught", "exit_code", "pytest", "skipped",
    "failed_nodeids", "skipped_nodeids",
    "source_hash_before", "source_hash_after", "source_after_state", "restored",
    "commit", "worker", "host", "duration", "matrix_index", "clone_retired",
})


def _validate_worker_result(item: object, index: int, row: dict,
                            worker: str, commit: str,
                            expected_source_digest: str) -> str | None:
    """Validate one untrusted, JSON-compatible worker payload at the boundary."""
    if not isinstance(item, dict):
        return "worker returned a non-object result"
    try:
        json.dumps(item, allow_nan=False)
    except (TypeError, ValueError):
        return "worker result is not JSON-compatible"
    if item.get("status") != "completed" and isinstance(item.get("error"), str):
        # A worker row that could not become evidence carries its own reason:
        # a suite that did not answer, a target that did not match, a source
        # that did not restore. The schema check below would replace that
        # reason with a sentence about field names, which is what the first
        # round-seventeen parallel run reported for 59 rows whose real error
        # was a collection failure. The row stays inconclusive either way;
        # the reason is what a reader needs. See D-099.
        return (f"worker row {item.get('status')}: "
                f"{_terminal_safe_diagnostic(item['error'])}")
    if set(item) != WORKER_RESULT_FIELDS:
        return "worker result schema does not match the required evidence fields"
    if item["matrix_index"] != index or isinstance(item["matrix_index"], bool):
        return "worker result matrix index does not match its partition"
    if item["id"] != row["id"]:
        return "worker result id does not match matrix index"
    if item["worker"] != worker:
        return "worker result worker does not match its partition"
    if item["commit"] != commit:
        return "worker result commit does not match frozen coordinator commit"
    if item["status"] != "completed":
        return "worker result status is not completed"
    exit_code = item["exit_code"]
    if type(exit_code) is not int or exit_code not in (0, 1):
        return "worker result has an invalid pytest exit code"
    caught = item["caught"]
    verdict = item["verdict"]
    if type(caught) is not bool or caught != (exit_code == 1):
        return "worker result caught flag is incompatible with pytest exit code"
    if verdict != ("caught" if exit_code == 1 else "SURVIVED"):
        return "worker result verdict is incompatible with pytest exit code"
    summary = item["pytest"]
    if not isinstance(summary, str) or not _summary_is_anchored(summary):
        return "worker result pytest summary is not anchored"
    if type(item["skipped"]) is not int or item["skipped"] < 0 or \
            item["skipped"] != _skipped_from_summary(summary):
        return "worker result skip count is incompatible with pytest summary"
    for field in ("failed_nodeids", "skipped_nodeids"):
        nodeids = item[field]
        if not isinstance(nodeids, list) or \
                not all(isinstance(nodeid, str) and nodeid for nodeid in nodeids) or \
                len(nodeids) != len(set(nodeids)):
            return f"worker result {field} are not exact unique node ids"
    if len(item["skipped_nodeids"]) != item["skipped"]:
        return "worker result skipped node ids do not match the skip count"
    before = item["source_hash_before"]
    after = item["source_hash_after"]
    if not isinstance(before, str) or not SHA256.fullmatch(before) or \
            not isinstance(after, str) or not SHA256.fullmatch(after) or after != before:
        return "worker result restoration hashes are not equal SHA-256 evidence"
    if before != expected_source_digest:
        return "worker result hashes do not match frozen source digest"
    if item["restored"] is not True or item["source_after_state"] != "readable":
        return "worker result does not prove source restoration"
    if item["clone_retired"] is not False:
        return "worker result incorrectly reports a retired clone"
    if not isinstance(item["host"], dict) or set(item["host"]) != {
            "platform", "release", "python", "git"} or \
            not all(isinstance(value, str) for value in item["host"].values()):
        return "worker result host evidence is invalid"
    if type(item["duration"]) not in (int, float) or item["duration"] < 0:
        return "worker result duration is invalid"
    return None


def _cleanup_failure(worker: str, label: str, caught: BaseException) -> dict:
    return {"worker": worker, "clone": label, "removed": False,
            "error": f"cleanup attempt raised {type(caught).__name__}"}


def _cleanup_parallel_resources(
        owned_root: Path, clones: list[tuple[str, Path, list[tuple[int, dict]]]],
        repo_root: Path) -> tuple[list[dict], bool, str | None]:
    """Attempt every contained clone and auxiliary root after executor exit."""
    cleanup: list[dict] = []
    for worker, clone, _ in clones:
        try:
            record = _cleanup_clone(owned_root, clone, worker, repo_root)
        except BaseException as caught:
            record = _cleanup_failure(worker, "<cleanup-raised>", caught)
        auxiliary = clone.parent / f"{clone.name}-pytest"
        record["auxiliary"] = auxiliary.name
        record["auxiliary_removed"] = True
        record["auxiliary_error"] = None
        try:
            auxiliary_exists = auxiliary.exists()
        except OSError as caught:
            auxiliary_exists = True
            record["auxiliary_removed"] = False
            record["auxiliary_error"] = f"auxiliary existence check failed ({type(caught).__name__})"
        if auxiliary_exists:
            try:
                auxiliary_record = _cleanup_clone(
                    owned_root, auxiliary, worker, repo_root)
            except BaseException as caught:
                auxiliary_record = _cleanup_failure(worker, "<cleanup-raised>", caught)
            record["auxiliary"] = auxiliary_record["clone"]
            record["auxiliary_removed"] = auxiliary_record["removed"]
            record["auxiliary_error"] = auxiliary_record["error"]
        cleanup.append(record)
    try:
        root_removed, root_error = _remove_owned_root(owned_root)
    except BaseException as caught:
        root_removed = False
        root_error = f"owned temp root cleanup raised ({type(caught).__name__})"
    for record in cleanup:
        record["owned_root_removed"] = root_removed
        record["owned_root_error"] = root_error
    cleanup.sort(key=lambda item: item["worker"])
    return cleanup, root_removed, root_error


def _remove_owned_root(owned_root: Path) -> tuple[bool, str | None]:
    """Remove only an empty, resolved root after every clone is gone."""
    try:
        root = owned_root.resolve(strict=True)
    except OSError as caught:
        return False, f"owned temp root unresolved ({type(caught).__name__})"
    try:
        root.rmdir()
    except OSError as caught:
        code = getattr(caught, "winerror", None)
        suffix = f" WinError {code}" if code is not None else ""
        return False, f"owned temp root removal failed ({type(caught).__name__}{suffix})"
    return True, None


def run_parallel(rows: list[dict], jobs: int, repo_root: Path) -> tuple[list[dict], list[dict]]:
    """Replay nonempty partitions in process clones and validate every result."""
    if jobs < 1:
        raise ValueError("jobs must be positive")
    repo_root = repo_root.resolve(strict=True)
    if not rows:
        return [], []
    commit = commit_identity(repo_root)
    superseded: dict[int, dict] = {}
    active_rows: list[tuple[int, dict]] = []
    for index, row in enumerate(rows):
        if row.get("superseded_by"):
            superseded[index] = _superseded_result(
                row, repo_root, host_identity(), commit)
        else:
            active_rows.append((index, row))
    partitions: list[list[tuple[int, dict]]] = [[] for _ in range(jobs)]
    for offset, item in enumerate(active_rows):
        partitions[offset % jobs].append(item)
    active = [(index, partition) for index, partition in enumerate(partitions)
              if partition]
    owner = {row_index: f"worker-{worker_index}"
             for worker_index, partition in active for row_index, _ in partition}
    if not active:
        return [superseded[index] for index in range(len(rows))], []
    try:
        _verify_coordinator_sources(repo_root, commit)
        source_digests = _frozen_row_source_hashes(
            repo_root, commit, [row for _, row in active_rows])
    except BaseException as caught:
        error = _parallel_error("coordinator source verification failed", caught, repo_root)
        return ([superseded[index] if index in superseded else
                 _parallel_inconclusive(row, index, owner[index], commit, error)
                 for index, row in enumerate(rows)], [])
    owned_root = Path(tempfile.mkdtemp(prefix="adc-replay-")).resolve(strict=True)
    clones = [(f"worker-{index}", owned_root / f"worker-{index}", partition)
              for index, partition in active]
    future_info: dict[object, tuple[str, Path, list[tuple[int, dict]]]] = {}
    collected: dict[int, dict] = {}
    errors: dict[int, str] = {}
    primary: BaseException | None = None
    cleanup: list[dict] = []
    root_removed = False
    try:
        with ProcessPoolExecutor(max_workers=len(clones)) as executor:
            for worker, clone, partition in clones:
                try:
                    prepare_clone(repo_root, clone, commit)
                    future_info[executor.submit(
                        run_clone_partition, clone, partition, worker)] = (
                            worker, clone, partition)
                except BaseException as caught:
                    for index, _ in partition:
                        errors[index] = _parallel_error(
                            "clone preparation or submission failed", caught, owned_root)
            for future in as_completed(future_info):
                worker, _, partition = future_info[future]
                try:
                    worker_results = future.result()
                except BaseException as caught:
                    for index, _ in partition:
                        errors[index] = _parallel_error(
                            "worker exception", caught, owned_root)
                    continue
                expected_order = [index for index, _ in partition]
                returned_order = [item.get("matrix_index") if isinstance(item, dict)
                                  else None for item in worker_results] if isinstance(worker_results, list) else []
                if len(set(returned_order)) != len(returned_order):
                    for index, _ in partition:
                        errors[index] = "duplicate worker result"
                    continue
                if any(index not in expected_order for index in returned_order):
                    for index, _ in partition:
                        errors[index] = "worker returned an unexpected matrix index"
                    continue
                if returned_order != expected_order:
                    for index, _ in partition:
                        errors[index] = "worker returned matrix indices out of partition order"
                    continue
                for index, row in partition:
                    item = worker_results[expected_order.index(index)]
                    error = _validate_worker_result(
                        item, index, row, worker, commit,
                        source_digests[Path(row["source"])])
                    if error is not None:
                        errors[index] = error
                    elif index in collected:
                        errors[index] = "duplicate worker result"
                    else:
                        collected[index] = item
    except BaseException as caught:
        primary = caught
        for index in owner:
            errors[index] = _parallel_error("parallel executor failed", caught, owned_root)
    finally:
        cleanup, root_removed, _ = _cleanup_parallel_resources(
            owned_root, clones, repo_root)
        failed_workers = {item["worker"] for item in cleanup
                          if not item["removed"] or not item["auxiliary_removed"]}
        for worker, _, partition in clones:
            if worker in failed_workers:
                for index, _ in partition:
                    errors[index] = "clone cleanup was not proven"
        if not root_removed:
            for index in owner:
                errors[index] = "owned temp root cleanup was not proven"
        if commit_identity(repo_root) != commit:
            for index in owner:
                errors[index] = "coordinator HEAD changed during parallel replay"
    results = [superseded[index] if index in superseded else
               collected[index] if index in collected and index not in errors else
               _parallel_inconclusive(row, index, owner[index], commit,
                                      errors.get(index, "missing worker result"))
               for index, row in enumerate(rows)]
    if isinstance(primary, (KeyboardInterrupt, SystemExit)):
        if any(not item["removed"] for item in cleanup):
            primary.add_note("parallel cleanup also failed")
        raise primary
    return results, cleanup


def derive_verdict(results) -> str:
    """What the recorded host results add up to.

    A function of the results and nothing else. The first version read the
    label off whichever host ran last, so identical evidence produced "caught"
    when Linux finished the run and "caught elsewhere" when Windows did. That
    made the coverage record describe the order someone happened to replay in.

    Caught anywhere is caught, because a guarantee held on one host is held,
    unless a host that ran every test saw the guarantee fail. Caught everywhere
    and caught somewhere are still worth distinguishing: the second means a
    host could not check it, and that is a fact about the host the record
    should keep rather than average away.

    A row no host caught is SURVIVED on every host, a host that skipped
    included. Until D-110 such a row read "unverified: every host skipped"
    when every result carried a skip, on the reasoning that nobody had
    looked. With exact identities (D-104) the console can name the tests the
    host skipped, and a later catching host restores "caught elsewhere"
    through the intersection, so the label protected nothing and hid
    something: on Windows, which skips the symlink test on every row, a new
    row could never fail a replay. Measured: M107 survived at 49fed51 under
    its first test, the summary read "0 not caught", and only the Linux job,
    which skips nothing, said otherwise.

    A host that skipped nothing and still did not catch the mutant has
    observed a survivor, and another host's record cannot soften that. The
    other record was taken on another host and, because a result stores no
    commit, usually at another commit. Before D-095 this function had no such
    branch: the round-sixteen Linux replay that measured M92 surviving exited
    0 with "0 not caught" because the stored Windows record said caught, and
    the same arithmetic kept the Linux CI job green for every row with a
    stored foreign catch.
    """
    caught = [r for r in results if r["verdict"] == "caught"]
    failed_elsewhere = {
        nodeid for result in caught for nodeid in result.get("failed_nodeids", ())
    }
    for result in results:
        if result["verdict"] != "SURVIVED":
            continue
        skipped_nodeids = result.get("skipped_nodeids")
        if not result.get("skipped") or not isinstance(skipped_nodeids, list) or \
                not skipped_nodeids or failed_elsewhere.isdisjoint(skipped_nodeids):
            return "SURVIVED"
    if caught:
        return "caught" if len(caught) == len(results) else "caught elsewhere"
    return "SURVIVED"


def replay(rows: list[dict], write: bool, wanted_subset: bool = False,
           repo_root: Path | None = None, evidence: list[dict] | None = None,
           cleanup: list[dict] | None = None, jobs: int = 1) -> int:
    repo_root = REPO_ROOT if repo_root is None else repo_root
    survivors: list[str] = []
    held_elsewhere: list[str] = []
    host = host_identity()
    print(f"  host: {host['platform']} {host['release']}, "
          f"python {host['python']}, {host['git']}\n")
    if jobs == 1:
        row_results = run_serial(rows, repo_root)
        cleanup_results: list[dict] = []
    else:
        row_results, cleanup_results = run_parallel(rows, jobs, repo_root)
    if evidence is not None:
        evidence.extend(row_results)
    if cleanup is not None:
        cleanup.extend(cleanup_results)
    for row, result in zip(rows, row_results, strict=True):
        # Every field on a console line is rendered, not only the worker's
        # error. The id, name, and replacement id come from matrix.json, which
        # serial replay reads from disk unfrozen. Measured after D-106: a row
        # name carrying a newline and an escape printed a forged summary line
        # in colour, in both modes. See D-106 as amended.
        label = _terminal_safe_diagnostic(str(row["id"]))
        name = _terminal_safe_diagnostic(str(row["name"]))
        if result["status"] == "superseded":
            # The behaviour this mutant attacked moved, so applying it is a
            # no-op and it would report as surviving. That reads like a gap and
            # is not one. Its replacement id is recorded on the row.
            print(f"  {label}  {name:42} superseded by "
                  f"{_terminal_safe_diagnostic(str(row['superseded_by']))}")
            continue
        if result["status"] != "completed":
            # D-102 rendered worker diagnostics on the parallel path only.
            # Measured: a serial SuiteBroken carrying a newline and an ANSI
            # escape printed a forged replay line on the console. The JSON
            # report keeps the raw text; the console gets one bounded,
            # terminal-safe line in both modes. See D-106.
            print(f"  {label}  {name:42} {_terminal_safe_diagnostic(str(result['verdict']))}: "
                  f"{_terminal_safe_diagnostic(result.get('error', 'no row evidence'))}")
            survivors.append(row["id"])
            continue
        verdict = result["verdict"]
        results = {r["platform"]: r for r in row.get("results", [])}
        results[host["platform"]] = {**host, "verdict": verdict,
                                     "pytest": result["pytest"],
                                     "skipped": result["skipped"],
                                     "failed_nodeids": result["failed_nodeids"],
                                     "skipped_nodeids": result["skipped_nodeids"]}
        row["results"] = [results[k] for k in sorted(results)]
        # Caught anywhere is caught. A host that cannot exercise the guarantee
        # reports a skip, and a skip is not evidence of absence.
        row["verdict"] = derive_verdict(row["results"])
        row["pytest"] = result["pytest"]
        # D-110: a local survivor under skips names the tests it skipped, so
        # a reader can see which test might have held it.
        skipped_names = ", ".join(
            nodeid.rsplit("::", 1)[-1] for nodeid in result["skipped_nodeids"])
        skip_note = (f", {result['skipped']} skipped: {skipped_names}"
                     if result["skipped"] else "")
        note = "" if verdict == row["verdict"] and not (
            verdict == "SURVIVED" and result["skipped"]) else (
            f"  (here: {verdict}{skip_note})")
        print(f"  {label}  {name:42} "
              f"{_terminal_safe_diagnostic(str(row['verdict']))}"
              f"{_terminal_safe_diagnostic(note)}")
        if row["verdict"] == "SURVIVED":
            survivors.append(row["id"])
        elif verdict == "SURVIVED":
            held_elsewhere.append(row["id"])
    print(f"\n  {len(rows)} mutants, {len(survivors)} not caught: "
          f"{[_terminal_safe_diagnostic(str(item)) for item in survivors] or 'none'}")
    if held_elsewhere:
        # Not a gate, a disclosure. These rows survived on this host only
        # under skipped tests, and the record that holds them came from a host
        # that could run those tests. A reader who sees only the line above
        # would not know this host observed nothing for them.
        print(f"  {len(held_elsewhere)} survived here under skipped tests and "
              f"rest on another host's record: "
              f"{[_terminal_safe_diagnostic(str(item)) for item in held_elsewhere]}")
    if write:
        if wanted_subset:
            # Writing a filtered run drops every row it did not touch, so the
            # record shrinks each time someone replays one mutant. This is not
            # hypothetical: it truncated the matrix from 43 rows to 1 while
            # this guard was being written, and git had to restore it.
            print("  --write refused for a filtered run: it would truncate the "
                  "matrix to the rows just replayed")
            return 2
        dirty = worktree_status(repo_root)
        if dirty:
            # D-103: a clean start is not enough. Handoff edits can land while
            # a serial run is mutating and restoring sources. Recheck after
            # every row and before the matrix becomes the authoritative record.
            print(f"  --write refused: working tree changed during serial replay "
                  f"and now differs from HEAD in {len(dirty)} path(s)")
            return 2
        MATRIX.write_text(json.dumps(rows, indent=2) + "\n",
                          encoding="utf-8", newline="\n")
    return 1 if survivors else 0


def matrix_sha256() -> str:
    return sha256_bytes(MATRIX.read_bytes())


def main(argv: list[str]) -> int:
    write = False
    report: Path | None = None
    wanted: list[str] = []
    jobs = 1
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--write":
            write = True
        elif arg == "--report":
            index += 1
            if index == len(argv):
                print("--report requires a path")
                return 2
            report = Path(argv[index])
        elif arg == "--jobs":
            index += 1
            if index == len(argv):
                print("--jobs requires a count")
                return 2
            try:
                jobs = int(argv[index])
            except ValueError:
                print("--jobs must be an integer")
                return 2
            if jobs < 1:
                print("--jobs must be positive")
                return 2
        elif arg.startswith("--"):
            print(f"unknown option: {arg}")
            return 2
        else:
            wanted.append(arg)
        index += 1
    rows = json.loads(MATRIX.read_text(encoding="utf-8"))
    missing = [m for m in wanted if m not in {r["id"] for r in rows}]
    if missing:
        print(f"unknown mutant ids: {missing}")
        return 2
    if wanted:
        rows = [r for r in rows if r["id"] in wanted]
    if jobs > 1 and write:
        print("--write is supported only by serial replay; parallel writes fail closed")
        return 2
    before = matrix_sha256()
    evidence: list[dict] = []
    cleanup: list[dict] = []
    serial_status_before: tuple[str, ...] | None = None
    serial_status_after: tuple[str, ...] | None = None
    if jobs == 1:
        try:
            serial_status_before = worktree_status(REPO_ROOT)
        except RuntimeError as caught:
            print(f"serial replay refused: {caught}")
            return 2
    if jobs == 1 and write and serial_status_before:
        # Read-only serial replay deliberately remains useful on a labelled
        # dirty tree. Only matrix publication requires a clean endpoint.
        print(f"--write refused before serial replay: working tree differs from "
              f"HEAD in {len(serial_status_before)} path(s)")
        outcome = 2
    else:
        outcome = replay(rows, write, wanted_subset=bool(wanted), repo_root=REPO_ROOT,
                         evidence=evidence, cleanup=cleanup, jobs=jobs)
    if jobs == 1:
        try:
            serial_status_after = worktree_status(REPO_ROOT)
        except RuntimeError as caught:
            print(f"serial replay endpoint could not be recorded: {caught}")
            outcome = 2
    after = matrix_sha256()
    if report is not None:
        report_commit = (evidence[0]["commit"] if jobs > 1 and evidence
                         else commit_identity(REPO_ROOT))
        report.write_text(json.dumps({
            "commit": report_commit,
            "exit_code": outcome,
            "matrix_sha256_before": before,
            "matrix_sha256_after": after,
            "rows": evidence,
            "cleanup": cleanup,
            "serial_worktree_status_before": (
                list(serial_status_before) if serial_status_before is not None else None),
            "serial_worktree_status_after": (
                list(serial_status_after) if serial_status_after is not None else None),
        }, indent=2) + "\n", encoding="utf-8", newline="\n")
    return outcome


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
