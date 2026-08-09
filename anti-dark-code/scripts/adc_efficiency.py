#!/usr/bin/env python3
"""Offline, opt-in efficiency receipts for Anti-Dark-Code.

This module records numeric usage supplied by an operator. It never discovers
host logs, reads prompts or responses, contacts a network service, or uploads a
receipt. Public receipts are allowlisted projections of local receipts.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import statistics
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = 1
EVIDENCE_LABEL = "community-self-reported"
MAX_RECEIPT_BYTES = 256 * 1024
MAX_TOKEN_COUNT = 1_000_000_000_000
MAX_CALL_COUNT = 1_000_000
MAX_TRIAL = 1_000_000
TASK_CLASSES = ("map", "audit", "verify", "remediate", "install", "other")
STUDY_ORDERS = ("skill-first", "baseline-first")
HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
MONTH_PATTERN = re.compile(r"^(\d{4})-(\d{2})$")
CONTROL_PATTERN = re.compile(r"[\x00-\x1f\x7f]")
PUBLIC_RECEIPT_FILENAME_RE = re.compile(r"^efficiency-([0-9a-f]{12})\.json$")

USAGE_FIELDS = (
    "input_tokens",
    "cache_read_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_tokens",
    "tool_prompt_tokens",
    "provider_total_tokens",
)
DELTA_FIELDS = USAGE_FIELDS
LOCAL_CONTROL_FIELDS = (
    "settings_sha256",
    "tools_sha256",
    "fixture_sha256",
    "oracle_sha256",
    "fresh_context",
    "same_acceptance_contract",
)


class EfficiencyReceiptError(ValueError):
    """Raised when an efficiency receipt or operation is invalid."""


def strict_json_loads(text: str) -> Any:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise EfficiencyReceiptError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        return json.loads(text, object_pairs_hook=reject_duplicate_keys)
    except json.JSONDecodeError as error:
        raise EfficiencyReceiptError(f"invalid JSON: {error}") from error


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_prefixed(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def normalize_sha256(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise EfficiencyReceiptError(f"{field} must be a SHA-256 digest")
    normalized = value.lower()
    if not normalized.startswith("sha256:"):
        normalized = "sha256:" + normalized
    if not HASH_PATTERN.fullmatch(normalized):
        raise EfficiencyReceiptError(f"{field} must be a SHA-256 digest")
    return normalized


def current_month() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m")


def validate_month(value: Any, field: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{field} must be YYYY-MM")
        return
    match = MONTH_PATTERN.fullmatch(value)
    if not match:
        errors.append(f"{field} must be YYYY-MM")
        return
    month = int(match.group(2))
    if month < 1 or month > 12:
        errors.append(f"{field} must contain a real month")


def validate_plain_string(
    value: Any,
    field: str,
    errors: list[str],
    *,
    max_length: int = 128,
    slug: bool = False,
) -> None:
    if not isinstance(value, str) or not value or len(value) > max_length:
        errors.append(f"{field} must be a non-empty string of at most {max_length} characters")
        return
    if CONTROL_PATTERN.search(value):
        errors.append(f"{field} contains a control character")
    if slug and not SLUG_PATTERN.fullmatch(value):
        errors.append(f"{field} must be a lowercase identifier")


def validate_exact_keys(value: Any, expected: set[str], field: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object")
        return False
    actual = set(value)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        errors.append(f"{field} is missing: {', '.join(missing)}")
    if extra:
        errors.append(f"{field} has unsupported fields: {', '.join(extra)}")
    return not missing and not extra


def validate_counter(value: Any, field: str, errors: list[str], *, nullable: bool = True) -> None:
    if value is None and nullable:
        return
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append(f"{field} must be an integer" + (" or null" if nullable else ""))
        return
    if value < 0 or value > MAX_TOKEN_COUNT:
        errors.append(f"{field} must be between 0 and {MAX_TOKEN_COUNT}")


def validate_usage(value: Any, field: str, errors: list[str]) -> None:
    expected = {"call_count", *USAGE_FIELDS}
    if not validate_exact_keys(value, expected, field, errors):
        return
    call_count = value["call_count"]
    if isinstance(call_count, bool) or not isinstance(call_count, int):
        errors.append(f"{field}.call_count must be an integer")
    elif call_count < 1 or call_count > MAX_CALL_COUNT:
        errors.append(f"{field}.call_count must be between 1 and {MAX_CALL_COUNT}")
    for name in USAGE_FIELDS:
        validate_counter(
            value[name],
            f"{field}.{name}",
            errors,
            nullable=name != "provider_total_tokens",
        )
    if errors:
        return
    input_tokens = value["input_tokens"]
    output_tokens = value["output_tokens"]
    total_tokens = value["provider_total_tokens"]
    if input_tokens is not None and output_tokens is not None and total_tokens != input_tokens + output_tokens:
        errors.append(f"{field}.provider_total_tokens must equal input_tokens + output_tokens")
    for subset in ("cache_read_input_tokens", "cache_write_input_tokens", "tool_prompt_tokens"):
        if input_tokens is not None and value[subset] is not None and value[subset] > input_tokens:
            errors.append(f"{field}.{subset} cannot exceed input_tokens")
    if output_tokens is not None and value["reasoning_tokens"] is not None and value["reasoning_tokens"] > output_tokens:
        errors.append(f"{field}.reasoning_tokens cannot exceed output_tokens")
    cache_read = value["cache_read_input_tokens"]
    cache_write = value["cache_write_input_tokens"]
    if input_tokens is not None and cache_read is not None and cache_write is not None:
        if cache_read + cache_write > input_tokens:
            errors.append(f"{field} cache read + write tokens cannot exceed input_tokens")


def validate_skill(value: Any, errors: list[str]) -> None:
    if not validate_exact_keys(value, {"version", "core_sha256"}, "skill", errors):
        return
    validate_plain_string(value["version"], "skill.version", errors, max_length=96)
    if not isinstance(value["core_sha256"], str) or not HASH_PATTERN.fullmatch(value["core_sha256"]):
        errors.append("skill.core_sha256 must be a SHA-256 digest")


def validate_study(value: Any, errors: list[str]) -> None:
    if not validate_exact_keys(value, {"task_class", "trial", "order"}, "study", errors):
        return
    if value["task_class"] not in TASK_CLASSES:
        errors.append("study.task_class is not supported")
    trial = value["trial"]
    if isinstance(trial, bool) or not isinstance(trial, int):
        errors.append("study.trial must be an integer")
    elif trial < 1 or trial > MAX_TRIAL:
        errors.append(f"study.trial must be between 1 and {MAX_TRIAL}")
    if value["order"] not in STUDY_ORDERS:
        errors.append("study.order must be skill-first or baseline-first")


def validate_local_controls(value: Any, errors: list[str]) -> None:
    if not validate_exact_keys(value, set(LOCAL_CONTROL_FIELDS), "controls", errors):
        return
    for name in LOCAL_CONTROL_FIELDS[:4]:
        if not isinstance(value[name], str) or not HASH_PATTERN.fullmatch(value[name]):
            errors.append(f"controls.{name} must be a SHA-256 digest")
    for name in LOCAL_CONTROL_FIELDS[4:]:
        if not isinstance(value[name], bool):
            errors.append(f"controls.{name} must be boolean")


def validate_public_controls(value: Any, errors: list[str]) -> None:
    expected = {"comparison_sha256", "fresh_context", "same_acceptance_contract"}
    if not validate_exact_keys(value, expected, "controls", errors):
        return
    if not isinstance(value["comparison_sha256"], str) or not HASH_PATTERN.fullmatch(value["comparison_sha256"]):
        errors.append("controls.comparison_sha256 must be a SHA-256 digest")
    for name in ("fresh_context", "same_acceptance_contract"):
        if not isinstance(value[name], bool):
            errors.append(f"controls.{name} must be boolean")


def validate_privacy(value: Any, errors: list[str]) -> None:
    expected = {
        "explicit_opt_in",
        "contains_content",
        "contains_paths",
        "contains_repo_or_user_identifiers",
    }
    if not validate_exact_keys(value, expected, "privacy", errors):
        return
    if value["explicit_opt_in"] is not True:
        errors.append("privacy.explicit_opt_in must be true")
    for name in expected - {"explicit_opt_in"}:
        if value[name] is not False:
            errors.append(f"privacy.{name} must be false")


def receipt_payload(receipt: Mapping[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(dict(receipt))
    payload.pop("receipt_id", None)
    payload.pop("integrity", None)
    return payload


def seal_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    sealed = copy.deepcopy(dict(receipt))
    digest = sha256_prefixed(canonical_json_bytes(receipt_payload(sealed)))
    sealed["receipt_id"] = digest
    sealed["integrity"] = {
        "algorithm": "sha256",
        "canonical_payload_sha256": digest,
        "note": "Content integrity only; this is not an authenticity attestation.",
    }
    return sealed


def validate_common(receipt: dict[str, Any], errors: list[str]) -> None:
    if receipt.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if receipt.get("evidence_label") != EVIDENCE_LABEL:
        errors.append(f"evidence_label must be {EVIDENCE_LABEL}")
    if receipt.get("visibility") not in {"local", "public"}:
        errors.append("visibility must be local or public")
    validate_month(receipt.get("created_month"), "created_month", errors)
    validate_skill(receipt.get("skill"), errors)
    validate_study(receipt.get("study"), errors)
    validate_privacy(receipt.get("privacy"), errors)

    receipt_id = receipt.get("receipt_id")
    integrity = receipt.get("integrity")
    if not isinstance(receipt_id, str) or not HASH_PATTERN.fullmatch(receipt_id):
        errors.append("receipt_id must be a SHA-256 digest")
    if validate_exact_keys(
        integrity,
        {"algorithm", "canonical_payload_sha256", "note"},
        "integrity",
        errors,
    ):
        if integrity["algorithm"] != "sha256":
            errors.append("integrity.algorithm must be sha256")
        if integrity["note"] != "Content integrity only; this is not an authenticity attestation.":
            errors.append("integrity.note is not canonical")
        digest = integrity["canonical_payload_sha256"]
        if not isinstance(digest, str) or not HASH_PATTERN.fullmatch(digest):
            errors.append("integrity.canonical_payload_sha256 must be a SHA-256 digest")
        expected = sha256_prefixed(canonical_json_bytes(receipt_payload(receipt)))
        if receipt_id != expected or digest != expected:
            errors.append("receipt content hash does not match its payload")


def validate_measurement_identity(value: dict[str, Any], field: str, errors: list[str]) -> None:
    validate_plain_string(value.get("provider"), f"{field}.provider", errors, max_length=64, slug=True)
    validate_plain_string(value.get("model"), f"{field}.model", errors, max_length=128)
    validate_plain_string(
        value.get("adapter_version"),
        f"{field}.adapter_version",
        errors,
        max_length=64,
        slug=True,
    )
    validate_plain_string(
        value.get("usage_semantics"),
        f"{field}.usage_semantics",
        errors,
        max_length=64,
        slug=True,
    )


def validate_actual(receipt: dict[str, Any], errors: list[str]) -> None:
    expected = {
        "schema_version",
        "receipt_type",
        "visibility",
        "evidence_label",
        "created_month",
        "skill",
        "study",
        "measurement",
        "controls",
        "quality",
        "privacy",
        "receipt_id",
        "integrity",
    }
    validate_exact_keys(receipt, expected, "receipt", errors)
    measurement = receipt.get("measurement")
    measurement_keys = {
        "source",
        "condition",
        "provider",
        "model",
        "adapter_version",
        "usage_semantics",
        "usage",
    }
    if validate_exact_keys(measurement, measurement_keys, "measurement", errors):
        if measurement["source"] != "host-reported":
            errors.append("measurement.source must be host-reported for actual usage")
        if measurement["condition"] not in {"skill", "baseline"}:
            errors.append("measurement.condition must be skill or baseline")
        validate_measurement_identity(measurement, "measurement", errors)
        validate_usage(measurement["usage"], "measurement.usage", errors)
    quality = receipt.get("quality")
    if validate_exact_keys(quality, {"passed"}, "quality", errors) and not isinstance(quality["passed"], bool):
        errors.append("quality.passed must be boolean")
    if receipt.get("visibility") == "local":
        validate_local_controls(receipt.get("controls"), errors)
    elif receipt.get("visibility") == "public":
        validate_public_controls(receipt.get("controls"), errors)


def validate_delta(value: Any, errors: list[str]) -> None:
    if not validate_exact_keys(value, set(DELTA_FIELDS), "measurement.token_delta", errors):
        return
    for name in DELTA_FIELDS:
        item = value[name]
        if item is None and name != "provider_total_tokens":
            continue
        if isinstance(item, bool) or not isinstance(item, int):
            errors.append(f"measurement.token_delta.{name} must be an integer" + (" or null" if name != "provider_total_tokens" else ""))
        elif item < -MAX_TOKEN_COUNT or item > MAX_TOKEN_COUNT:
            errors.append(f"measurement.token_delta.{name} is outside the supported range")


def validate_pair(receipt: dict[str, Any], errors: list[str]) -> None:
    expected = {
        "schema_version",
        "receipt_type",
        "visibility",
        "evidence_label",
        "created_month",
        "skill",
        "study",
        "measurement",
        "controls",
        "quality",
        "privacy",
        "receipt_id",
        "integrity",
    }
    if receipt.get("visibility") == "local":
        expected.add("source_receipts")
    validate_exact_keys(receipt, expected, "receipt", errors)
    measurement = receipt.get("measurement")
    measurement_keys = {
        "source",
        "provider",
        "model",
        "adapter_version",
        "usage_semantics",
        "skill_usage",
        "baseline_usage",
        "token_delta",
        "percent_provider_total_delta",
    }
    if validate_exact_keys(measurement, measurement_keys, "measurement", errors):
        if measurement["source"] != "controlled-pair":
            errors.append("measurement.source must be controlled-pair")
        validate_measurement_identity(measurement, "measurement", errors)
        validate_usage(measurement["skill_usage"], "measurement.skill_usage", errors)
        validate_usage(measurement["baseline_usage"], "measurement.baseline_usage", errors)
        validate_delta(measurement["token_delta"], errors)
        percent = measurement["percent_provider_total_delta"]
        if percent is not None and (isinstance(percent, bool) or not isinstance(percent, (int, float))):
            errors.append("measurement.percent_provider_total_delta must be a number or null")
        if isinstance(percent, float) and (percent != percent or percent in {float("inf"), float("-inf")}):
            errors.append("measurement.percent_provider_total_delta must be finite")
        if not errors:
            expected_delta = calculate_token_delta(
                measurement["skill_usage"], measurement["baseline_usage"]
            )
            if measurement["token_delta"] != expected_delta:
                errors.append("measurement.token_delta does not match the paired usage")
            expected_percent = calculate_percent_delta(
                measurement["skill_usage"]["provider_total_tokens"],
                measurement["baseline_usage"]["provider_total_tokens"],
            )
            if percent != expected_percent:
                errors.append("measurement.percent_provider_total_delta does not match the paired usage")
    quality = receipt.get("quality")
    quality_keys = {"skill_passed", "baseline_passed", "same_acceptance_contract"}
    if validate_exact_keys(quality, quality_keys, "quality", errors):
        for name in quality_keys:
            if quality[name] is not True:
                errors.append(f"quality.{name} must be true for a controlled pair")
    if receipt.get("visibility") == "local":
        validate_local_controls(receipt.get("controls"), errors)
        source = receipt.get("source_receipts")
        if validate_exact_keys(
            source,
            {"skill_receipt_id", "baseline_receipt_id"},
            "source_receipts",
            errors,
        ):
            for name in ("skill_receipt_id", "baseline_receipt_id"):
                if not isinstance(source[name], str) or not HASH_PATTERN.fullmatch(source[name]):
                    errors.append(f"source_receipts.{name} must be a SHA-256 digest")
    elif receipt.get("visibility") == "public":
        validate_public_controls(receipt.get("controls"), errors)
    controls = receipt.get("controls")
    if isinstance(controls, dict):
        for name in ("fresh_context", "same_acceptance_contract"):
            if controls.get(name) is not True:
                errors.append(f"controls.{name} must be true for a controlled pair")


def validate_receipt(receipt: Any, *, require_public: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(receipt, dict):
        return ["receipt must be a JSON object"]
    receipt_type = receipt.get("receipt_type")
    if receipt_type == "actual_usage":
        validate_actual(receipt, errors)
    elif receipt_type == "controlled_pair":
        validate_pair(receipt, errors)
    else:
        errors.append("receipt_type must be actual_usage or controlled_pair")
    validate_common(receipt, errors)
    if require_public and receipt.get("visibility") != "public":
        errors.append("public ledger accepts only privacy-stripped public receipts")
    return sorted(set(errors))


def require_valid_receipt(receipt: Any, *, require_public: bool = False) -> dict[str, Any]:
    errors = validate_receipt(receipt, require_public=require_public)
    if errors:
        raise EfficiencyReceiptError("; ".join(errors))
    return copy.deepcopy(receipt)


def make_usage(
    *,
    call_count: int,
    input_tokens: int | None,
    cache_read_input_tokens: int | None,
    cache_write_input_tokens: int | None,
    output_tokens: int | None,
    reasoning_tokens: int | None,
    tool_prompt_tokens: int | None,
    provider_total_tokens: int,
) -> dict[str, int | None]:
    return {
        "call_count": call_count,
        "input_tokens": input_tokens,
        "cache_read_input_tokens": cache_read_input_tokens,
        "cache_write_input_tokens": cache_write_input_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "tool_prompt_tokens": tool_prompt_tokens,
        "provider_total_tokens": provider_total_tokens,
    }


def create_actual_receipt(
    *,
    explicit_opt_in: bool,
    condition: str,
    skill_version: str,
    core_sha256: str,
    provider: str,
    model: str,
    adapter_version: str,
    usage_semantics: str,
    settings_sha256: str,
    tools_sha256: str,
    fixture_sha256: str,
    oracle_sha256: str,
    fresh_context: bool,
    same_acceptance_contract: bool,
    quality_passed: bool,
    provider_total_tokens: int,
    task_class: str,
    trial: int,
    order: str,
    call_count: int = 1,
    input_tokens: int | None = None,
    cache_read_input_tokens: int | None = None,
    cache_write_input_tokens: int | None = None,
    output_tokens: int | None = None,
    reasoning_tokens: int | None = None,
    tool_prompt_tokens: int | None = None,
    created_month: str | None = None,
) -> dict[str, Any]:
    if explicit_opt_in is not True:
        raise EfficiencyReceiptError("recording requires explicit opt-in")
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "receipt_type": "actual_usage",
        "visibility": "local",
        "evidence_label": EVIDENCE_LABEL,
        "created_month": created_month or current_month(),
        "skill": {
            "version": skill_version,
            "core_sha256": normalize_sha256(core_sha256, "core_sha256"),
        },
        "study": {
            "task_class": task_class,
            "trial": trial,
            "order": order,
        },
        "measurement": {
            "source": "host-reported",
            "condition": condition,
            "provider": provider,
            "model": model,
            "adapter_version": adapter_version,
            "usage_semantics": usage_semantics,
            "usage": make_usage(
                call_count=call_count,
                input_tokens=input_tokens,
                cache_read_input_tokens=cache_read_input_tokens,
                cache_write_input_tokens=cache_write_input_tokens,
                output_tokens=output_tokens,
                reasoning_tokens=reasoning_tokens,
                tool_prompt_tokens=tool_prompt_tokens,
                provider_total_tokens=provider_total_tokens,
            ),
        },
        "controls": {
            "settings_sha256": normalize_sha256(settings_sha256, "settings_sha256"),
            "tools_sha256": normalize_sha256(tools_sha256, "tools_sha256"),
            "fixture_sha256": normalize_sha256(fixture_sha256, "fixture_sha256"),
            "oracle_sha256": normalize_sha256(oracle_sha256, "oracle_sha256"),
            "fresh_context": fresh_context,
            "same_acceptance_contract": same_acceptance_contract,
        },
        "quality": {"passed": quality_passed},
        "privacy": {
            "explicit_opt_in": True,
            "contains_content": False,
            "contains_paths": False,
            "contains_repo_or_user_identifiers": False,
        },
    }
    sealed = seal_receipt(receipt)
    return require_valid_receipt(sealed)


def calculate_token_delta(
    skill_usage: Mapping[str, int | None], baseline_usage: Mapping[str, int | None]
) -> dict[str, int | None]:
    delta: dict[str, int | None] = {}
    for name in DELTA_FIELDS:
        skill_value = skill_usage[name]
        baseline_value = baseline_usage[name]
        delta[name] = (
            baseline_value - skill_value
            if isinstance(skill_value, int)
            and not isinstance(skill_value, bool)
            and isinstance(baseline_value, int)
            and not isinstance(baseline_value, bool)
            else None
        )
    return delta


def calculate_percent_delta(skill_total: int, baseline_total: int) -> float | None:
    if baseline_total == 0:
        return None
    return round(((baseline_total - skill_total) / baseline_total) * 100.0, 6)


def create_controlled_pair(
    skill_receipt: Mapping[str, Any], baseline_receipt: Mapping[str, Any]
) -> dict[str, Any]:
    skill = require_valid_receipt(skill_receipt)
    baseline = require_valid_receipt(baseline_receipt)
    for label, receipt, expected_condition in (
        ("skill", skill, "skill"),
        ("baseline", baseline, "baseline"),
    ):
        if receipt["receipt_type"] != "actual_usage" or receipt["visibility"] != "local":
            raise EfficiencyReceiptError(f"{label} input must be a local actual_usage receipt")
        if receipt["measurement"]["condition"] != expected_condition:
            raise EfficiencyReceiptError(f"{label} input has the wrong condition")
        if receipt["quality"]["passed"] is not True:
            raise EfficiencyReceiptError(f"{label} input did not pass the acceptance oracle")
        if receipt["controls"]["fresh_context"] is not True:
            raise EfficiencyReceiptError(f"{label} input did not start from fresh context")
        if receipt["controls"]["same_acceptance_contract"] is not True:
            raise EfficiencyReceiptError(f"{label} input lacks the same-contract assertion")

    if skill["skill"] != baseline["skill"]:
        raise EfficiencyReceiptError("skill identity differs between the pair")
    if skill["study"] != baseline["study"]:
        raise EfficiencyReceiptError("study task_class, trial, or order differs between the pair")
    if skill["created_month"] != baseline["created_month"]:
        raise EfficiencyReceiptError("controlled-pair runs must use the same reporting month")
    for name in ("provider", "model", "adapter_version", "usage_semantics"):
        if skill["measurement"][name] != baseline["measurement"][name]:
            raise EfficiencyReceiptError(f"measurement.{name} differs between the pair")
    for name in LOCAL_CONTROL_FIELDS:
        if skill["controls"][name] != baseline["controls"][name]:
            raise EfficiencyReceiptError(f"controls.{name} differs between the pair")

    skill_usage = skill["measurement"]["usage"]
    baseline_usage = baseline["measurement"]["usage"]
    delta = calculate_token_delta(skill_usage, baseline_usage)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "receipt_type": "controlled_pair",
        "visibility": "local",
        "evidence_label": EVIDENCE_LABEL,
        "created_month": max(skill["created_month"], baseline["created_month"]),
        "skill": copy.deepcopy(skill["skill"]),
        "study": copy.deepcopy(skill["study"]),
        "measurement": {
            "source": "controlled-pair",
            "provider": skill["measurement"]["provider"],
            "model": skill["measurement"]["model"],
            "adapter_version": skill["measurement"]["adapter_version"],
            "usage_semantics": skill["measurement"]["usage_semantics"],
            "skill_usage": copy.deepcopy(skill_usage),
            "baseline_usage": copy.deepcopy(baseline_usage),
            "token_delta": delta,
            "percent_provider_total_delta": calculate_percent_delta(
                skill_usage["provider_total_tokens"],
                baseline_usage["provider_total_tokens"],
            ),
        },
        "controls": copy.deepcopy(skill["controls"]),
        "quality": {
            "skill_passed": True,
            "baseline_passed": True,
            "same_acceptance_contract": True,
        },
        "source_receipts": {
            "skill_receipt_id": skill["receipt_id"],
            "baseline_receipt_id": baseline["receipt_id"],
        },
        "privacy": copy.deepcopy(skill["privacy"]),
    }
    sealed = seal_receipt(receipt)
    return require_valid_receipt(sealed)


def public_comparison_digest(receipt: Mapping[str, Any]) -> str:
    controls = receipt["controls"]
    private_comparison = {
        "domain": "anti-dark-code-efficiency-public-comparison-v1",
        "study": copy.deepcopy(receipt["study"]),
        "measurement_identity": {
            "provider": receipt["measurement"]["provider"],
            "model": receipt["measurement"]["model"],
            "adapter_version": receipt["measurement"]["adapter_version"],
            "usage_semantics": receipt["measurement"]["usage_semantics"],
        },
        "private_controls": {
            name: controls[name]
            for name in LOCAL_CONTROL_FIELDS
        },
    }
    return sha256_prefixed(canonical_json_bytes(private_comparison))


def experimental_key(receipt: Mapping[str, Any]) -> tuple[str, ...]:
    """Identify one study cell without exposing its private comparison inputs."""
    controls = receipt["controls"]
    comparison = controls.get("comparison_sha256")
    if comparison is None:
        comparison = public_comparison_digest(receipt)
    return (
        receipt["skill"]["version"],
        receipt["skill"]["core_sha256"],
        receipt["measurement"]["provider"],
        receipt["measurement"]["model"],
        receipt["study"]["task_class"],
        str(receipt["study"]["trial"]),
        receipt["study"]["order"],
        comparison,
    )


def public_projection(receipt: Mapping[str, Any]) -> dict[str, Any]:
    local = require_valid_receipt(receipt)
    if local["visibility"] != "local":
        raise EfficiencyReceiptError("only a local receipt can be exported")
    public = {
        "schema_version": local["schema_version"],
        "receipt_type": local["receipt_type"],
        "visibility": "public",
        "evidence_label": local["evidence_label"],
        "created_month": local["created_month"],
        "skill": copy.deepcopy(local["skill"]),
        "study": copy.deepcopy(local["study"]),
        "measurement": copy.deepcopy(local["measurement"]),
        "controls": {
            "comparison_sha256": public_comparison_digest(local),
            "fresh_context": local["controls"]["fresh_context"],
            "same_acceptance_contract": local["controls"]["same_acceptance_contract"],
        },
        "quality": copy.deepcopy(local["quality"]),
        "privacy": copy.deepcopy(local["privacy"]),
    }
    sealed = seal_receipt(public)
    return require_valid_receipt(sealed, require_public=True)


def is_linklike(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        stat_result = path.lstat()
    except (FileNotFoundError, OSError):
        return False
    attributes = getattr(stat_result, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse)


def first_linklike_component(path: Path) -> Path | None:
    absolute = path.expanduser().absolute()
    for candidate in list(reversed(absolute.parents)) + [absolute]:
        if candidate == Path(candidate.anchor):
            continue
        if is_linklike(candidate):
            return candidate
    return None


def write_json_atomic(path: Path, value: Mapping[str, Any]) -> Path:
    destination = path.expanduser().absolute()
    linked = first_linklike_component(destination)
    if linked is not None:
        raise EfficiencyReceiptError(f"refusing output through a link-like path component: {linked.name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    linked = first_linklike_component(destination)
    if linked is not None:
        raise EfficiencyReceiptError(f"refusing output through a link-like path component: {linked.name}")
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        linked = first_linklike_component(destination)
        if linked is not None:
            raise EfficiencyReceiptError(f"refusing output through a link-like path component: {linked.name}")
        os.replace(temp_name, destination)
        temp_name = None
    finally:
        if temp_name:
            try:
                Path(temp_name).unlink()
            except FileNotFoundError:
                pass
    return destination


def load_receipt(path: Path, *, require_public: bool = False) -> dict[str, Any]:
    source = path.expanduser().absolute()
    linked = first_linklike_component(source)
    if linked is not None:
        raise EfficiencyReceiptError(f"refusing receipt through a link-like path component: {linked.name}")
    try:
        size = source.stat().st_size
    except OSError as error:
        raise EfficiencyReceiptError(f"cannot read receipt {source}: {error}") from error
    if size > MAX_RECEIPT_BYTES:
        raise EfficiencyReceiptError(f"receipt exceeds {MAX_RECEIPT_BYTES} bytes: {source}")
    try:
        value = strict_json_loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, EfficiencyReceiptError) as error:
        raise EfficiencyReceiptError(f"invalid receipt JSON {source}: {error}") from error
    return require_valid_receipt(value, require_public=require_public)


def export_public_receipt(receipt: Mapping[str, Any], output_dir: Path) -> Path:
    public = public_projection(receipt)
    digest = public["receipt_id"].removeprefix("sha256:")
    return write_json_atomic(output_dir / f"efficiency-{digest[:12]}.json", public)


def empty_summary() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "measurement_scope": "community-self-reported receipts; not provider-attested",
        "claim_boundary": (
            "Actual usage is not savings. Token deltas appear only for quality-qualified "
            "controlled pairs and are not combined across provider/model/adapter/usage-semantics/task-class strata."
        ),
        "as_of_month": None,
        "receipt_counts": {
            "actual_usage": 0,
            "controlled_pairs": 0,
            "duplicates_ignored": 0,
        },
        "strata": [],
    }


def rounded_median(values: list[float]) -> float | None:
    if not values:
        return None
    return round(float(statistics.median(values)), 6)


def aggregate_receipts(
    receipts: Iterable[Mapping[str, Any]], *, require_public: bool = True
) -> dict[str, Any]:
    unique: dict[str, dict[str, Any]] = {}
    duplicates = 0
    for raw in receipts:
        receipt = require_valid_receipt(raw, require_public=require_public)
        receipt_id = receipt["receipt_id"]
        if receipt_id in unique:
            duplicates += 1
            continue
        unique[receipt_id] = receipt

    experiments: dict[tuple[str, ...], str] = {}
    for receipt_id, receipt in unique.items():
        key = experimental_key(receipt)
        if key in experiments:
            raise EfficiencyReceiptError(
                "distinct community receipts claim the same experimental identity"
            )
        experiments[key] = receipt_id

    summary = empty_summary()
    summary["receipt_counts"]["duplicates_ignored"] = duplicates
    if unique:
        summary["as_of_month"] = max(receipt["created_month"] for receipt in unique.values())

    strata: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for receipt in sorted(unique.values(), key=lambda item: item["receipt_id"]):
        measurement = receipt["measurement"]
        key = (
            measurement["provider"],
            measurement["model"],
            measurement["adapter_version"],
            measurement["usage_semantics"],
            receipt["study"]["task_class"],
        )
        stratum = strata.setdefault(
            key,
            {
                "provider": key[0],
                "model": key[1],
                "adapter_version": key[2],
                "usage_semantics": key[3],
                "task_class": key[4],
                "evidence_label": EVIDENCE_LABEL,
                "actual_usage": {
                    "receipts": 0,
                    "by_condition": {
                        "skill": {
                            "receipts": 0,
                            "provider_total_tokens": 0,
                        },
                        "baseline": {
                            "receipts": 0,
                            "provider_total_tokens": 0,
                        },
                    },
                },
                "controlled_pairs": {
                    "pairs": 0,
                    "skill_provider_total_tokens": 0,
                    "baseline_provider_total_tokens": 0,
                    "quality_qualified_token_delta": 0,
                    "positive_delta_pairs": 0,
                    "zero_delta_pairs": 0,
                    "negative_delta_pairs": 0,
                    "median_percent_provider_total_delta": None,
                },
                "_percent_values": [],
            },
        )
        if receipt["receipt_type"] == "actual_usage":
            summary["receipt_counts"]["actual_usage"] += 1
            stratum["actual_usage"]["receipts"] += 1
            condition = measurement["condition"]
            condition_usage = stratum["actual_usage"]["by_condition"][condition]
            condition_usage["receipts"] += 1
            condition_usage["provider_total_tokens"] += measurement["usage"]["provider_total_tokens"]
            continue

        summary["receipt_counts"]["controlled_pairs"] += 1
        pair = stratum["controlled_pairs"]
        pair["pairs"] += 1
        skill_total = measurement["skill_usage"]["provider_total_tokens"]
        baseline_total = measurement["baseline_usage"]["provider_total_tokens"]
        delta = measurement["token_delta"]["provider_total_tokens"]
        pair["skill_provider_total_tokens"] += skill_total
        pair["baseline_provider_total_tokens"] += baseline_total
        pair["quality_qualified_token_delta"] += delta
        if delta > 0:
            pair["positive_delta_pairs"] += 1
        elif delta < 0:
            pair["negative_delta_pairs"] += 1
        else:
            pair["zero_delta_pairs"] += 1
        percent = measurement["percent_provider_total_delta"]
        if percent is not None:
            stratum["_percent_values"].append(percent)

    for key in sorted(strata):
        stratum = strata[key]
        stratum["controlled_pairs"]["median_percent_provider_total_delta"] = rounded_median(
            stratum.pop("_percent_values")
        )
        summary["strata"].append(stratum)
    return summary


def ledger_receipts(ledger: Path) -> list[dict[str, Any]]:
    root = ledger.expanduser().absolute()
    if not root.is_dir() or first_linklike_component(root) is not None:
        raise EfficiencyReceiptError(f"ledger must be a real directory: {root}")
    receipts: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.json"), key=lambda item: item.as_posix()):
        linked = first_linklike_component(path)
        if linked is not None:
            raise EfficiencyReceiptError(f"ledger contains a link-like path component: {linked.name}")
        receipt = load_receipt(path, require_public=True)
        match = PUBLIC_RECEIPT_FILENAME_RE.fullmatch(path.name)
        digest = receipt["receipt_id"].removeprefix("sha256:")
        if not match or match.group(1) != digest[:12]:
            raise EfficiencyReceiptError(f"public receipt filename does not match its content identity: {path.name}")
        receipts.append(receipt)
    return receipts


def aggregate_ledger(ledger: Path) -> dict[str, Any]:
    return aggregate_receipts(ledger_receipts(ledger), require_public=True)


def git_paths(repo: Path, args: Sequence[str]) -> list[str]:
    try:
        process = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            timeout=20,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        raise EfficiencyReceiptError("could not inspect the candidate Git change") from error
    if process.returncode != 0:
        raise EfficiencyReceiptError("could not inspect the candidate Git change")
    return [
        item.decode("utf-8", errors="surrogateescape")
        for item in process.stdout.split(b"\0")
        if item
    ]


def resolve_git_commit(repo: Path, ref: str) -> str:
    if not isinstance(ref, str) or not ref or CONTROL_PATTERN.search(ref):
        raise EfficiencyReceiptError("changed-from must name a Git commit or ref")
    try:
        process = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "rev-parse",
                "--verify",
                "--end-of-options",
                f"{ref}^{{commit}}",
            ],
            capture_output=True,
            timeout=20,
            check=False,
            text=True,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        raise EfficiencyReceiptError("could not resolve the candidate Git base") from error
    commit = process.stdout.strip()
    if process.returncode != 0 or not re.fullmatch(r"[0-9a-fA-F]{40,64}", commit):
        raise EfficiencyReceiptError("could not resolve the candidate Git base")
    return commit.lower()


def expected_summary_text(summary: Mapping[str, Any]) -> str:
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


def validate_ledger_change(
    *,
    repo: Path,
    ledger: Path,
    changed_from: str,
    summary_path: Path,
    docs_summary_path: Path,
    allow_workflow_maintenance: bool = False,
) -> tuple[list[str], int]:
    repo = repo.expanduser().resolve()
    ledger = ledger.expanduser().resolve()
    summary_path = summary_path.expanduser().resolve()
    docs_summary_path = docs_summary_path.expanduser().resolve()
    try:
        ledger_rel = ledger.relative_to(repo).as_posix().rstrip("/") + "/"
        summary_rel = summary_path.relative_to(repo).as_posix()
        docs_summary_rel = docs_summary_path.relative_to(repo).as_posix()
    except ValueError:
        return ["ledger and summaries must be inside the candidate repository"], 0

    try:
        base_commit = resolve_git_commit(repo, changed_from)
        comparison = f"{base_commit}...HEAD"
        changed = git_paths(repo, ["diff", "--name-only", "-z", comparison, "--"])
        added = git_paths(repo, ["diff", "--name-only", "-z", "--diff-filter=A", comparison, "--"])
    except EfficiencyReceiptError as error:
        return [str(error)], 0
    new_receipts = sorted(path for path in added if path.startswith(ledger_rel))
    if not new_receipts:
        if allow_workflow_maintenance and set(changed) == {".github/workflows/efficiency-ledger.yml"}:
            return [], 0
        return ["a receipt PR must add exactly one public ledger receipt"], 0
    expected_prefix = re.escape(ledger_rel)
    if any(not re.fullmatch(expected_prefix + r"efficiency-[0-9a-f]{12}\.json", path) for path in new_receipts):
        return ["the added ledger path must use the canonical efficiency-<12hex>.json name"], len(new_receipts)
    allowed = set(new_receipts) | {summary_rel, docs_summary_rel}
    if len(new_receipts) != 1 or set(changed) != allowed:
        return ["a receipt PR must add one ledger receipt and update only the two generated summaries"], len(new_receipts)
    try:
        summary = aggregate_ledger(ledger)
    except EfficiencyReceiptError as error:
        return [str(error)], len(new_receipts)
    expected = expected_summary_text(summary)
    for path, label in ((summary_path, "metrics summary"), (docs_summary_path, "website summary")):
        try:
            actual = path.read_bytes()
        except OSError:
            return [f"{label} is missing or unreadable"], len(new_receipts)
        if actual != expected.encode("utf-8"):
            return [f"{label} is stale; regenerate it from the complete public ledger"], len(new_receipts)
    return [], len(new_receipts)


def validate_ledger_pr(
    *, repo: Path, changed_from: str, allow_workflow_maintenance: bool = False
) -> tuple[list[str], int]:
    root = repo.expanduser().absolute()
    return validate_ledger_change(
        repo=root,
        ledger=root / "metrics" / "ledger",
        changed_from=changed_from,
        summary_path=root / "metrics" / "summary.json",
        docs_summary_path=root / "docs" / "data" / "efficiency-summary.json",
        allow_workflow_maintenance=allow_workflow_maintenance,
    )


def add_identity_arguments(
    parser: argparse.ArgumentParser, *, suppress_skill_identity_help: bool = False
) -> None:
    injected_help = argparse.SUPPRESS if suppress_skill_identity_help else None
    parser.add_argument("--skill-version", required=True, help=injected_help)
    parser.add_argument("--core-sha256", required=True, help=injected_help)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--adapter-version", default="manual-v1")
    parser.add_argument("--usage-semantics", required=True)
    parser.add_argument("--settings-sha256", required=True)
    parser.add_argument("--tools-sha256", required=True)
    parser.add_argument("--fixture-sha256", required=True)
    parser.add_argument("--oracle-sha256", required=True)
    parser.add_argument("--task-class", choices=TASK_CLASSES, required=True)
    parser.add_argument("--trial", type=int, required=True)
    parser.add_argument("--order", choices=STUDY_ORDERS, required=True)


def add_usage_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--call-count", type=int, default=1)
    parser.add_argument("--input-tokens", type=int)
    parser.add_argument("--cache-read-input-tokens", type=int)
    parser.add_argument("--cache-write-input-tokens", type=int)
    parser.add_argument("--output-tokens", type=int)
    parser.add_argument("--reasoning-tokens", type=int)
    parser.add_argument("--tool-prompt-tokens", type=int)
    parser.add_argument("--provider-total-tokens", type=int, required=True)


def command_record(args: argparse.Namespace) -> int:
    receipt = create_actual_receipt(
        explicit_opt_in=args.opt_in,
        condition=args.condition,
        skill_version=args.skill_version,
        core_sha256=args.core_sha256,
        provider=args.provider,
        model=args.model,
        adapter_version=args.adapter_version,
        usage_semantics=args.usage_semantics,
        settings_sha256=args.settings_sha256,
        tools_sha256=args.tools_sha256,
        fixture_sha256=args.fixture_sha256,
        oracle_sha256=args.oracle_sha256,
        fresh_context=args.fresh_context,
        same_acceptance_contract=args.same_acceptance_contract,
        quality_passed=args.quality_passed,
        task_class=args.task_class,
        trial=args.trial,
        order=args.order,
        created_month=args.month,
        call_count=args.call_count,
        input_tokens=args.input_tokens,
        cache_read_input_tokens=args.cache_read_input_tokens,
        cache_write_input_tokens=args.cache_write_input_tokens,
        output_tokens=args.output_tokens,
        reasoning_tokens=args.reasoning_tokens,
        tool_prompt_tokens=args.tool_prompt_tokens,
        provider_total_tokens=args.provider_total_tokens,
    )
    path = write_json_atomic(Path(args.out), receipt)
    print(f"RECORDED actual usage receipt: {path}")
    return 0


def command_pair(args: argparse.Namespace) -> int:
    receipt = create_controlled_pair(
        load_receipt(Path(args.skill_receipt)),
        load_receipt(Path(args.baseline_receipt)),
    )
    path = write_json_atomic(Path(args.out), receipt)
    delta = receipt["measurement"]["token_delta"]["provider_total_tokens"]
    print(f"PAIRED community/self-reported receipt: delta={delta:+d} tokens -> {path}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    failures = 0
    for value in args.receipts:
        try:
            receipt = load_receipt(Path(value), require_public=args.require_public)
        except EfficiencyReceiptError as error:
            failures += 1
            print(f"INVALID {value}: {error}", file=sys.stderr)
        else:
            print(f"VALID {receipt['receipt_type']} {value}")
    return 1 if failures else 0


def command_export(args: argparse.Namespace) -> int:
    path = export_public_receipt(load_receipt(Path(args.receipt)), Path(args.out_dir))
    print(f"EXPORTED privacy-stripped public receipt: {path}")
    return 0


def command_aggregate(args: argparse.Namespace) -> int:
    summary = aggregate_ledger(Path(args.ledger))
    path = write_json_atomic(Path(args.out), summary)
    for mirror in args.mirror_out:
        write_json_atomic(Path(mirror), summary)
    counts = summary["receipt_counts"]
    print(
        "AGGREGATED community/self-reported ledger: "
        f"actual={counts['actual_usage']}, pairs={counts['controlled_pairs']}, "
        f"duplicates={counts['duplicates_ignored']} -> {path}"
    )
    return 0


def command_validate_ledger_pr(args: argparse.Namespace) -> int:
    errors, additions = validate_ledger_pr(
        repo=Path(args.repo),
        changed_from=args.changed_from,
        allow_workflow_maintenance=args.allow_workflow_maintenance,
    )
    for error in errors:
        print(f"INVALID ledger change: {error}", file=sys.stderr)
    if errors:
        return 1
    if additions:
        print("VALID ledger change: one public receipt and both deterministic summaries")
    else:
        print("VALID internal workflow maintenance: no public receipt claimed")
    return 0


def build_parser(*, suppress_injected_identity_help: bool = False) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="adc_efficiency.py",
        description="Offline, opt-in Anti-Dark-Code efficiency receipts",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    record = sub.add_parser("record", help="Record explicit host-reported numeric usage")
    record.add_argument("--out", required=True)
    record.add_argument("--opt-in", action="store_true", help="Confirm explicit local receipt creation")
    record.add_argument("--condition", choices=("skill", "baseline"), required=True)
    record.add_argument("--month", help="Coarse UTC month in YYYY-MM; defaults to current month")
    record.add_argument("--fresh-context", action="store_true")
    record.add_argument("--same-acceptance-contract", action="store_true")
    record.add_argument("--quality-passed", action="store_true")
    add_identity_arguments(record, suppress_skill_identity_help=suppress_injected_identity_help)
    add_usage_arguments(record)
    record.set_defaults(func=command_record)

    pair = sub.add_parser("pair", help="Form a quality-qualified controlled pair")
    pair.add_argument("--skill-receipt", required=True)
    pair.add_argument("--baseline-receipt", required=True)
    pair.add_argument("--out", required=True)
    pair.set_defaults(func=command_pair)

    validate = sub.add_parser("validate", help="Validate receipt structure and content integrity")
    validate.add_argument("receipts", nargs="+")
    validate.add_argument("--require-public", action="store_true")
    validate.set_defaults(func=command_validate)

    export = sub.add_parser("export", help="Write a privacy-stripped content-hashed public receipt")
    export.add_argument("--receipt", required=True)
    export.add_argument("--out-dir", required=True)
    export.set_defaults(func=command_export)

    aggregate = sub.add_parser("aggregate", help="Aggregate a public receipt ledger deterministically")
    aggregate.add_argument("--ledger", required=True)
    aggregate.add_argument("--out", required=True)
    aggregate.add_argument("--mirror-out", "--mirror", dest="mirror_out", action="append", default=[])
    aggregate.set_defaults(func=command_aggregate)

    ledger_pr = sub.add_parser("validate-ledger-pr", help="Validate one public receipt PR and its generated summaries")
    ledger_pr.add_argument("--repo", required=True)
    ledger_pr.add_argument("--changed-from", required=True)
    ledger_pr.add_argument("--allow-workflow-maintenance", action="store_true")
    ledger_pr.set_defaults(func=command_validate_ledger_pr)
    return parser


def main(
    argv: Sequence[str] | None = None, *, suppress_injected_identity_help: bool = False
) -> int:
    parser = build_parser(suppress_injected_identity_help=suppress_injected_identity_help)
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except EfficiencyReceiptError as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
