from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "adc_model_policy.py"
CATALOG = Path(__file__).resolve().parents[1] / "assets" / "model-policy.json"


def policy():
    spec = importlib.util.spec_from_file_location("adc_model_policy", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def catalog() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def request(**overrides: object) -> dict:
    value: dict = {
        "available_models": [
            {"id": "gpt-5.6-luna", "controls": ["tools"], "efforts": ["low", "medium"]},
            {"id": "gpt-5.6-terra", "controls": ["tools"], "efforts": ["medium", "high"]},
            {"id": "gpt-5.6-sol", "controls": ["tools"], "efforts": ["high", "xhigh", "ultra"]},
            {"id": "gpt-6-astra", "controls": ["tools"], "efforts": ["high", "xhigh", "ultra"]},
        ],
        "current_model": "gpt-6-astra",
        "can_select": True,
        "switch_authorized": True,
        "task_class": "bounded",
        "has_oracle": True,
        "verification_failed": False,
        "required_controls": ["tools"],
    }
    value.update(overrides)
    return value


class ModelPolicyTests(unittest.TestCase):
    def test_failure_escalation_still_meets_the_task_quality_floor(self) -> None:
        result = policy().select_model_policy(
            request(current_model="gpt-5.6-luna", task_class="consequential",
                    verification_failed=True, failure_evidence="acceptance-check-1"),
            catalog(), today=date(2026, 9, 7))
        self.assertEqual("strong", result["target_tier"])
        self.assertEqual("gpt-5.6-sol", result["model"])

    def test_module_and_catalog_exist(self) -> None:
        """Removing either standalone local policy artifact breaks its public boundary."""
        self.assertTrue(SCRIPT.is_file())
        self.assertTrue(CATALOG.is_file())

    def test_snapshot_preserves_exact_documented_model_ids(self) -> None:
        """Changing an alias or replacing an exact identifier would make dated attribution ambiguous."""
        self.assertEqual(
            {
                "gpt-6-astra", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna",
                "gpt-daybreak-blue-latest",
            },
            set(catalog()["models"]),
        )

    def test_bounded_checkable_work_selects_live_economy_model(self) -> None:
        """Changing tier ordering or ignoring availability would choose Terra or an absent model."""
        result = policy().select_model_policy(request(), catalog(), today=date(2026, 9, 7))
        self.assertEqual("select", result["action"])
        self.assertEqual("gpt-5.6-luna", result["model"])
        self.assertEqual("economy", result["target_tier"])

    def test_routine_scoped_work_selects_standard_model(self) -> None:
        """Treating routine work as economy would downshift this explicitly scoped task."""
        result = policy().select_model_policy(
            request(task_class="routine"), catalog(), today=date(2026, 9, 7)
        )
        self.assertEqual("gpt-5.6-terra", result["model"])
        self.assertEqual("standard", result["target_tier"])

    def test_consequential_work_keeps_current_strong_model(self) -> None:
        """A cost-first route would incorrectly replace Astra during a consequential task."""
        result = policy().select_model_policy(
            request(task_class="consequential"), catalog(), today=date(2026, 9, 7)
        )
        self.assertEqual("keep-current", result["action"])
        self.assertEqual("gpt-6-astra", result["model"])
        self.assertEqual("current-satisfies-strong", result["reason"])

    def test_no_oracle_keeps_current_even_when_an_economy_route_is_available(self) -> None:
        """Dropping the oracle guard would automatically send uncertain work to Luna."""
        result = policy().select_model_policy(
            request(has_oracle=False), catalog(), today=date(2026, 9, 7)
        )
        self.assertEqual("keep-current", result["action"])
        self.assertEqual("no-acceptance-oracle", result["reason"])

    def test_host_without_selection_control_keeps_current(self) -> None:
        """Ignoring host capability would claim a model switch the caller cannot make."""
        result = policy().select_model_policy(
            request(can_select=False), catalog(), today=date(2026, 9, 7)
        )
        self.assertEqual("keep-current", result["action"])
        self.assertEqual("host-selection-unavailable", result["reason"])

    def test_user_selected_parent_model_is_preserved_without_switch_authority(self) -> None:
        """Treating host capability as user authority would replace the selected parent model."""
        result = policy().select_model_policy(
            request(switch_authorized=False), catalog(), today=date(2026, 9, 7)
        )
        self.assertEqual("keep-current", result["action"])
        self.assertEqual("model-switch-not-authorized", result["reason"])

    def test_required_control_must_be_reported_by_live_host_metadata(self) -> None:
        """Using catalog capabilities as live host truth would select a model with no reported tool control."""
        available = [
            {"id": "gpt-5.6-luna", "controls": [], "efforts": ["low"]},
            {"id": "gpt-5.6-terra", "controls": [], "efforts": ["medium"]},
        ]
        result = policy().select_model_policy(
            request(available_models=available, current_model="gpt-5.6-terra"),
            catalog(),
            today=date(2026, 9, 7),
        )
        self.assertEqual("keep-current", result["action"])
        self.assertEqual("no-live-eligible-model", result["reason"])

    def test_exact_effort_value_must_be_supported_without_equating_ultra_and_max(self) -> None:
        """Normalizing the host's exact effort value would silently route with a different setting."""
        available = [
            {"id": "gpt-5.6-luna", "controls": ["tools"], "efforts": ["low", "max"]},
            {"id": "gpt-6-astra", "controls": ["tools"], "efforts": ["ultra"]},
        ]
        result = policy().select_model_policy(
            request(available_models=available, required_effort="ultra"),
            catalog(),
            today=date(2026, 9, 7),
        )
        self.assertEqual("keep-current", result["action"])
        self.assertEqual("no-live-eligible-model", result["reason"])

    def test_evidence_backed_failure_escalates_once_and_counts_both_attempts(self) -> None:
        """Ignoring a real verification failure would leave the second attempt on the standard tier."""
        result = policy().select_model_policy(
            request(
                current_model="gpt-5.6-terra",
                task_class="routine",
                verification_failed=True,
                failure_evidence="acceptance-check: failing-test-log",
            ),
            catalog(),
            today=date(2026, 9, 7),
        )
        self.assertEqual("select", result["action"])
        self.assertEqual("gpt-5.6-sol", result["model"])
        self.assertEqual("strong", result["target_tier"])
        self.assertEqual(2, result["attempts_to_record"])
        self.assertEqual(0, result["remaining_escalations"])

    def test_consequential_route_never_falls_back_to_cheaper_standard_tier(self) -> None:
        """Allowing a standard fallback would select Terra when no live strong model exists."""
        available = [{"id": "gpt-5.6-terra", "controls": ["tools"], "efforts": ["medium"]}]
        result = policy().select_model_policy(
            request(available_models=available, current_model="gpt-5.6-terra", task_class="consequential"),
            catalog(),
            today=date(2026, 9, 7),
        )
        self.assertEqual("keep-current", result["action"])
        self.assertEqual("no-live-eligible-model", result["reason"])

    def test_stale_or_unknown_cost_catalog_keeps_current(self) -> None:
        """Treating old or unranked pricing as current evidence would downshift this task."""
        stale = catalog()
        stale["checked_on"] = "2026-01-01"
        result = policy().select_model_policy(request(), stale, today=date(2026, 9, 7))
        self.assertEqual("keep-current", result["action"])
        self.assertEqual("catalog-stale", result["reason"])

        unknown_rank = catalog()
        unknown_rank["models"]["gpt-5.6-luna"].pop("relative_cost_rank")
        result = policy().select_model_policy(request(), unknown_rank, today=date(2026, 9, 7))
        self.assertEqual("keep-current", result["action"])
        self.assertEqual("cost-rank-unknown", result["reason"])

    def test_future_catalog_date_is_refused(self) -> None:
        """Accepting a future snapshot would treat unavailable pricing evidence as current."""
        future = catalog()
        future["checked_on"] = "2026-09-08"
        result = policy().select_model_policy(request(), future, today=date(2026, 9, 7))
        self.assertEqual("keep-current", result["action"])
        self.assertEqual("catalog-future", result["reason"])

    def test_nonfinite_cost_rank_is_refused(self) -> None:
        """Ordering a NaN rank can make selection depend on input order rather than cost evidence."""
        invalid = catalog()
        invalid["models"]["gpt-5.6-luna"]["relative_cost_rank"] = float("nan")
        result = policy().select_model_policy(request(), invalid, today=date(2026, 9, 7))
        self.assertEqual("keep-current", result["action"])
        self.assertEqual("cost-rank-unknown", result["reason"])

    def test_downshift_requires_a_strictly_lower_cost_rank(self) -> None:
        """A nominal economy tier cannot replace the current model when its rank is more expensive."""
        expensive = catalog()
        expensive["models"]["gpt-5.6-luna"]["relative_cost_rank"] = 5
        result = policy().select_model_policy(request(), expensive, today=date(2026, 9, 7))
        self.assertEqual("keep-current", result["action"])
        self.assertEqual("no-cheaper-eligible-model", result["reason"])

    def test_existing_escalation_count_prevents_another_failure_route(self) -> None:
        """Ignoring a persisted escalation count would permit repeated retries after failure."""
        result = policy().select_model_policy(
            request(
                current_model="gpt-5.6-terra", task_class="routine", verification_failed=True,
                failure_evidence="acceptance-check: failing-test-log", escalation_count=1,
            ),
            catalog(), today=date(2026, 9, 7),
        )
        self.assertEqual("keep-current", result["action"])
        self.assertEqual("escalation-limit-reached", result["reason"])

    def test_malformed_catalog_is_refused_without_throwing(self) -> None:
        """A permissive parser could make routing decisions from malformed local metadata."""
        result = policy().select_model_policy(request(), {"checked_on": "nope"}, today=date(2026, 9, 7))
        self.assertEqual("keep-current", result["action"])
        self.assertEqual("catalog-invalid", result["reason"])

    def test_cli_only_prints_a_json_recommendation(self) -> None:
        """Changing the offline CLI contract would make it invoke work instead of returning a decision."""
        process = subprocess.run(
            [
                sys.executable, str(SCRIPT), "--catalog", str(CATALOG),
                "--available", "gpt-5.6-luna", "--available", "gpt-5.6-terra",
                "--current", "gpt-5.6-terra", "--task", "bounded", "--can-select", "--has-oracle",
                "--switch-authorized",
            ],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual("gpt-5.6-luna", json.loads(process.stdout)["model"])

    def test_cli_request_json_accepts_live_control_metadata(self) -> None:
        """A bare repeated model ID cannot prove the tool support required for this route."""
        request_json = json.dumps({
            "available_models": [{"id": "gpt-5.6-luna", "controls": ["tools"]}],
            "current_model": "gpt-6-astra", "can_select": True, "switch_authorized": True,
            "task_class": "bounded", "has_oracle": True, "required_controls": ["tools"],
        })
        process = subprocess.run(
            [sys.executable, str(SCRIPT), "--catalog", str(CATALOG), "--request", request_json],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual("gpt-5.6-luna", json.loads(process.stdout)["model"])

    def test_cli_malformed_request_json_has_a_fixed_conservative_reason(self) -> None:
        """Leaking a parser exception would make host integrations handle an unstable failure contract."""
        process = subprocess.run(
            [sys.executable, str(SCRIPT), "--catalog", str(CATALOG), "--request", "{"],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual("request-json-invalid", json.loads(process.stdout)["reason"])

    def test_request_json_over_size_cap_is_refused(self) -> None:
        """Removing the input cap would let a host integration feed unbounded metadata to the helper."""
        self.assertIsNone(policy()._load_request_json("x" * (policy().MAX_REQUEST_BYTES + 1)))


if __name__ == "__main__":
    unittest.main()
