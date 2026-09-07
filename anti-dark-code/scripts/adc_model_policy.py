#!/usr/bin/env python3
"""Offline, host-neutral model-routing recommendation.

This module only evaluates caller-provided capability and catalog metadata.  It
does not invoke a model, tool, subprocess, network request, or host setting.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date
from pathlib import Path
from typing import Any, Mapping


TIERS = ("economy", "standard", "strong")
TASK_TIERS = {"bounded": "economy", "routine": "standard", "consequential": "strong"}
MAX_REQUEST_BYTES = 64 * 1024


def _valid_rank(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
        and value >= 0
    )


def _result(current: object, reason: str, *, target_tier: str | None = None,
            attempts: int = 1, effort: object = None) -> dict[str, Any]:
    return {
        "action": "keep-current",
        "model": current if isinstance(current, str) else None,
        "requested_effort": effort if isinstance(effort, str) else None,
        "target_tier": target_tier,
        "reason": reason,
        "attempts_to_record": attempts,
        "remaining_escalations": 0,
    }


def _parse_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _catalog_status(catalog: object, today: date, max_age_days: object) -> tuple[str | None, Mapping[str, Any] | None]:
    if not isinstance(catalog, Mapping) or catalog.get("schema_version") != 1:
        return "catalog-invalid", None
    checked = _parse_date(catalog.get("checked_on"))
    models = catalog.get("models")
    if checked is None or not isinstance(models, Mapping):
        return "catalog-invalid", None
    age_limit = max_age_days if max_age_days is not None else catalog.get("max_age_days", 30)
    if isinstance(age_limit, bool) or not isinstance(age_limit, int) or age_limit < 0:
        return "catalog-invalid", None
    if checked > today:
        return "catalog-future", None
    if (today - checked).days > age_limit:
        return "catalog-stale", None
    for model_id, metadata in models.items():
        if not isinstance(model_id, str) or not isinstance(metadata, Mapping):
            return "catalog-invalid", None
        if metadata.get("tier") not in TIERS:
            return "catalog-invalid", None
    return None, models


def _live_models(value: object) -> list[dict[str, object]] | None:
    if not isinstance(value, list):
        return None
    result: list[dict[str, object]] = []
    seen: set[str] = set()
    for candidate in value:
        if isinstance(candidate, str):
            candidate = {"id": candidate}
        if not isinstance(candidate, Mapping) or not isinstance(candidate.get("id"), str):
            return None
        model_id = candidate["id"]
        if model_id in seen:
            continue
        controls = candidate.get("controls")
        efforts = candidate.get("efforts")
        if controls is not None and (not isinstance(controls, list) or not all(isinstance(v, str) for v in controls)):
            return None
        if efforts is not None and (not isinstance(efforts, list) or not all(isinstance(v, str) for v in efforts)):
            return None
        if candidate.get("eligible", True) is not True:
            continue
        seen.add(model_id)
        result.append({"id": model_id, "controls": controls, "efforts": efforts})
    return result


def _eligible(live: list[dict[str, object]], models: Mapping[str, Any], required_controls: set[str],
              required_effort: str | None) -> list[dict[str, Any]]:
    eligible: list[dict[str, Any]] = []
    for candidate in live:
        model_id = candidate["id"]
        if not isinstance(model_id, str):
            continue
        # These are caller-reported live controls, not catalog assumptions.
        controls = candidate["controls"]
        if required_controls and (not isinstance(controls, list) or not required_controls.issubset(set(controls))):
            continue
        efforts = candidate["efforts"]
        if required_effort is not None and (not isinstance(efforts, list) or required_effort not in efforts):
            continue
        metadata = models.get(model_id)
        if not isinstance(metadata, Mapping):
            continue
        rank = metadata.get("relative_cost_rank")
        if not _valid_rank(rank):
            rank = None
        eligible.append({"id": model_id, "tier": metadata["tier"], "rank": rank})
    return eligible


def select_model_policy(request: Mapping[str, Any], catalog: Mapping[str, Any] | None,
                        *, today: date | None = None) -> dict[str, Any]:
    """Return a conservative recommendation; never perform a switch itself."""
    current = request.get("current_model") if isinstance(request, Mapping) else None
    effort = request.get("required_effort") if isinstance(request, Mapping) else None
    if not isinstance(request, Mapping) or not isinstance(current, str) or not current:
        return _result(current, "request-invalid", effort=effort)
    if effort is not None and (not isinstance(effort, str) or not effort):
        return _result(current, "request-invalid")
    task_class = request.get("task_class")
    if task_class not in TASK_TIERS:
        return _result(current, "task-class-unknown", effort=effort)
    target_tier = TASK_TIERS[task_class]
    if request.get("can_select") is not True:
        return _result(current, "host-selection-unavailable", target_tier=target_tier, effort=effort)
    if request.get("switch_authorized") is not True:
        return _result(current, "model-switch-not-authorized", target_tier=target_tier, effort=effort)
    if request.get("has_oracle") is not True:
        return _result(current, "no-acceptance-oracle", target_tier=target_tier, effort=effort)
    if request.get("requirements_known", True) is not True:
        return _result(current, "requirements-unknown", target_tier=target_tier, effort=effort)
    if request.get("current_constraints_known", True) is not True:
        return _result(current, "current-constraints-unknown", target_tier=target_tier, effort=effort)

    failed = request.get("verification_failed", False)
    if not isinstance(failed, bool):
        return _result(current, "request-invalid", target_tier=target_tier, effort=effort)
    if failed and (not isinstance(request.get("failure_evidence"), str) or not request["failure_evidence"].strip()):
        return _result(current, "failure-evidence-unknown", target_tier=target_tier, effort=effort)
    escalation_count = request.get("escalation_count", 0)
    if isinstance(escalation_count, bool) or not isinstance(escalation_count, int) or escalation_count < 0:
        return _result(current, "request-invalid", target_tier=target_tier, effort=effort)
    if failed and escalation_count >= 1:
        return _result(current, "escalation-limit-reached", target_tier=target_tier, effort=effort)

    now = today or date.today()
    status, models = _catalog_status(catalog, now, request.get("max_catalog_age_days"))
    if status:
        return _result(current, status, target_tier=target_tier, attempts=2 if failed else 1, effort=effort)
    assert models is not None
    current_metadata = models.get(current)
    if not isinstance(current_metadata, Mapping):
        return _result(current, "current-model-unknown", target_tier=target_tier, attempts=2 if failed else 1, effort=effort)
    current_tier = current_metadata.get("tier")
    if current_tier not in TIERS:
        return _result(current, "current-quality-unknown", target_tier=target_tier, attempts=2 if failed else 1, effort=effort)
    current_rank = current_metadata.get("relative_cost_rank")
    if not _valid_rank(current_rank):
        return _result(current, "cost-rank-unknown", target_tier=target_tier, attempts=2 if failed else 1, effort=effort)

    required = request.get("required_controls", [])
    if not isinstance(required, list) or not all(isinstance(v, str) and v for v in required):
        return _result(current, "request-invalid", target_tier=target_tier, effort=effort)
    live = _live_models(request.get("available_models"))
    if live is None:
        return _result(current, "available-models-unknown", target_tier=target_tier, effort=effort)
    candidates = _eligible(live, models, set(required), effort)
    if not candidates:
        return _result(current, "no-live-eligible-model", target_tier=target_tier, attempts=2 if failed else 1, effort=effort)

    current_index = TIERS.index(current_tier)
    target_index = TIERS.index(target_tier)
    if failed:
        target_index = max(target_index, current_index + 1)
        if target_index >= len(TIERS):
            return _result(current, "failure-already-strong", target_tier=current_tier, attempts=2, effort=effort)
        target_tier = TIERS[target_index]
    elif current_index == target_index:
        return _result(current, f"current-satisfies-{target_tier}", target_tier=target_tier, effort=effort)

    tier_candidates = [candidate for candidate in candidates if candidate["tier"] == target_tier]
    if not tier_candidates:
        return _result(current, "no-live-eligible-model", target_tier=target_tier, attempts=2 if failed else 1, effort=effort)
    if any(candidate["rank"] is None for candidate in tier_candidates):
        return _result(current, "cost-rank-unknown", target_tier=target_tier, attempts=2 if failed else 1, effort=effort)
    chosen = min(tier_candidates, key=lambda candidate: (candidate["rank"], candidate["id"]))
    if not failed and target_index < current_index and chosen["rank"] >= current_rank:
        return _result(current, "no-cheaper-eligible-model", target_tier=target_tier, effort=effort)
    return {
        "action": "select",
        "model": chosen["id"],
        "requested_effort": effort,
        "target_tier": target_tier,
        "reason": "verification-failure-escalation" if failed else f"{task_class}-tier-route",
        "attempts_to_record": 2 if failed else 1,
        "remaining_escalations": 0,
    }


def _load_catalog(path: str) -> object:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _load_request_json(value: str) -> Mapping[str, Any] | None:
    if len(value.encode("utf-8")) > MAX_REQUEST_BYTES:
        return None
    try:
        parsed = json.loads(value, parse_constant=lambda _value: (_ for _ in ()).throw(ValueError()))
    except (TypeError, ValueError, RecursionError):
        return None
    return parsed if isinstance(parsed, Mapping) else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Return an offline model-routing recommendation as JSON.")
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--available", action="append", default=[])
    parser.add_argument("--current")
    parser.add_argument("--task", dest="task_class", choices=tuple(TASK_TIERS))
    parser.add_argument("--can-select", action="store_true")
    parser.add_argument("--switch-authorized", action="store_true")
    parser.add_argument("--has-oracle", action="store_true")
    parser.add_argument("--verification-failed", action="store_true")
    parser.add_argument("--failure-evidence")
    parser.add_argument("--requires-control", action="append", default=[])
    parser.add_argument("--required-effort")
    parser.add_argument("--max-catalog-age-days", type=int)
    parser.add_argument("--request", help="JSON object with live model/control/effort metadata (64 KiB maximum).")
    args = parser.parse_args(argv)
    request = {
        "available_models": args.available,
        "current_model": args.current,
        "can_select": args.can_select,
        "switch_authorized": args.switch_authorized,
        "task_class": args.task_class,
        "has_oracle": args.has_oracle,
        "verification_failed": args.verification_failed,
        "failure_evidence": args.failure_evidence,
        "required_controls": args.requires_control,
        "required_effort": args.required_effort,
        "max_catalog_age_days": args.max_catalog_age_days,
    }
    if args.request is not None:
        supplied = _load_request_json(args.request)
        if supplied is None:
            print(json.dumps(_result(args.current, "request-json-invalid"), sort_keys=True))
            return 0
        request.update(supplied)
    print(json.dumps(select_model_policy(request, _load_catalog(args.catalog)), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
