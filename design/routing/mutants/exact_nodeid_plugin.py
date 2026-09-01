"""Evidence-only pytest plugin for exact collected node IDs and outcomes.

The round-sixteen stability gate loads this tracked module in both serial and
xdist runs.  It writes one controller-owned JSON record to the path named by
``ADC_EVIDENCE_OUTCOMES``; workers never write the artifact.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


_nodeids: list[str] = []
_reports: dict[str, list[tuple[str, str]]] = {}
_worker_collections: dict[str, list[str]] = {}


def pytest_configure(config) -> None:
    global _nodeids, _reports, _worker_collections
    _nodeids = []
    _reports = {}
    _worker_collections = {}


def _is_worker(config) -> bool:
    return hasattr(config, "workerinput")


def pytest_collection_finish(session) -> None:
    global _nodeids
    if not _is_worker(session.config):
        _nodeids = [item.nodeid for item in session.items]


def pytest_xdist_node_collection_finished(node, ids) -> None:
    """Require every xdist worker to collect the same exact ordered set."""
    global _nodeids
    worker_id = getattr(getattr(node, "gateway", None), "id", str(node))
    _worker_collections[worker_id] = list(ids)
    if not _nodeids:
        _nodeids = list(ids)
    elif _nodeids != list(ids):
        raise RuntimeError("xdist workers collected different exact node-id orders")


def pytest_runtest_logreport(report) -> None:
    outcome = (
        "error"
        if report.when != "call" and report.outcome == "failed"
        else report.outcome
    )
    _reports.setdefault(report.nodeid, []).append((report.when, outcome))


def _aggregate(reports: list[tuple[str, str]]) -> str:
    values = {outcome for _, outcome in reports}
    if "error" in values:
        return "error"
    if "failed" in values:
        return "failed"
    if "skipped" in values:
        return "skipped"
    if values == {"passed"}:
        return "passed"
    return "missing"


def pytest_sessionfinish(session, exitstatus) -> None:
    if _is_worker(session.config):
        return
    outcomes = {nodeid: _aggregate(_reports.get(nodeid, [])) for nodeid in _nodeids}
    payload = {
        "collect_nodeids": _nodeids,
        "collect_nodeids_sha256": hashlib.sha256(
            "\n".join(_nodeids).encode()
        ).hexdigest(),
        "worker_collections": _worker_collections,
        "worker_collection_sha256": {
            worker: hashlib.sha256("\n".join(ids).encode()).hexdigest()
            for worker, ids in _worker_collections.items()
        },
        "outcomes": outcomes,
        "reports": {nodeid: _reports.get(nodeid, []) for nodeid in _nodeids},
        "missing": [
            nodeid for nodeid, outcome in outcomes.items() if outcome == "missing"
        ],
        "exitstatus": exitstatus,
    }
    target = Path(os.environ["ADC_EVIDENCE_OUTCOMES"])
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
