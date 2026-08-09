from __future__ import annotations

import copy
import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "adc_efficiency.py"
SPEC = importlib.util.spec_from_file_location("adc_efficiency", SCRIPT)
assert SPEC and SPEC.loader
efficiency = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(efficiency)

DIGESTS = {
    "core": "1" * 64,
    "settings": "2" * 64,
    "tools": "3" * 64,
    "fixture": "4" * 64,
    "oracle": "5" * 64,
}


class EfficiencyReceiptTests(unittest.TestCase):
    def git(self, repo: Path, *args: str) -> str:
        process = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return process.stdout.strip()

    def initialize_receipt_repo(self, repo: Path) -> tuple[Path, Path, Path, str]:
        ledger = repo / "metrics" / "ledger"
        ledger.mkdir(parents=True)
        summary_path = repo / "metrics" / "summary.json"
        docs_summary = repo / "docs" / "data" / "efficiency-summary.json"
        empty = efficiency.empty_summary()
        efficiency.write_json_atomic(summary_path, empty)
        efficiency.write_json_atomic(docs_summary, empty)
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        self.git(repo, "config", "user.email", "tests@example.invalid")
        self.git(repo, "config", "user.name", "ADC Tests")
        self.git(repo, "config", "core.autocrlf", "false")
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-qm", "base")
        return ledger, summary_path, docs_summary, self.git(repo, "rev-parse", "HEAD")

    def commit_valid_receipt_change(
        self,
        repo: Path,
        ledger: Path,
        summary_path: Path,
        docs_summary: Path,
    ) -> Path:
        receipt_path = efficiency.export_public_receipt(self.actual("skill", 10), ledger)
        current = efficiency.aggregate_ledger(ledger)
        efficiency.write_json_atomic(summary_path, current)
        efficiency.write_json_atomic(docs_summary, current)
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-qm", "receipt")
        return receipt_path

    def actual(
        self,
        condition: str,
        total: int,
        *,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        provider: str = "openai",
        model: str = "model-a",
        adapter_version: str = "manual-v1",
        usage_semantics: str = "provider-reported-v1",
        quality_passed: bool = True,
        fresh_context: bool = True,
        same_contract: bool = True,
        fixture_sha256: str = DIGESTS["fixture"],
        task_class: str = "audit",
        trial: int = 1,
        order: str = "skill-first",
    ) -> dict:
        return efficiency.create_actual_receipt(
            explicit_opt_in=True,
            condition=condition,
            skill_version="2026.08.09-unified.5",
            core_sha256=DIGESTS["core"],
            provider=provider,
            model=model,
            adapter_version=adapter_version,
            usage_semantics=usage_semantics,
            settings_sha256=DIGESTS["settings"],
            tools_sha256=DIGESTS["tools"],
            fixture_sha256=fixture_sha256,
            oracle_sha256=DIGESTS["oracle"],
            fresh_context=fresh_context,
            same_acceptance_contract=same_contract,
            quality_passed=quality_passed,
            task_class=task_class,
            trial=trial,
            order=order,
            provider_total_tokens=total,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            created_month="2026-08",
        )

    def public(self, receipt: dict) -> dict:
        return efficiency.public_projection(receipt)

    def test_zero_is_preserved_and_null_is_not_invented(self) -> None:
        receipt = self.actual("skill", 0, input_tokens=0, output_tokens=0)
        usage = receipt["measurement"]["usage"]
        self.assertEqual(usage["input_tokens"], 0)
        self.assertEqual(usage["output_tokens"], 0)
        self.assertEqual(usage["provider_total_tokens"], 0)
        self.assertIsNone(usage["cache_read_input_tokens"])
        self.assertEqual(efficiency.validate_receipt(receipt), [])

    def test_recording_requires_explicit_opt_in(self) -> None:
        with self.assertRaisesRegex(efficiency.EfficiencyReceiptError, "explicit opt-in"):
            efficiency.create_actual_receipt(
                explicit_opt_in=False,
                condition="skill",
                skill_version="v1",
                core_sha256=DIGESTS["core"],
                provider="openai",
                model="model-a",
                adapter_version="manual-v1",
                usage_semantics="provider-reported-v1",
                settings_sha256=DIGESTS["settings"],
                tools_sha256=DIGESTS["tools"],
                fixture_sha256=DIGESTS["fixture"],
                oracle_sha256=DIGESTS["oracle"],
                fresh_context=True,
                same_acceptance_contract=True,
                quality_passed=True,
                provider_total_tokens=1,
                task_class="audit",
                trial=1,
                order="skill-first",
            )

    def test_invalid_extreme_and_inconsistent_counts_are_rejected(self) -> None:
        for value in (-1, efficiency.MAX_TOKEN_COUNT + 1):
            with self.subTest(value=value):
                with self.assertRaises(efficiency.EfficiencyReceiptError):
                    self.actual("skill", value)
        with self.assertRaisesRegex(efficiency.EfficiencyReceiptError, "must equal"):
            self.actual("skill", 12, input_tokens=5, output_tokens=6)
        for trial in (0, efficiency.MAX_TRIAL + 1):
            with self.subTest(trial=trial):
                with self.assertRaisesRegex(efficiency.EfficiencyReceiptError, "study.trial"):
                    self.actual("skill", 1, trial=trial)
        with self.assertRaisesRegex(efficiency.EfficiencyReceiptError, "task_class"):
            self.actual("skill", 1, task_class="unknown")
        receipt = self.actual("skill", 1)
        receipt["measurement"]["usage"]["call_count"] = True
        receipt = efficiency.seal_receipt(receipt)
        self.assertTrue(any("call_count" in item for item in efficiency.validate_receipt(receipt)))

    def test_unknown_fields_and_content_tampering_are_rejected(self) -> None:
        receipt = self.actual("skill", 10)
        receipt["prompt"] = "private text"
        errors = efficiency.validate_receipt(receipt)
        self.assertTrue(any("unsupported fields" in item for item in errors))
        self.assertTrue(any("content hash" in item for item in errors))

        tampered = self.actual("skill", 10)
        tampered["measurement"]["usage"]["provider_total_tokens"] = 11
        self.assertTrue(any("content hash" in item for item in efficiency.validate_receipt(tampered)))

    def test_controlled_pair_requires_comparable_identity_and_controls(self) -> None:
        skill = self.actual("skill", 80)
        cases = (
            self.actual("baseline", 100, provider="anthropic"),
            self.actual("baseline", 100, model="model-b"),
            self.actual("baseline", 100, fixture_sha256="6" * 64),
            self.actual("baseline", 100, task_class="verify"),
            self.actual("baseline", 100, trial=2),
            self.actual("baseline", 100, order="baseline-first"),
        )
        for baseline in cases:
            with self.subTest(
                provider=baseline["measurement"]["provider"],
                model=baseline["measurement"]["model"],
                fixture=baseline["controls"]["fixture_sha256"],
            ):
                with self.assertRaises(efficiency.EfficiencyReceiptError):
                    efficiency.create_controlled_pair(skill, baseline)

    def test_controlled_pair_requires_quality_freshness_and_same_contract(self) -> None:
        skill = self.actual("skill", 80)
        for baseline in (
            self.actual("baseline", 100, quality_passed=False),
            self.actual("baseline", 100, fresh_context=False),
            self.actual("baseline", 100, same_contract=False),
        ):
            with self.assertRaises(efficiency.EfficiencyReceiptError):
                efficiency.create_controlled_pair(skill, baseline)

    def test_controlled_pair_requires_the_same_reporting_month(self) -> None:
        skill = self.actual("skill", 80)
        baseline = self.actual("baseline", 100)
        baseline["created_month"] = "2026-07"
        baseline = efficiency.seal_receipt(baseline)
        with self.assertRaisesRegex(efficiency.EfficiencyReceiptError, "same reporting month"):
            efficiency.create_controlled_pair(skill, baseline)

    def test_public_controlled_pair_requires_true_controls(self) -> None:
        public = self.public(efficiency.create_controlled_pair(
            self.actual("skill", 80), self.actual("baseline", 100)
        ))
        public["controls"]["fresh_context"] = False
        public["controls"]["same_acceptance_contract"] = False
        public = efficiency.seal_receipt(public)
        errors = efficiency.validate_receipt(public, require_public=True)
        self.assertTrue(any("controls.fresh_context must be true" in item for item in errors), errors)
        self.assertTrue(any("controls.same_acceptance_contract must be true" in item for item in errors), errors)
        with self.assertRaises(efficiency.EfficiencyReceiptError):
            efficiency.aggregate_receipts([public])

    def test_pair_accepts_only_local_actual_receipts_in_the_right_roles(self) -> None:
        skill = self.actual("skill", 80)
        baseline = self.actual("baseline", 100)
        pair = efficiency.create_controlled_pair(skill, baseline)
        with self.assertRaisesRegex(efficiency.EfficiencyReceiptError, "actual_usage"):
            efficiency.create_controlled_pair(pair, baseline)
        with self.assertRaisesRegex(efficiency.EfficiencyReceiptError, "wrong condition"):
            efficiency.create_controlled_pair(baseline, skill)
        with self.assertRaisesRegex(efficiency.EfficiencyReceiptError, "local actual_usage"):
            efficiency.create_controlled_pair(self.public(skill), baseline)

    def test_negative_pair_delta_is_retained(self) -> None:
        pair = efficiency.create_controlled_pair(
            self.actual("skill", 120, input_tokens=100, output_tokens=20),
            self.actual("baseline", 100, input_tokens=80, output_tokens=20),
        )
        measurement = pair["measurement"]
        self.assertEqual(measurement["token_delta"]["provider_total_tokens"], -20)
        self.assertEqual(measurement["percent_provider_total_delta"], -20.0)

        summary = efficiency.aggregate_receipts([self.public(pair)])
        result = summary["strata"][0]["controlled_pairs"]
        self.assertEqual(result["quality_qualified_token_delta"], -20)
        self.assertEqual(result["negative_delta_pairs"], 1)
        self.assertEqual(result["positive_delta_pairs"], 0)

    def test_baseline_zero_has_no_percentage_but_keeps_delta(self) -> None:
        pair = efficiency.create_controlled_pair(
            self.actual("skill", 1),
            self.actual("baseline", 0, input_tokens=0, output_tokens=0),
        )
        self.assertEqual(pair["measurement"]["token_delta"]["provider_total_tokens"], -1)
        self.assertIsNone(pair["measurement"]["percent_provider_total_delta"])

    def test_public_export_strips_comparison_inputs_and_uses_content_hash_name(self) -> None:
        pair = efficiency.create_controlled_pair(
            self.actual("skill", 80), self.actual("baseline", 100)
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = efficiency.export_public_receipt(pair, Path(tmp))
            public = efficiency.load_receipt(path, require_public=True)
            digest = public["receipt_id"].removeprefix("sha256:")
            self.assertEqual(path.name, f"efficiency-{digest[:12]}.json")
            serialized = json.dumps(public, sort_keys=True)
            for private_name in (
                "settings_sha256",
                "tools_sha256",
                "fixture_sha256",
                "oracle_sha256",
                "source_receipts",
            ):
                self.assertNotIn(private_name, serialized)
            self.assertEqual(set(public["controls"]), {
                "comparison_sha256", "fresh_context", "same_acceptance_contract"
            })

    def test_public_comparison_digest_is_stable_for_one_experiment(self) -> None:
        skill = self.actual("skill", 80)
        baseline = self.actual("baseline", 100)
        self.assertNotEqual(skill["receipt_id"], baseline["receipt_id"])
        self.assertEqual(
            efficiency.public_comparison_digest(skill),
            efficiency.public_comparison_digest(baseline),
        )

    def test_aggregation_rejects_distinct_results_for_one_experimental_identity(self) -> None:
        first = self.public(efficiency.create_controlled_pair(
            self.actual("skill", 80), self.actual("baseline", 100)
        ))
        second = self.public(efficiency.create_controlled_pair(
            self.actual("skill", 81), self.actual("baseline", 100)
        ))
        self.assertNotEqual(first["receipt_id"], second["receipt_id"])
        self.assertEqual(
            first["controls"]["comparison_sha256"],
            second["controls"]["comparison_sha256"],
        )
        with self.assertRaisesRegex(efficiency.EfficiencyReceiptError, "experimental identity"):
            efficiency.aggregate_receipts([first, second])

    def test_public_export_refuses_reexport_and_local_ledger_entries(self) -> None:
        local = self.actual("skill", 10)
        public = self.public(local)
        with self.assertRaisesRegex(efficiency.EfficiencyReceiptError, "only a local"):
            efficiency.public_projection(public)
        with self.assertRaisesRegex(efficiency.EfficiencyReceiptError, "public ledger"):
            efficiency.aggregate_receipts([local])

    def test_aggregation_deduplicates_and_is_order_deterministic(self) -> None:
        pair_a = self.public(efficiency.create_controlled_pair(
            self.actual("skill", 80), self.actual("baseline", 100)
        ))
        pair_b = self.public(efficiency.create_controlled_pair(
            self.actual("skill", 90, provider="anthropic", model="claude-a"),
            self.actual("baseline", 100, provider="anthropic", model="claude-a"),
        ))
        first = efficiency.aggregate_receipts([pair_b, pair_a, copy.deepcopy(pair_a)])
        second = efficiency.aggregate_receipts([pair_a, pair_a, pair_b])
        self.assertEqual(first, second)
        self.assertEqual(first["receipt_counts"]["controlled_pairs"], 2)
        self.assertEqual(first["receipt_counts"]["duplicates_ignored"], 1)
        self.assertEqual([(item["provider"], item["model"], item["task_class"]) for item in first["strata"]], [
            ("anthropic", "claude-a", "audit"), ("openai", "model-a", "audit")
        ])
        self.assertNotIn("quality_qualified_token_delta", first)

    def test_actual_usage_is_labeled_usage_not_savings(self) -> None:
        actual = self.public(self.actual("skill", 100))
        summary = efficiency.aggregate_receipts([actual])
        self.assertEqual(summary["receipt_counts"]["actual_usage"], 1)
        actual_usage = summary["strata"][0]["actual_usage"]
        self.assertEqual(actual_usage["receipts"], 1)
        self.assertEqual(
            actual_usage["by_condition"]["skill"],
            {"receipts": 1, "provider_total_tokens": 100},
        )
        self.assertEqual(
            actual_usage["by_condition"]["baseline"],
            {"receipts": 0, "provider_total_tokens": 0},
        )
        self.assertNotIn("provider_total_tokens", actual_usage)
        self.assertNotIn("saving", json.dumps(summary["strata"][0]["actual_usage"]).lower())

    def test_actual_usage_aggregation_keeps_conditions_separate(self) -> None:
        skill = self.public(self.actual("skill", 40, trial=1))
        baseline = self.public(self.actual("baseline", 70, trial=2))
        actual_usage = efficiency.aggregate_receipts([baseline, skill])["strata"][0]["actual_usage"]
        self.assertEqual(actual_usage["receipts"], 2)
        self.assertEqual(
            actual_usage["by_condition"],
            {
                "skill": {"receipts": 1, "provider_total_tokens": 40},
                "baseline": {"receipts": 1, "provider_total_tokens": 70},
            },
        )

    def test_load_rejects_malformed_and_oversized_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            malformed = Path(tmp) / "bad.json"
            malformed.write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(efficiency.EfficiencyReceiptError, "invalid receipt JSON"):
                efficiency.load_receipt(malformed)
            oversized = Path(tmp) / "large.json"
            oversized.write_bytes(b" " * (efficiency.MAX_RECEIPT_BYTES + 1))
            with self.assertRaisesRegex(efficiency.EfficiencyReceiptError, "exceeds"):
                efficiency.load_receipt(oversized)

    def test_load_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.json"
            path.write_text('{"schema_version":1,"schema_version":1}\n', encoding="utf-8")
            with self.assertRaisesRegex(efficiency.EfficiencyReceiptError, "duplicate JSON key"):
                efficiency.load_receipt(path)

    def test_ledger_requires_content_identity_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger"
            ledger.mkdir()
            receipt = self.public(self.actual("skill", 10))
            efficiency.write_json_atomic(ledger / "wrong-name.json", receipt)
            with self.assertRaisesRegex(efficiency.EfficiencyReceiptError, "filename does not match"):
                efficiency.aggregate_ledger(ledger)

    def test_writer_refuses_link_like_parent_components(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            victim = root / "victim"
            victim.mkdir()
            alias = root / "alias"
            try:
                alias.symlink_to(victim, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"symlink creation unavailable: {error}")
            with self.assertRaisesRegex(efficiency.EfficiencyReceiptError, "link-like path component"):
                efficiency.write_json_atomic(alias / "receipt.json", {"value": 1})
            self.assertEqual(list(victim.iterdir()), [])

    def test_receipt_pr_requires_one_receipt_and_fresh_mirrored_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            ledger = repo / "metrics" / "ledger"
            ledger.mkdir(parents=True)
            summary_path = repo / "metrics" / "summary.json"
            docs_summary = repo / "docs" / "data" / "efficiency-summary.json"
            empty = efficiency.empty_summary()
            efficiency.write_json_atomic(summary_path, empty)
            efficiency.write_json_atomic(docs_summary, empty)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "tests@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "ADC Tests"], check=True)
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
            base = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            efficiency.export_public_receipt(self.actual("skill", 10), ledger)
            current = efficiency.aggregate_ledger(ledger)
            efficiency.write_json_atomic(summary_path, current)
            efficiency.write_json_atomic(docs_summary, current)
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "receipt"], check=True)

            errors, additions = efficiency.validate_ledger_change(
                repo=repo,
                ledger=ledger,
                changed_from=base,
                summary_path=summary_path,
                docs_summary_path=docs_summary,
            )
            self.assertEqual(errors, [])
            self.assertEqual(additions, 1)

            docs_summary.write_text("{}\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "stale"], check=True)
            errors, _ = efficiency.validate_ledger_change(
                repo=repo,
                ledger=ledger,
                changed_from=base,
                summary_path=summary_path,
                docs_summary_path=docs_summary,
            )
            self.assertTrue(any("website summary is stale" in item for item in errors), errors)

            current = efficiency.aggregate_ledger(ledger)
            efficiency.write_json_atomic(summary_path, current)
            efficiency.write_json_atomic(docs_summary, current)
            docs_summary.write_bytes(docs_summary.read_bytes().replace(b"\n", b"\r\n"))
            self.git(repo, "add", ".")
            self.git(repo, "commit", "-qm", "noncanonical summary newlines")
            errors, _ = efficiency.validate_ledger_change(
                repo=repo,
                ledger=ledger,
                changed_from=base,
                summary_path=summary_path,
                docs_summary_path=docs_summary,
            )
            self.assertTrue(any("website summary is stale" in item for item in errors), errors)

    def test_validate_ledger_pr_exact_cli_accepts_a_valid_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            ledger, summary_path, docs_summary, base = self.initialize_receipt_repo(repo)
            self.commit_valid_receipt_change(repo, ledger, summary_path, docs_summary)
            errors, additions = efficiency.validate_ledger_pr(repo=repo, changed_from=base)
            self.assertEqual((errors, additions), ([], 1))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = efficiency.main([
                    "validate-ledger-pr", "--repo", str(repo), "--changed-from", base,
                ])
            self.assertEqual(result, 0)
            self.assertIn("VALID ledger change", output.getvalue())

    def test_validate_ledger_pr_rejects_unrelated_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            ledger, summary_path, docs_summary, base = self.initialize_receipt_repo(repo)
            self.commit_valid_receipt_change(repo, ledger, summary_path, docs_summary)
            (repo / "unrelated.txt").write_text("not part of receipt intake\n", encoding="utf-8")
            self.git(repo, "add", ".")
            self.git(repo, "commit", "-qm", "unrelated")
            errors, additions = efficiency.validate_ledger_pr(repo=repo, changed_from=base)
            self.assertEqual(additions, 1)
            self.assertEqual(
                errors,
                ["a receipt PR must add one ledger receipt and update only the two generated summaries"],
            )

    def test_validate_ledger_pr_rejects_tampering_missing_and_stale_summaries(self) -> None:
        cases = ("tampered-receipt", "missing-summary", "stale-summary", "wrong-filename")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                ledger, summary_path, docs_summary, base = self.initialize_receipt_repo(repo)
                receipt_path = self.commit_valid_receipt_change(
                    repo, ledger, summary_path, docs_summary
                )
                if case == "tampered-receipt":
                    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                    receipt["measurement"]["usage"]["provider_total_tokens"] += 1
                    efficiency.write_json_atomic(receipt_path, receipt)
                elif case == "missing-summary":
                    docs_summary.unlink()
                elif case == "stale-summary":
                    docs_summary.write_text("{}\n", encoding="utf-8")
                else:
                    receipt_path.rename(ledger / "efficiency-000000000000.json")
                self.git(repo, "add", "-A")
                self.git(repo, "commit", "-qm", case)
                errors, additions = efficiency.validate_ledger_pr(repo=repo, changed_from=base)
                self.assertEqual(additions, 1)
                self.assertTrue(errors, case)
                if case == "tampered-receipt":
                    self.assertTrue(any("content hash" in error for error in errors), errors)
                elif case == "missing-summary":
                    self.assertTrue(any("website summary is missing" in error for error in errors), errors)
                elif case == "stale-summary":
                    self.assertTrue(any("website summary is stale" in error for error in errors), errors)
                else:
                    self.assertTrue(any("filename does not match" in error for error in errors), errors)

    def test_validate_ledger_pr_uses_merge_base_for_a_branch_behind_main(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            ledger, summary_path, docs_summary, _ = self.initialize_receipt_repo(repo)
            self.git(repo, "branch", "candidate")
            (repo / "upstream-only.txt").write_text("new on main\n", encoding="utf-8")
            self.git(repo, "add", ".")
            self.git(repo, "commit", "-qm", "main advanced")
            updated_main = self.git(repo, "rev-parse", "HEAD")
            self.git(repo, "checkout", "-q", "candidate")
            self.commit_valid_receipt_change(repo, ledger, summary_path, docs_summary)

            errors, additions = efficiency.validate_ledger_pr(
                repo=repo,
                changed_from=updated_main,
            )
            self.assertEqual((errors, additions), ([], 1))

    def test_empty_aggregate_is_stable_and_makes_no_savings_claim(self) -> None:
        first = efficiency.aggregate_receipts([])
        second = efficiency.aggregate_receipts([])
        self.assertEqual(first, second)
        self.assertEqual(first["strata"], [])
        self.assertIn("Actual usage is not savings", first["claim_boundary"])

    def test_cli_records_validates_exports_and_aggregates_only_to_requested_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            local = root / "local.json"
            public_dir = root / "public"
            summary = root / "summary.json"
            mirror = root / "docs-summary.json"
            record_args = [
                "record",
                "--out", str(local),
                "--opt-in",
                "--condition", "skill",
                "--skill-version", "v1",
                "--core-sha256", DIGESTS["core"],
                "--provider", "openai",
                "--model", "model-a",
                "--usage-semantics", "provider-reported-v1",
                "--task-class", "audit",
                "--trial", "1",
                "--order", "skill-first",
                "--settings-sha256", DIGESTS["settings"],
                "--tools-sha256", DIGESTS["tools"],
                "--fixture-sha256", DIGESTS["fixture"],
                "--oracle-sha256", DIGESTS["oracle"],
                "--provider-total-tokens", "10",
                "--month", "2026-08",
            ]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(efficiency.main(record_args), 0)
                self.assertEqual(efficiency.main(["validate", str(local)]), 0)
                self.assertEqual(efficiency.main([
                    "export", "--receipt", str(local), "--out-dir", str(public_dir)
                ]), 0)
                self.assertEqual(efficiency.main([
                    "aggregate", "--ledger", str(public_dir), "--out", str(summary),
                    "--mirror-out", str(mirror),
                ]), 0)
            self.assertTrue(local.is_file())
            self.assertEqual(len(list(public_dir.glob("efficiency-*.json"))), 1)
            self.assertEqual(json.loads(summary.read_text(encoding="utf-8"))["receipt_counts"]["actual_usage"], 1)
            self.assertEqual(summary.read_bytes(), mirror.read_bytes())

    def test_aggregation_separates_task_classes(self) -> None:
        audit = self.public(self.actual("skill", 10, task_class="audit"))
        verify = self.public(self.actual("skill", 20, task_class="verify"))
        summary = efficiency.aggregate_receipts([verify, audit])
        self.assertEqual(
            [
                (
                    item["task_class"],
                    item["actual_usage"]["by_condition"]["skill"]["provider_total_tokens"],
                )
                for item in summary["strata"]
            ],
            [("audit", 10), ("verify", 20)],
        )

    def test_aggregation_separates_adapter_and_usage_semantics(self) -> None:
        first = self.public(self.actual(
            "skill", 10, adapter_version="manual-v1", usage_semantics="provider-reported-v1"
        ))
        second = self.public(self.actual(
            "skill", 20, adapter_version="manual-v2", usage_semantics="provider-reported-v2"
        ))
        summary = efficiency.aggregate_receipts([second, first])
        self.assertEqual(
            [
                (
                    item["adapter_version"],
                    item["usage_semantics"],
                    item["actual_usage"]["by_condition"]["skill"]["provider_total_tokens"],
                )
                for item in summary["strata"]
            ],
            [
                ("manual-v1", "provider-reported-v1", 10),
                ("manual-v2", "provider-reported-v2", 20),
            ],
        )


if __name__ == "__main__":
    unittest.main()
