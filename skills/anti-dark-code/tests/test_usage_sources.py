from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "adc_usage_sources.py"


def adapter():
    spec = importlib.util.spec_from_file_location("adc_usage_sources", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UsageSourceTests(unittest.TestCase):
    def test_credential_shaped_metadata_is_not_retained(self) -> None:
        credential = "sk-proj-synthetic-example-never-a-real-key"
        state, events, diagnostics = adapter().parse_rows([
            {"timestamp": "2026-09-07T19:00:00Z", "type": "session_meta",
             "payload": {"id": "thread-c", "session_id": "session-c", "model_provider": credential}},
            {"timestamp": "2026-09-07T19:00:01Z", "type": "turn_context",
             "payload": {"turn_id": "turn-c", "model": credential, "effort": credential}},
            {"timestamp": "2026-09-07T19:00:02Z", "type": "token_usage_record",
             "payload": {"thread_id": "thread-c", "session_id": "session-c", "turn_id": "turn-c",
                         "response_id": "response-c", "usage": {"input_tokens": 1, "output_tokens": 2}}},
        ], "codex")
        self.assertEqual(1, len(events))
        self.assertNotIn(credential, json.dumps([state, events, diagnostics]))
        self.assertIsNone(events[0]["model"])
        self.assertIsNone(events[0]["provider"])

    def test_adapter_module_exists(self) -> None:
        """The collector's pure source boundary is a standalone stdlib module."""
        self.assertTrue(SCRIPT.is_file())

    def test_codex_response_uses_context_and_hashes_native_identifiers(self) -> None:
        """Removing context or hashing would make this modern per-response case fail."""
        rows = [
            {
                "timestamp": "2026-09-07T15:01:02+00:00",
                "type": "session_meta",
                "payload": {
                    "id": "thread-private-17",
                    "session_id": "session-private-17",
                    "parent_thread_id": "parent-private-17",
                    "model_provider": "openai",
                    "cli_version": "0.153.0",
                    "source": {"subagent": {"id": "private-child"}},
                    "base_instructions": "never retain this prompt",
                    "cwd": "C:/private/repository",
                },
            },
            {
                "timestamp": "2026-09-07T15:01:03Z",
                "type": "turn_context",
                "payload": {
                    "turn_id": "turn-private-17",
                    "root_turn_id": "root-private-17",
                    "model": "gpt-6-astra",
                    "effort": "xhigh",
                },
            },
            {
                "timestamp": "2026-09-07T15:01:04.000Z",
                "type": "token_usage_record",
                "payload": {
                    "thread_id": "thread-private-17",
                    "turn_id": "turn-private-17",
                    "session_id": "session-private-17",
                    "root_turn_id": "root-private-17",
                    "response_id": "response-private-17",
                    "usage": {
                        "input_tokens": 12,
                        "cached_input_tokens": 5,
                        "cache_write_input_tokens": 3,
                        "output_tokens": 7,
                        "reasoning_output_tokens": 2,
                        "total_tokens": 19,
                    },
                },
            },
        ]

        state, events, diagnostics = adapter().parse_rows(rows, "codex")

        self.assertEqual({}, diagnostics)
        self.assertEqual(1, len(events))
        event = events[0]
        self.assertEqual("2026-09-07T15:01:04Z", event["timestamp"])
        self.assertEqual("openai", event["provider"])
        self.assertEqual("gpt-6-astra", event["model"])
        self.assertEqual("turn-context", event["model_source"])
        self.assertEqual("xhigh", event["effort"])
        self.assertEqual("subagent", event["role"])
        self.assertEqual("codex-response-inclusive-v1", event["usage_semantics"])
        self.assertEqual("turn", event["task_scope"])
        self.assertEqual(
            {
                "input_tokens": 12,
                "cache_read_input_tokens": 5,
                "cache_write_input_tokens": 3,
                "output_tokens": 7,
                "reasoning_tokens": 2,
                "provider_total_tokens": 19,
            },
            event["usage"],
        )
        for key in ("event_id", "task_id", "root_task_id"):
            self.assertRegex(event[key], r"^[0-9a-f]{64}$")
        self.assertEqual(
            hashlib.sha256(b"codex:response:response-private-17").hexdigest(),
            event["event_id"],
        )
        serialized = json.dumps({"state": state, "events": events, "diagnostics": diagnostics})
        for forbidden in ("private-17", "private-child", "private/repository", "never retain"):
            self.assertNotIn(forbidden, serialized)

    def test_codex_replay_keeps_same_event_id_for_ledger_deduplication(self) -> None:
        """Changing the response identity would defeat durable cross-file replay handling."""
        rows = [
            {"timestamp": "2026-09-07T15:01:03Z", "type": "turn_context",
             "payload": {"turn_id": "turn-1", "root_turn_id": "root-1", "model": "gpt-5.6-terra"}},
            {"timestamp": "2026-09-07T15:01:04Z", "type": "token_usage_record",
             "payload": {"thread_id": "thread-1", "turn_id": "turn-1", "root_turn_id": "root-1",
                         "response_id": "response-1", "usage": {"input_tokens": 1, "output_tokens": 2}}},
        ]
        state, first, _ = adapter().parse_rows(rows, "codex")
        state, second, diagnostics = adapter().parse_rows(rows, "codex", state)
        self.assertEqual(1, len(first))
        self.assertEqual(1, len(second))
        self.assertEqual(first[0]["event_id"], second[0]["event_id"])
        self.assertEqual({}, diagnostics)

    def test_codex_context_survives_an_incremental_parse_boundary(self) -> None:
        """Dropping bounded turn context would leave a later response model unknown."""
        context_rows = [
            {"timestamp": "2026-09-07T15:01:00Z", "type": "session_meta",
             "payload": {"id": "thread-boundary", "session_id": "session-boundary",
                         "model_provider": "openai", "source": {"subagent": {}}}},
            {"timestamp": "2026-09-07T15:01:01Z", "type": "turn_context",
             "payload": {"turn_id": "turn-boundary", "root_turn_id": "root-boundary",
                         "model": "gpt-5.6-sol", "effort": "high"}},
        ]
        state, events, diagnostics = adapter().parse_rows(context_rows, "codex")
        self.assertEqual([], events)
        self.assertEqual({}, diagnostics)
        state, events, diagnostics = adapter().parse_rows([
            {"timestamp": "2026-09-07T15:01:02Z", "type": "token_usage_record",
             "payload": {"thread_id": "thread-boundary", "turn_id": "turn-boundary",
                         "session_id": "session-boundary", "root_turn_id": "root-boundary", "response_id": "response-boundary",
                         "usage": {"input_tokens": 2, "output_tokens": 3}}},
        ], "codex", state)
        self.assertEqual({}, diagnostics)
        self.assertEqual("gpt-5.6-sol", events[0]["model"])
        self.assertEqual("high", events[0]["effort"])
        self.assertEqual("subagent", events[0]["role"])
        self.assertNotIn("boundary", json.dumps(state))

    def test_codex_reroute_is_associated_with_later_usage(self) -> None:
        """Ignoring an evidenced reroute would preserve the requested rather than served model."""
        rows = [
            {"timestamp": "2026-09-07T15:00:59Z", "type": "session_meta",
             "payload": {"id": "thread-2", "session_id": "session-2", "model_provider": "openai"}},
            {"timestamp": "2026-09-07T15:01:00Z", "type": "turn_context",
             "payload": {"turn_id": "turn-2", "root_turn_id": "root-2", "model": "gpt-5.6-sol"}},
            {"timestamp": "2026-09-07T15:01:01Z", "type": "model/rerouted",
             "payload": {"threadId": "thread-2", "turnId": "turn-2", "fromModel": "gpt-5.6-sol", "toModel": "gpt-6-astra"}},
            {"timestamp": "2026-09-07T15:01:02Z", "type": "token_usage_record",
             "payload": {"thread_id": "thread-2", "turn_id": "turn-2", "root_turn_id": "root-2",
                         "session_id": "session-2", "response_id": "response-2", "usage": {"input_tokens": 2, "output_tokens": 3}}},
        ]
        _, events, diagnostics = adapter().parse_rows(rows, "codex")
        self.assertEqual({}, diagnostics)
        self.assertEqual("gpt-6-astra", events[0]["model"])
        self.assertEqual("rerouted", events[0]["model_source"])

    def test_codex_response_model_overrides_reroute_metadata(self) -> None:
        """A direct serving-model record is stronger evidence than a turn-level reroute."""
        rows = [
            {"timestamp": "2026-09-07T15:00:59Z", "type": "session_meta",
             "payload": {"id": "thread-direct", "session_id": "session-direct", "model_provider": "openai"}},
            {"timestamp": "2026-09-07T15:01:00Z", "type": "turn_context",
             "payload": {"turn_id": "turn-direct", "root_turn_id": "root-direct", "model": "requested-model"}},
            {"timestamp": "2026-09-07T15:01:01Z", "type": "model/rerouted",
             "payload": {"threadId": "thread-direct", "turnId": "turn-direct", "toModel": "rerouted-model"}},
            {"timestamp": "2026-09-07T15:01:02Z", "type": "token_usage_record",
             "payload": {"thread_id": "thread-direct", "session_id": "session-direct", "turn_id": "turn-direct",
                         "response_id": "response-direct", "model": "served-model",
                         "usage": {"input_tokens": 2, "output_tokens": 3}}},
        ]
        _, events, diagnostics = adapter().parse_rows(rows, "codex")
        self.assertEqual({}, diagnostics)
        self.assertEqual("served-model", events[0]["model"])
        self.assertEqual("usage", events[0]["model_source"])

    def test_codex_ignores_cumulative_notification_and_marks_old_format_unsupported(self) -> None:
        """Treating either notification as a response would double count historical usage."""
        rows = [
            {"timestamp": "2026-09-07T15:01:00Z", "type": "event_msg",
             "payload": {"type": "token_count", "info": {"total_tokens": 1234, "message": "private text"}}},
            {"timestamp": "2026-09-07T15:01:01Z", "type": "token_usage_record",
             "payload": {"thread_id": "thread-3", "turn_id": "turn-3", "usage": {"total_tokens": 1234}}},
        ]
        _, events, diagnostics = adapter().parse_rows(rows, "codex")
        self.assertEqual([], events)
        self.assertEqual(
            {"cumulative_notifications_ignored": 1, "legacy_usage_unsupported": 1}, diagnostics,
        )

    def test_codex_mirror_chunk_after_modern_usage_is_only_informational(self) -> None:
        """Classifying a later mirror as legacy would create a false coverage failure."""
        state, events, diagnostics = adapter().parse_rows([
            {"timestamp": "2026-09-07T15:01:00Z", "type": "token_usage_record",
             "payload": {"thread_id": "thread-4", "turn_id": "turn-4", "response_id": "response-4",
                         "usage": {"input_tokens": 2, "output_tokens": 3}}},
        ], "codex")
        self.assertEqual(1, len(events))
        self.assertEqual({}, diagnostics)
        state, events, diagnostics = adapter().parse_rows([
            {"timestamp": "2026-09-07T15:01:01Z", "type": "event_msg",
             "payload": {"type": "token_count", "info": {"total_tokens": 5}}},
        ], "codex", state)
        self.assertEqual([], events)
        self.assertEqual({"cumulative_notifications_ignored": 1}, diagnostics)
        self.assertTrue(state["codex"]["seen_modern_usage"])

    def test_invalid_usage_and_timestamp_are_skipped_without_echoing_input(self) -> None:
        """Accepting bool counters or invalid dates would contaminate durable usage data."""
        rows = [
            {"timestamp": "not-a-date-secret", "type": "token_usage_record",
             "payload": {"thread_id": "thread-secret", "turn_id": "turn-secret", "response_id": "response-secret",
                         "usage": {"input_tokens": 1, "output_tokens": 2}}},
            {"timestamp": "2026-09-07T15:01:02Z", "type": "token_usage_record",
             "payload": {"thread_id": "thread-secret", "turn_id": "turn-secret", "response_id": "response-secret",
                         "usage": {"input_tokens": True, "output_tokens": 2}}},
        ]
        state, events, diagnostics = adapter().parse_rows(rows, "codex")
        self.assertEqual([], events)
        self.assertEqual({"invalid_timestamp": 1, "invalid_usage_counter": 1}, diagnostics)
        self.assertNotIn("secret", json.dumps(state))
        self.assertNotIn("secret", json.dumps(diagnostics))

    def test_claude_normalizes_cache_categories_and_keeps_repeated_stream_identity(self) -> None:
        """Changing a stream request identity would make ledger upsert unable to coalesce it."""
        row = {
            "timestamp": "2026-09-07T15:02:00-04:00",
            "type": "assistant",
            "sessionId": "claude-session-private",
            "parentUuid": "claude-parent-private",
            "requestId": "request-private-4",
            "message": {
                "id": "message-private-4",
                "model": "claude-sonnet-4-5",
                "usage": {
                    "input_tokens": 10,
                    "cache_read_input_tokens": 5,
                    "cache_creation_input_tokens": 3,
                    "output_tokens": 7,
                    "output_tokens_details": {"thinking_tokens": 2},
                },
            },
        }
        state, events, diagnostics = adapter().parse_rows([row, row], "claude")
        self.assertEqual({}, diagnostics)
        self.assertEqual(2, len(events))
        self.assertEqual(events[0]["event_id"], events[1]["event_id"])
        event = events[0]
        self.assertEqual("2026-09-07T19:02:00Z", event["timestamp"])
        self.assertEqual("anthropic", event["provider"])
        self.assertEqual("claude-sonnet-4-5", event["model"])
        self.assertEqual("usage", event["model_source"])
        self.assertEqual("agent", event["role"])
        self.assertEqual("claude-message-inclusive-v1", event["usage_semantics"])
        self.assertEqual("request", event["task_scope"])
        self.assertEqual(event["task_id"], event["root_task_id"])
        self.assertEqual(
            {
                "input_tokens": 18,
                "cache_read_input_tokens": 5,
                "cache_write_input_tokens": 3,
                "output_tokens": 7,
                "reasoning_tokens": 2,
                "provider_total_tokens": 25,
            }, event["usage"],
        )
        serialized = json.dumps({"state": state, "events": events})
        self.assertNotIn("private", serialized)

    def test_claude_missing_cache_breakdown_makes_inclusive_input_unknown(self) -> None:
        """Inventing zero cache counts changes the meaning of an absent source field."""
        rows = [{
            "timestamp": "2026-09-07T19:02:00Z", "sessionId": "session-5", "requestId": "request-5",
            "message": {"id": "message-5", "model": "claude-haiku", "usage": {"input_tokens": 10, "output_tokens": 7}},
        }]
        _, events, diagnostics = adapter().parse_rows(rows, "claude")
        self.assertEqual({"incomplete_claude_usage": 1}, diagnostics)
        self.assertIsNone(events[0]["usage"]["input_tokens"])
        self.assertIsNone(events[0]["usage"]["cache_read_input_tokens"])
        self.assertIsNone(events[0]["usage"]["cache_write_input_tokens"])
        self.assertIsNone(events[0]["usage"]["reasoning_tokens"])
        self.assertIsNone(events[0]["usage"]["provider_total_tokens"])

    def test_claude_partial_row_without_message_identity_cannot_split_a_message(self) -> None:
        """Using requestId first and message.id later would double count one streamed message."""
        partial = {
            "timestamp": "2026-09-07T19:02:00Z", "type": "assistant", "sessionId": "session-identity",
            "requestId": "request-identity", "message": {"model": "claude-haiku", "usage": {
                "input_tokens": 1, "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0, "output_tokens": 2,
            }},
        }
        complete = json.loads(json.dumps(partial))
        complete["message"]["id"] = "message-identity"
        _, events, diagnostics = adapter().parse_rows([partial, complete], "claude")
        self.assertEqual(1, len(events))
        self.assertEqual({"missing_usage_identity": 1}, diagnostics)
        self.assertEqual(
            hashlib.sha256(b"claude:anthropic:message-identity").hexdigest(), events[0]["event_id"],
        )

    def test_claude_compaction_iterations_are_explicitly_unsupported(self) -> None:
        """Reporting top-level usage when iterations exist would understate compaction consumption."""
        rows = [{
            "timestamp": "2026-09-07T19:02:00Z", "sessionId": "session-6", "requestId": "request-6",
            "message": {"id": "message-6", "model": "claude-sonnet", "usage": {
                "input_tokens": 10, "output_tokens": 7, "iterations": [{"input_tokens": 1, "output_tokens": 2}],
            }},
        }]
        _, events, diagnostics = adapter().parse_rows(rows, "claude")
        self.assertEqual([], events)
        self.assertEqual({"unsupported_compaction_usage": 1}, diagnostics)

    def test_claude_single_message_iteration_matching_top_level_is_not_compaction(self) -> None:
        """Discarding the verified one-entry mirror would lose ordinary current Claude usage."""
        rows = [{
            "timestamp": "2026-09-07T19:02:00Z", "type": "assistant", "sessionId": "session-iteration",
            "requestId": "request-iteration", "message": {"id": "message-iteration", "model": "claude-sonnet",
            "usage": {
                "input_tokens": 2, "cache_read_input_tokens": 592,
                "cache_creation_input_tokens": 29715, "output_tokens": 12167,
                "output_tokens_details": {"thinking_tokens": 900},
                "iterations": [{
                    "type": "message", "input_tokens": 2, "cache_read_input_tokens": 592,
                    "cache_creation_input_tokens": 29715, "output_tokens": 12167,
                    "cache_creation": {"ephemeral_5m_input_tokens": 29715},
                }],
            }},
        }]
        _, events, diagnostics = adapter().parse_rows(rows, "claude")
        self.assertEqual({}, diagnostics)
        self.assertEqual(1, len(events))
        self.assertEqual(30309, events[0]["usage"]["input_tokens"])
        self.assertEqual(42476, events[0]["usage"]["provider_total_tokens"])
        self.assertEqual(900, events[0]["usage"]["reasoning_tokens"])

    def test_unknown_host_and_malformed_row_are_bounded_diagnostics(self) -> None:
        """An unsupported source must not raise or serialize its untrusted contents."""
        state, events, diagnostics = adapter().parse_rows(["private raw record"], "unrecognized")
        self.assertEqual([], events)
        self.assertEqual({"unsupported_host": 1}, diagnostics)
        self.assertEqual({}, state)

    def test_malformed_known_host_row_is_a_label_not_an_exception(self) -> None:
        """Dereferencing an incomplete host record would make collection brittle."""
        state, events, diagnostics = adapter().parse_rows([{
            "timestamp": "2026-09-07T19:02:00Z", "type": "token_usage_record",
        }], "codex")
        self.assertEqual([], events)
        self.assertEqual({"malformed_row": 1}, diagnostics)
        self.assertNotIn("token_usage_record", json.dumps(state))

    def test_ordinary_nonusage_rows_do_not_become_usage_diagnostics(self) -> None:
        """Counting chat input as malformed usage would make source coverage look worse."""
        state, events, diagnostics = adapter().parse_rows([
            {"timestamp": "2026-09-07T19:02:00Z", "type": "user", "payload": {"text": "private"}},
        ], "codex")
        self.assertEqual([], events)
        self.assertEqual({}, diagnostics)
        self.assertEqual({}, state["codex"]["contexts"])
        state, events, diagnostics = adapter().parse_rows([
            {"timestamp": "2026-09-07T19:02:00Z", "type": "user", "message": {"content": "private"}},
        ], "claude")
        self.assertEqual(({}, [], {}), (state, events, diagnostics))

    def test_source_metadata_is_bounded_to_technical_identifiers(self) -> None:
        """Allowing arbitrary model text would retain source content in emitted metadata."""
        secret_model = "private prompt text " + ("x" * 200)
        _, events, diagnostics = adapter().parse_rows([
            {"timestamp": "2026-09-07T19:02:00Z", "type": "token_usage_record",
             "payload": {"thread_id": "thread-7", "turn_id": "turn-7", "response_id": "response-7",
                         "model": secret_model, "usage": {"input_tokens": 2, "output_tokens": 3}}},
        ], "codex")
        self.assertEqual({"invalid_metadata": 1}, diagnostics)
        self.assertIsNone(events[0]["model"])
        self.assertEqual("unknown", events[0]["model_source"])
        self.assertNotIn("private prompt", json.dumps(events))

    def test_codex_without_a_turn_and_scope_is_request_scoped(self) -> None:
        """Calling an unlinked response a task would inflate feedback denominators."""
        _, events, diagnostics = adapter().parse_rows([
            {"timestamp": "2026-09-07T19:02:00Z", "type": "token_usage_record",
             "payload": {"response_id": "response-unlinked", "usage": {"input_tokens": 2, "output_tokens": 3}}},
        ], "codex")
        self.assertEqual({}, diagnostics)
        self.assertEqual("request", events[0]["task_scope"])

    def test_codex_response_identity_is_independent_of_provider_metadata(self) -> None:
        """Including optional provider metadata in the ID would defeat copied-log replay protection."""
        response = {"timestamp": "2026-09-07T19:02:00Z", "type": "token_usage_record",
                    "payload": {"thread_id": "thread-stable", "session_id": "session-stable",
                                "turn_id": "turn-stable", "response_id": "response-stable",
                                "usage": {"input_tokens": 2, "output_tokens": 3}}}
        state, first, diagnostics = adapter().parse_rows([response], "codex")
        self.assertEqual({}, diagnostics)
        self.assertIsNone(first[0]["provider"])
        state, second, diagnostics = adapter().parse_rows([
            {"timestamp": "2026-09-07T19:01:58Z", "type": "session_meta",
             "payload": {"id": "thread-stable", "session_id": "session-stable", "model_provider": "acme"}},
            {"timestamp": "2026-09-07T19:01:59Z", "type": "turn_context",
             "payload": {"turn_id": "turn-stable", "root_turn_id": "root-stable", "model": "model-stable"}},
            response,
        ], "codex", state)
        self.assertEqual({}, diagnostics)
        self.assertEqual(first[0]["event_id"], second[0]["event_id"])
        self.assertEqual(hashlib.sha256(b"codex:response:response-stable").hexdigest(), second[0]["event_id"])
        self.assertEqual("acme", second[0]["provider"])

    def test_codex_reused_turn_cannot_leak_context_between_scopes(self) -> None:
        """A turn ID alone is not a session identity and must not cross-attribute models."""
        rows = [
            {"timestamp": "2026-09-07T19:00:00Z", "type": "session_meta",
             "payload": {"id": "thread-a", "session_id": "session-a", "model_provider": "provider-a"}},
            {"timestamp": "2026-09-07T19:00:01Z", "type": "turn_context",
             "payload": {"turn_id": "shared-turn", "root_turn_id": "root-a", "model": "model-a"}},
            {"timestamp": "2026-09-07T19:00:02Z", "type": "model/rerouted",
             "payload": {"threadId": "thread-a", "turnId": "shared-turn", "toModel": "served-a"}},
            {"timestamp": "2026-09-07T19:00:04Z", "type": "session_meta",
             "payload": {"id": "thread-b", "session_id": "session-b", "model_provider": "provider-b"}},
            {"timestamp": "2026-09-07T19:00:05Z", "type": "turn_context",
             "payload": {"turn_id": "shared-turn", "root_turn_id": "root-b", "model": "model-b"}},
            {"timestamp": "2026-09-07T19:00:06Z", "type": "model/rerouted",
             "payload": {"threadId": "thread-b", "turnId": "shared-turn", "toModel": "served-b"}},
            {"timestamp": "2026-09-07T19:00:07Z", "type": "token_usage_record",
             "payload": {"thread_id": "thread-a", "session_id": "session-a", "turn_id": "shared-turn",
                         "response_id": "response-a", "usage": {"input_tokens": 2, "output_tokens": 3}}},
            {"timestamp": "2026-09-07T19:00:07Z", "type": "token_usage_record",
             "payload": {"thread_id": "thread-b", "session_id": "session-b", "turn_id": "shared-turn",
                         "response_id": "response-b", "usage": {"input_tokens": 5, "output_tokens": 7}}},
        ]
        _, events, diagnostics = adapter().parse_rows(rows, "codex")
        self.assertEqual({}, diagnostics)
        self.assertEqual(["provider-a", "provider-b"], [event["provider"] for event in events])
        self.assertEqual(["served-a", "served-b"], [event["model"] for event in events])
        self.assertEqual(["rerouted", "rerouted"], [event["model_source"] for event in events])
        self.assertNotEqual(events[0]["root_task_id"], events[1]["root_task_id"])


if __name__ == "__main__":
    unittest.main()
