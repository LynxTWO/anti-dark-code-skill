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
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

MATRIX = Path(__file__).with_name("matrix.json")


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
    return [sys.executable, "-m", "pytest", *paths, "-q", "-k", INTEGRITY_FILTER]


class SuiteBroken(RuntimeError):
    """The suite did not run, so the mutant proved nothing either way."""


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


def run_suite(paths=DEFAULT_SUITE, repo_root: Path = REPO_ROOT) -> tuple[int, str, int]:
    """Return the pytest exit, exact summary line, and skipped count.

    A mutant is caught when tests fail. It is not caught when they pass. A
    suite that could not collect, crashed, or was interrupted says nothing
    about the mutant, and treating that as either verdict would put a false
    row in the record. Those raise instead.
    """
    execution_cwd = _WORKER_SUITE_CWD or repo_root
    command_paths = paths
    cache_root = Path(tempfile.mkdtemp(prefix="adc-replay-pycache-"))
    environment = dict(os.environ)
    environment.pop("PYTHONPYCACHEPREFIX", None)
    environment.pop("PYTHONDONTWRITEBYTECODE", None)
    environment.update({"PYTHONPYCACHEPREFIX": str(cache_root),
                        "PYTHONDONTWRITEBYTECODE": "1"})
    if _WORKER_SUITE_CWD is not None:
        command_paths = tuple(
            str(path if Path(path).is_absolute() else repo_root / path)
            for path in paths)
    command = suite_command(command_paths)
    if _WORKER_TEMP_ROOT is not None:
        pytest_root = _WORKER_TEMP_ROOT / "pytest"
        command.append(f"--basetemp={pytest_root}")
        environment.update({"TMP": str(_WORKER_TEMP_ROOT),
                            "TEMP": str(_WORKER_TEMP_ROOT),
                            "TMPDIR": str(_WORKER_TEMP_ROOT)})
    launch_error: OSError | None = None
    cleanup_error: OSError | None = None
    try:
        done = subprocess.run(command, cwd=execution_cwd, env=environment,
                              capture_output=True, text=True)
    except OSError as caught:
        launch_error = caught
        done = None
    finally:
        try:
            shutil.rmtree(cache_root)
        except OSError as caught:
            cleanup_error = caught
    if cleanup_error is not None:
        raise SuiteBroken(f"owned bytecode cache cleanup failed: {cleanup_error}")
    if launch_error is not None:
        raise SuiteBroken(f"pytest launch failed: {launch_error}")
    assert done is not None
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
    return done.returncode, summary, skipped


def _row_evidence(row: dict, host: dict, worker: str, commit: str,
                  started: float, before: str | None = None) -> dict:
    """Start a JSON-compatible result before a row can mutate a source."""
    return {
        "id": row["id"], "status": "inconclusive", "verdict": "INCONCLUSIVE",
        "caught": None, "exit_code": None, "pytest": None, "skipped": 0,
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
            exit_code, summary, skipped = run_suite(
                tuple(row.get("suite", DEFAULT_SUITE)), repo_root)
            result["pytest"] = summary
            result["skipped"] = skipped
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


def _verify_coordinator_sources(repo_root: Path, commit: str) -> None:
    """Freeze the coordinator bytes before it creates any clone or worker."""
    try:
        matrix_relative = MATRIX.resolve().relative_to(REPO_ROOT.resolve())
        replay_relative = Path(__file__).resolve().relative_to(REPO_ROOT.resolve())
    except ValueError as caught:
        raise RuntimeError("replay authority paths are outside the coordinator") from caught
    matrix_path = repo_root / matrix_relative
    _verify_working_sources(repo_root, commit, {matrix_relative, replay_relative})
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


WORKER_RESULT_FIELDS = frozenset({
    "id", "status", "verdict", "caught", "exit_code", "pytest", "skipped",
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

    Caught anywhere is caught, because a guarantee held on one host is held.
    Caught everywhere and caught somewhere are still worth distinguishing: the
    second means a host could not check it, and that is a fact about the host
    the record should keep rather than average away.

    Every host skipping is not evidence of absence. It is evidence nobody
    looked, and calling it SURVIVED would put a gap in the record that no host
    has observed.
    """
    caught = [r for r in results if r["verdict"] == "caught"]
    if caught:
        return "caught" if len(caught) == len(results) else "caught elsewhere"
    if results and all(r.get("skipped") for r in results):
        return "unverified: every host skipped"
    return "SURVIVED"


def replay(rows: list[dict], write: bool, wanted_subset: bool = False,
           repo_root: Path | None = None, evidence: list[dict] | None = None,
           cleanup: list[dict] | None = None, jobs: int = 1) -> int:
    repo_root = REPO_ROOT if repo_root is None else repo_root
    survivors: list[str] = []
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
        if result["status"] == "superseded":
            # The behaviour this mutant attacked moved, so applying it is a
            # no-op and it would report as surviving. That reads like a gap and
            # is not one. Its replacement id is recorded on the row.
            print(f"  {row['id']}  {row['name']:42} superseded by "
                  f"{row['superseded_by']}")
            continue
        if result["status"] != "completed":
            print(f"  {row['id']}  {row['name']:42} {result['verdict']}: "
                  f"{result.get('error', 'no row evidence')}")
            survivors.append(row["id"])
            continue
        verdict = result["verdict"]
        results = {r["platform"]: r for r in row.get("results", [])}
        results[host["platform"]] = {**host, "verdict": verdict,
                                     "pytest": result["pytest"],
                                     "skipped": result["skipped"]}
        row["results"] = [results[k] for k in sorted(results)]
        # Caught anywhere is caught. A host that cannot exercise the guarantee
        # reports a skip, and a skip is not evidence of absence.
        row["verdict"] = derive_verdict(row["results"])
        row["pytest"] = result["pytest"]
        note = "" if verdict == row["verdict"] else (
            f"  (here: {verdict}{', ' + str(result['skipped']) + ' skipped' if result['skipped'] else ''})")
        print(f"  {row['id']}  {row['name']:42} {row['verdict']}{note}")
        if row["verdict"] == "SURVIVED":
            survivors.append(row["id"])
    print(f"\n  {len(rows)} mutants, {len(survivors)} not caught: "
          f"{survivors or 'none'}")
    if write:
        if wanted_subset:
            # Writing a filtered run drops every row it did not touch, so the
            # record shrinks each time someone replays one mutant. This is not
            # hypothetical: it truncated the matrix from 43 rows to 1 while
            # this guard was being written, and git had to restore it.
            print("  --write refused for a filtered run: it would truncate the "
                  "matrix to the rows just replayed")
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
    outcome = replay(rows, write, wanted_subset=bool(wanted), repo_root=REPO_ROOT,
                     evidence=evidence, cleanup=cleanup, jobs=jobs)
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
        }, indent=2) + "\n", encoding="utf-8", newline="\n")
    return outcome


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
