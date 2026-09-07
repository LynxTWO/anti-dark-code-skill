#!/usr/bin/env python3
"""Pure, bounded adapters for opted-in local Codex and Claude usage rows.

Rows are already-decoded JSON objects supplied by the private collector.  This
module never reads files and deliberately retains only hashes, model metadata,
and bounded context needed to associate a later usage record with a turn.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re
from typing import Any, Iterable


USAGE_KEYS = (
    "input_tokens",
    "cache_read_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_tokens",
    "provider_total_tokens",
)
_CONTEXT_LIMIT = 32
_METADATA_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/:-]{0,127}$")


def _digest(*parts: str) -> str:
    return hashlib.sha256(":".join(parts).encode("utf-8")).hexdigest()


def _native_hash(host: str, kind: str, value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return _digest(host, kind, value)


def _codex_scope(session_id: object, thread_id: object) -> str | None:
    session_hash = _native_hash("codex", "session", session_id)
    thread_hash = _native_hash("codex", "thread", thread_id)
    if session_hash is None or thread_hash is None:
        return None
    return _digest("codex", "scope", session_hash, thread_hash)


def _codex_context_key(scope_hash: str, turn_hash: str) -> str:
    return _digest("codex", "context", scope_hash, turn_hash)


def _counter(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _usage_counter(mapping: dict[str, Any], name: str) -> tuple[bool, int | None]:
    """Return whether *name* was present and its valid integer value."""
    if name not in mapping:
        return False, None
    return True, _counter(mapping[name])


def _timestamp(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    text = value[:-1] + "+00:00" if value.endswith(("Z", "z")) else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _diagnose(diagnostics: dict[str, int], label: str) -> None:
    diagnostics[label] = diagnostics.get(label, 0) + 1


def _string(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _metadata(value: object, diagnostics: dict[str, int]) -> str | None:
    """Accept only compact technical identifiers, never arbitrary source text."""
    text = _string(value)
    if text is None:
        return None
    if _METADATA_IDENTIFIER.fullmatch(text) is None:
        _diagnose(diagnostics, "invalid_metadata")
        return None
    return text


def _bounded_put(mapping: dict[str, Any], key: str, value: Any) -> None:
    mapping.pop(key, None)
    mapping[key] = value
    while len(mapping) > _CONTEXT_LIMIT:
        mapping.pop(next(iter(mapping)))


def _initial_codex_state(state: object) -> dict[str, Any]:
    """Read only the narrow, serializable state shape this adapter owns."""
    result: dict[str, Any] = {
        "contexts": {}, "reroutes": {}, "sessions": {}, "active_scope": None,
        "seen_modern_usage": False,
    }
    if not isinstance(state, dict) or not isinstance(state.get("codex"), dict):
        return result
    candidate = state["codex"]
    for name in ("contexts", "reroutes"):
        source = candidate.get(name)
        if not isinstance(source, dict):
            continue
        target = result[name]
        for key, value in list(source.items())[-_CONTEXT_LIMIT:]:
            if not isinstance(key, str):
                continue
            if name == "contexts" and isinstance(value, dict):
                target[key] = {
                    field: value[field]
                    for field in ("model", "effort", "root_task_id")
                    if field in value and (
                        value[field] is None
                        or (field == "root_task_id" and isinstance(value[field], str) and re.fullmatch(r"[0-9a-f]{64}", value[field]))
                        or (field in {"model", "effort"} and isinstance(value[field], str) and _METADATA_IDENTIFIER.fullmatch(value[field]))
                    )
                }
            elif name == "reroutes" and isinstance(value, str) and _METADATA_IDENTIFIER.fullmatch(value):
                target[key] = value
    source_sessions = candidate.get("sessions")
    if isinstance(source_sessions, dict):
        for scope, value in list(source_sessions.items())[-_CONTEXT_LIMIT:]:
            if (not isinstance(scope, str) or re.fullmatch(r"[0-9a-f]{64}", scope) is None
                    or not isinstance(value, dict)):
                continue
            thread_hash = value.get("thread_hash")
            if not isinstance(thread_hash, str) or re.fullmatch(r"[0-9a-f]{64}", thread_hash) is None:
                continue
            session = {"thread_hash": thread_hash}
            for field in ("provider", "host_version"):
                item = value.get(field)
                if isinstance(item, str) and _METADATA_IDENTIFIER.fullmatch(item):
                    session[field] = item
            if value.get("role") in {"agent", "subagent", "approval-review", "unknown"}:
                session["role"] = value["role"]
            result["sessions"][scope] = session
    active_scope = candidate.get("active_scope")
    if isinstance(active_scope, str) and active_scope in result["sessions"]:
        result["active_scope"] = active_scope
    result["seen_modern_usage"] = candidate.get("seen_modern_usage") is True
    return result


def _role_from_session(payload: dict[str, Any]) -> str:
    source = payload.get("source")
    if isinstance(source, dict) and source.get("subagent") is not None:
        return "subagent"
    model = _string(payload.get("model"))
    if model == "codex-auto-review":
        return "approval-review"
    return "agent"


def _empty_usage() -> dict[str, int | None]:
    return {key: None for key in USAGE_KEYS}


def _codex_usage(source: object) -> tuple[dict[str, int | None] | None, str | None]:
    if not isinstance(source, dict):
        return None, "legacy_usage_unsupported"
    names = {
        "input_tokens": "input_tokens",
        "cached_input_tokens": "cache_read_input_tokens",
        "cache_write_input_tokens": "cache_write_input_tokens",
        "output_tokens": "output_tokens",
        "reasoning_output_tokens": "reasoning_tokens",
        "total_tokens": "provider_total_tokens",
    }
    usage = _empty_usage()
    present = False
    for raw_name, normalized in names.items():
        exists, value = _usage_counter(source, raw_name)
        present = present or exists
        if exists and value is None:
            return None, "invalid_usage_counter"
        if exists:
            usage[normalized] = value
    if not present or (usage["input_tokens"] is None and usage["output_tokens"] is None):
        return None, "legacy_usage_unsupported"
    return usage, None


def _codex_event(
    payload: dict[str, Any], stamp: str, state: dict[str, Any], diagnostics: dict[str, int],
) -> dict[str, Any] | None:
    response_id = _string(payload.get("response_id"))
    if response_id is None:
        _diagnose(diagnostics, "legacy_usage_unsupported")
        return None
    usage, issue = _codex_usage(payload.get("usage"))
    if issue is not None:
        _diagnose(diagnostics, issue)
        return None
    turn_id = _string(payload.get("turn_id"))
    turn_hash = _native_hash("codex", "turn", turn_id)
    scope_hash = _codex_scope(payload.get("session_id"), payload.get("thread_id"))
    matched_session = state["sessions"].get(scope_hash, {}) if scope_hash else {}
    context_key = _codex_context_key(scope_hash, turn_hash) if scope_hash and turn_hash else None
    context = state["contexts"].get(context_key, {}) if context_key else {}
    if turn_hash and scope_hash:
        task_id = _digest("codex", "task", scope_hash, turn_hash)
        task_scope = "turn"
    elif turn_hash:
        task_id = _digest("codex", "task", turn_hash)
        task_scope = "request"
    else:
        task_id = _digest("codex", "task", _digest("response", response_id))
        task_scope = "request"
    root_raw = _string(payload.get("root_turn_id"))
    root_task_id = _native_hash("codex", "root", root_raw)
    if root_task_id is None:
        root_task_id = context.get("root_task_id") if isinstance(context, dict) else None
    if not isinstance(root_task_id, str):
        root_task_id = task_id
    reported_model = _metadata(payload.get("model"), diagnostics)
    rerouted = state["reroutes"].get(context_key) if context_key else None
    if reported_model is not None:
        model, model_source = reported_model, "usage"
    elif isinstance(rerouted, str):
        model, model_source = rerouted, "rerouted"
    elif isinstance(context, dict) and isinstance(context.get("model"), str):
        model, model_source = context["model"], "turn-context"
    else:
        model, model_source = None, "unknown"
    role = None
    if model == "codex-auto-review":
        role = "approval-review"
    if role not in {"agent", "subagent", "approval-review"}:
        role = matched_session.get("role", "unknown") if isinstance(matched_session, dict) else "unknown"
    if role not in {"agent", "subagent", "approval-review"}:
        role = "unknown"
    event: dict[str, Any] = {
        "event_id": _digest("codex", "response", response_id),
        "task_id": task_id,
        "root_task_id": root_task_id,
        "timestamp": stamp,
        "provider": matched_session.get("provider") if isinstance(matched_session, dict) else None,
        "model": model,
        "model_source": model_source,
        "effort": context.get("effort") if isinstance(context, dict) else None,
        "role": role,
        "usage_semantics": "codex-response-inclusive-v1",
        "task_scope": task_scope,
        "usage": usage,
    }
    version = matched_session.get("host_version") if isinstance(matched_session, dict) else None
    if isinstance(version, str):
        event["host_version"] = version
    return event


def _parse_codex(rows: Iterable[object], state: object) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, int]]:
    codex = _initial_codex_state(state)
    events: list[dict[str, Any]] = []
    diagnostics: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            _diagnose(diagnostics, "malformed_row")
            continue
        row_type = _string(row.get("type"))
        if row_type not in {"session_meta", "turn_context", "model/rerouted", "token_usage_record"}:
            if row_type == "event_msg":
                payload = row.get("payload")
                if isinstance(payload, dict) and payload.get("type") == "token_count":
                    _diagnose(diagnostics, "cumulative_notifications_ignored")
            continue
        payload = row.get("payload")
        if not isinstance(payload, dict):
            _diagnose(diagnostics, "malformed_row")
            continue
        stamp = _timestamp(row.get("timestamp"))
        if stamp is None:
            _diagnose(diagnostics, "invalid_timestamp")
            continue
        if row_type == "session_meta":
            codex["active_scope"] = None
            scope_hash = _codex_scope(payload.get("session_id"), payload.get("id"))
            if scope_hash is None:
                continue
            provider = _metadata(payload.get("model_provider"), diagnostics)
            version = _metadata(payload.get("cli_version"), diagnostics)
            session = {
                "thread_hash": _native_hash("codex", "thread", payload.get("id")),
                "role": _role_from_session(payload),
            }
            if provider:
                session["provider"] = provider
            if version:
                session["host_version"] = version
            _bounded_put(codex["sessions"], scope_hash, session)
            codex["active_scope"] = scope_hash
        elif row_type == "turn_context":
            turn_hash = _native_hash("codex", "turn", payload.get("turn_id"))
            scope_hash = codex.get("active_scope")
            if turn_hash is None:
                _diagnose(diagnostics, "missing_usage_identity")
                continue
            if not isinstance(scope_hash, str) or scope_hash not in codex["sessions"]:
                continue
            root_task = _native_hash("codex", "root", payload.get("root_turn_id"))
            context = {
                "model": _metadata(payload.get("model"), diagnostics),
                "effort": _metadata(payload.get("effort"), diagnostics),
                "root_task_id": root_task,
            }
            _bounded_put(codex["contexts"], _codex_context_key(scope_hash, turn_hash), context)
        elif row_type == "model/rerouted":
            turn_hash = _native_hash("codex", "turn", payload.get("turnId") or payload.get("turn_id"))
            scope_hash = codex.get("active_scope")
            active_session = codex["sessions"].get(scope_hash) if isinstance(scope_hash, str) else None
            reroute_thread = _native_hash("codex", "thread", payload.get("threadId") or payload.get("thread_id"))
            target = _metadata(payload.get("toModel") or payload.get("to_model"), diagnostics)
            if (turn_hash and target and isinstance(scope_hash, str) and isinstance(active_session, dict)
                    and reroute_thread == active_session.get("thread_hash")):
                _bounded_put(codex["reroutes"], _codex_context_key(scope_hash, turn_hash), target)
        elif row_type == "token_usage_record":
            event = _codex_event(payload, stamp, codex, diagnostics)
            if event is not None:
                codex["seen_modern_usage"] = True
                events.append(event)
    return {"codex": codex}, events, diagnostics


def _claude_usage(source: object) -> tuple[dict[str, int | None] | None, str | None]:
    if not isinstance(source, dict):
        return None, "incomplete_claude_usage"
    raw_names = {
        "input_tokens": "input_tokens",
        "cache_read_input_tokens": "cache_read_input_tokens",
        "cache_creation_input_tokens": "cache_write_input_tokens",
        "output_tokens": "output_tokens",
    }
    raw: dict[str, int | None] = {}
    for name in raw_names:
        exists, value = _usage_counter(source, name)
        if exists and value is None:
            return None, "invalid_usage_counter"
        raw[name] = value if exists else None
    if "iterations" in source:
        iterations = source["iterations"]
        if (not isinstance(iterations, list) or len(iterations) != 1
                or not isinstance(iterations[0], dict) or iterations[0].get("type") != "message"):
            return None, "unsupported_compaction_usage"
        mirrored = iterations[0]
        for name in raw_names:
            exists, value = _usage_counter(mirrored, name)
            if not exists or value is None or raw[name] is None or value != raw[name]:
                return None, "unsupported_compaction_usage"
    if all(value is None for value in raw.values()):
        return None, "incomplete_claude_usage"
    usage = _empty_usage()
    usage["cache_read_input_tokens"] = raw["cache_read_input_tokens"]
    usage["cache_write_input_tokens"] = raw["cache_creation_input_tokens"]
    usage["output_tokens"] = raw["output_tokens"]
    details = source.get("output_tokens_details")
    if isinstance(details, dict) and "thinking_tokens" in details:
        thinking = _counter(details["thinking_tokens"])
        if thinking is None:
            return None, "invalid_usage_counter"
        usage["reasoning_tokens"] = thinking
    complete_input = all(raw[name] is not None for name in (
        "input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens",
    ))
    if complete_input:
        usage["input_tokens"] = sum(raw[name] for name in (
            "input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens",
        ) if raw[name] is not None)
        if usage["output_tokens"] is not None:
            usage["provider_total_tokens"] = usage["input_tokens"] + usage["output_tokens"]
        return usage, None
    return usage, "incomplete_claude_usage"


def _parse_claude(rows: Iterable[object], state: object) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, int]]:
    del state  # Claude rows carry all currently supported attribution.
    events: list[dict[str, Any]] = []
    diagnostics: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            _diagnose(diagnostics, "malformed_row")
            continue
        message = row.get("message")
        if not isinstance(message, dict):
            continue
        if "usage" not in message:
            continue
        stamp = _timestamp(row.get("timestamp"))
        if stamp is None:
            _diagnose(diagnostics, "invalid_timestamp")
            continue
        usage, issue = _claude_usage(message.get("usage"))
        if issue == "unsupported_compaction_usage":
            _diagnose(diagnostics, issue)
            continue
        if usage is None:
            _diagnose(diagnostics, issue or "incomplete_claude_usage")
            continue
        if issue:
            _diagnose(diagnostics, issue)
        # message.id is the only observed per-message response identity.  A
        # requestId fallback could create a second event when a later stream
        # snapshot supplies the message ID.
        message_id = _string(message.get("id"))
        if message_id is None:
            _diagnose(diagnostics, "missing_usage_identity")
            continue
        session_hash = _native_hash("claude", "session", row.get("sessionId"))
        request_hash = _native_hash("claude", "request", row.get("requestId")) or _native_hash("claude", "message", message_id)
        task_id = _digest("claude", "task", session_hash, request_hash) if session_hash else _digest("claude", "task", request_hash)
        # Request/message IDs describe transport linkage, not a verified human task.
        root_task_id = task_id
        model = _metadata(message.get("model"), diagnostics)
        role = "agent" if row.get("type") == "assistant" else "unknown"
        events.append({
            "event_id": _digest("claude", "anthropic", message_id),
            "task_id": task_id,
            "root_task_id": root_task_id,
            "timestamp": stamp,
            "provider": "anthropic",
            "model": model,
            "model_source": "usage" if model else "unknown",
            "effort": None,
            "role": role,
            "usage_semantics": "claude-message-inclusive-v1",
            "task_scope": "request",
            "usage": usage,
        })
    return {}, events, diagnostics


def parse_rows(rows: Iterable[object], host: str, state: dict[str, Any] | None = None) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, int]]:
    """Normalize a finite sequence of decoded source rows without retaining content."""
    if host == "codex":
        return _parse_codex(rows, state)
    if host == "claude":
        return _parse_claude(rows, state)
    return {}, [], {"unsupported_host": 1}
