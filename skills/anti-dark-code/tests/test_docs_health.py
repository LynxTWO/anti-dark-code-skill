"""Synthetic documentation-health fixtures; no private repository inputs."""

from __future__ import annotations

import contextlib
import datetime as dt
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SKILL = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adc = load_module("adc_docs_health_test_adc", SKILL / "scripts/adc.py")
health = load_module("adc_docs_health_test_helper", SKILL / "scripts/adc_docs_health.py")


class DocsHealthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name).resolve()

    def write(self, path, content):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def cli(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = adc.main(["docs-health", "--repo", str(self.repo), *args])
        return code, output.getvalue()

    def test_both_field_shapes_risks_and_statuses(self):
        self.write("docs/unknowns/example.md", """# Unknowns
## Entries
### First
- **Concern:** Evidence is incomplete.
- **Risk level:** high
- **Status:** open
### Second
**Concern:** A different boundary needs a check.
**Risk:** critical
**Status:** in progress
### Third
Risk level: low
Status: resolved
### Fourth
**Risk:** medium
**Status:** deferred
### Fifth
**Risk:** high
**Status:** blocked
### Sixth
**Risk:** low
**Status:** ready
### Seventh
**Risk:** high
**Status:** fixed
### Eighth
**Risk:** critical
**Status:** done
""")
        unknowns = health.report(self.repo, adc)["unknowns"]
        self.assertEqual(unknowns["total_entries"], 8)
        self.assertEqual(unknowns["open_entries"], 5)
        self.assertEqual(unknowns["open_high_critical"], 3)
        self.assertEqual(unknowns["open_without_status"], 0)
        self.assertEqual(unknowns["by_risk"], {"critical": 2, "high": 3, "low": 2, "medium": 1})
        self.assertEqual(unknowns["by_status"], {
            "blocked": 1, "deferred": 1, "done": 1, "fixed": 1,
            "in progress": 1, "open": 1, "ready": 1, "resolved": 1})

    def test_missing_status_and_closed_section_with_sibling_open_entries(self):
        self.write("docs/unknowns/example.md", """# Unknowns
## Entries
### No status
- **Concern:** Still unclear.
- **Risk level:** high
## Closed items
### Already closed
**Risk:** critical
**Status:** open
### Also closed
**Concern:** The resolution is recorded elsewhere.
## More entries
### Another open item
**Concern:** A later check is pending.
""")
        report = health.report(self.repo, adc)
        self.assertEqual(report["unknowns"]["total_entries"], 4)
        self.assertEqual(report["unknowns"]["by_status"], {"closed": 2, "missing": 2})
        self.assertEqual(report["unknowns"]["open_entries"], 2)
        self.assertEqual(report["unknowns"]["open_without_status"], 2)
        self.assertEqual(report["unknowns"]["open_high_critical"], 1)
        self.assertEqual(report["findings"][0]["code"], "missing-status")

    def test_bold_fields_in_one_paragraph(self):
        self.write("docs/unknowns/example.md", "### Question\n**Risk:** high. **Status:** open.\n")
        unknowns = health.report(self.repo, adc)["unknowns"]
        self.assertEqual(unknowns["by_status"], {"open": 1})
        self.assertEqual(unknowns["by_risk"], {"high": 1})
        self.assertEqual(unknowns["open_without_status"], 0)

    def test_decorated_risk_values_use_the_existing_severity_buckets(self):
        self.write("docs/unknowns/example.md", """### First question
**Risk:** high before release.
**Status:** open
### Second question
**Risk level:** CRITICAL (release boundary)
**Status:** open
### Third question
**Risk:** medium - follow-up check pending
**Status:** open
### Fourth question
**Risk:** low: later review
**Status:** open
""")
        unknowns = health.report(self.repo, adc)["unknowns"]
        self.assertEqual(unknowns["by_risk"], {"critical": 1, "high": 1, "low": 1, "medium": 1})
        self.assertEqual(unknowns["open_entries"], 4)
        self.assertEqual(unknowns["open_high_critical"], 2)

    def test_closed_status_date_annotations_do_not_create_open_entries(self):
        self.write("docs/unknowns/example.md", """### First question
**Risk:** critical
**Status:** resolved (2026-10-01)
### Second question
**Risk:** high
**Status:** fixed - 2026-10-02
### Third question
**Risk:** critical
**Status:** DONE, 2026-10-03
### Fourth question
**Risk:** high
**Status:** closed on 2026-10-04
""")
        code, output = self.cli("--json", "--max-open", "0")
        unknowns = json.loads(output)["unknowns"]
        self.assertEqual(code, 0)
        self.assertEqual(unknowns["by_status"], {"closed": 1, "done": 1, "fixed": 1, "resolved": 1})
        self.assertEqual(unknowns["open_entries"], 0)
        self.assertEqual(unknowns["open_high_critical"], 0)

    def test_active_status_qualifiers_keep_entries_open(self):
        self.write("docs/unknowns/example.md", """### First question
**Risk:** high before release
**Status:** in progress (owner review)
### Second question
**Risk:** high
**Status:** blocked on a synthetic prerequisite
### Third question
**Risk:** critical
**Status:** deferred until the next review
### Fourth question
**Risk:** high
**Status:** ready for review
### Fifth question
**Risk:** high
**Status:** open since 2026-10-01
""")
        unknowns = health.report(self.repo, adc)["unknowns"]
        self.assertEqual(unknowns["by_status"], {"blocked": 1, "deferred": 1, "in progress": 1, "open": 1, "ready": 1})
        self.assertEqual(unknowns["open_entries"], 5)
        self.assertEqual(unknowns["open_high_critical"], 5)
        self.assertEqual(unknowns["open_without_status"], 0)

    def test_noncanonical_values_stay_visible_and_negated_statuses_stay_open(self):
        self.write("docs/unknowns/example.md", """### First question
**Risk:** urgent
**Status:** not resolved
### Second question
**Risk:** very high
**Status:** awaiting review
### Third question
**Risk:** highish
**Status:** resolvedness unknown
### Fourth question
**Risk:** unknown
**Status:** not fixed
""")
        unknowns = health.report(self.repo, adc)["unknowns"]
        self.assertEqual(unknowns["by_status"], {"awaiting review": 1, "not fixed": 1, "not resolved": 1, "resolvedness unknown": 1})
        self.assertEqual(unknowns["by_risk"], {"highish": 1, "unknown": 1, "urgent": 1, "very high": 1})
        self.assertEqual(unknowns["open_entries"], 4)
        self.assertEqual(unknowns["open_high_critical"], 0)
        self.assertEqual(unknowns["open_without_status"], 0)

    def test_status_words_in_other_fields_do_not_supply_a_status(self):
        self.write("docs/unknowns/example.md", """### Question
**Concern:** resolved (2026-10-01) refers to a different question.
**Risk:** high
**Next best check:** fixed status still needs evidence.
""")
        unknowns = health.report(self.repo, adc)["unknowns"]
        self.assertEqual(unknowns["by_status"], {"missing": 1})
        self.assertEqual(unknowns["open_entries"], 1)
        self.assertEqual(unknowns["open_without_status"], 1)

    def test_blocks_buckets_include_qualified_missing_and_unknown_values(self):
        self.write("docs/unknowns/example.md", """### First question
- **Risk:** high
- **Status:** open
- **Blocks:** next release (acceptance check)
- **Revisit:** 2026-10-25
### Second question
**Status:** open
**Blocks:** LATER - follow-up work
### Third question
**Status:** resolved
**Blocks:** nothing; informational
### Fourth question
**Status:** open
### Fifth question
**Status:** open
**Blocks:** unknown
### Sixth question
**Status:** open
**Blocks:** owner review
""")
        report = health.report(self.repo, adc, today=dt.date(2026, 10, 26))
        self.assertEqual(report["unknowns"]["by_blocks"], {
            "later": 1, "missing": 1, "next release": 1,
            "nothing": 1, "owner review": 1, "unknown": 1})
        self.assertEqual(report["unknowns"]["open_past_revisit"], 1)
        self.assertEqual(report["unknowns"]["total_entries"], 6)

    def test_revisit_dates_are_strictly_past_the_report_evaluation_date(self):
        self.write("docs/unknowns/example.md", """### Past
**Status:** open
**Revisit:** 2026-10-25 (owner review)
### Today
**Status:** blocked on a synthetic prerequisite
**Revisit:** 2026-10-26
### Future
**Status:** in progress
**Revisit:** 2026-10-27 - follow-up check
""")
        report = health.report(self.repo, adc, today=dt.date(2026, 10, 26))
        self.assertEqual(report["evaluated_on"], "2026-10-26")
        self.assertEqual(report["unknowns"]["open_past_revisit"], 1)
        self.assertEqual(report["unknowns"]["open_entries"], 3)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            health.print_report(report)
        self.assertIn("EVALUATED_ON 2026-10-26", output.getvalue())
        self.assertIn("open_past_revisit=1", output.getvalue())
        self.assertIn("by_blocks: missing=3", output.getvalue())

    def test_invalid_revisit_dates_and_event_text_are_not_overdue_dates(self):
        values = ["2026-02-30", "2025-13-01", "0000-01-01", "2026-10-250", "after deployment", "after the 2020-01-01 migration", "on 2020-01-01", "unknown", ""]
        self.write("docs/unknowns/example.md", "\n".join(
            f"### Question {index}\n**Status:** open\n**Revisit:** {value}\n"
            for index, value in enumerate(values)))
        report = health.report(self.repo, adc, today=dt.date(2026, 10, 26))
        self.assertEqual(report["unknowns"]["open_past_revisit"], 0)
        self.assertEqual(report["unknowns"]["open_entries"], len(values))
        self.assertIsNone(health.revisit_date("2023-02-29"))
        self.assertEqual(health.revisit_date("2024-02-29"), dt.date(2024, 2, 29))

    def test_decorated_revisit_dates_with_qualifiers_are_counted(self):
        values = [
            "`2020-02-29` (owner review)", "``2020-02-29`` - follow-up check",
            "*2020-02-29* (owner review)", "**2020-02-29**: owner review",
            "_2020-02-29_ (owner review)", "__2020-02-29__; owner review",
            "***2020-02-29*** (owner review)", "___2020-02-29___ (owner review)",
            "`2020-02-29`", "**2020-02-29**",
            "`2020-02-29 (owner review)`", "**2020-02-29 (owner review)**",
        ]
        self.write("docs/unknowns/example.md", "\n".join(
            f"### Question {index}\n**Status:** open\n**Revisit:** {value}\n"
            for index, value in enumerate(values)))
        report = health.report(self.repo, adc, today=dt.date(2026, 10, 26))
        self.assertEqual(report["unknowns"]["open_past_revisit"], len(values))
        self.assertEqual(report["unknowns"]["open_entries"], len(values))
        for value in values:
            with self.subTest(value=value):
                self.assertEqual(health.revisit_date(value), dt.date(2020, 2, 29))

    def test_decorated_revisit_dates_preserve_invalid_and_event_exclusions(self):
        values = [
            "`2023-02-29` (owner review)", "**2020-02-290** (owner review)",
            "`2020-02-29T00:00:00` (owner review)", "`2020-02-29`extra",
            "*2020-02-29*extra", "after `2020-02-29` (owner review)",
            "`after 2020-02-29` (owner review)", "**2020-02-29* (owner review)",
            "`2020-02-29 (owner review)", "2020-02-29` (owner review)",
            "**2020-02-29` (owner review)",
        ]
        self.write("docs/unknowns/example.md", "\n".join(
            f"### Question {index}\n**Status:** open\n**Revisit:** {value}\n"
            for index, value in enumerate(values)))
        report = health.report(self.repo, adc, today=dt.date(2026, 10, 26))
        self.assertEqual(report["unknowns"]["open_past_revisit"], 0)
        self.assertEqual(report["unknowns"]["open_entries"], len(values))
        for value in values:
            with self.subTest(value=value):
                self.assertIsNone(health.revisit_date(value))

    def test_closed_entries_with_old_revisit_dates_are_not_overdue(self):
        self.write("docs/unknowns/example.md", """## Entries
### Resolved question
**Status:** resolved (2026-10-01)
**Blocks:** nothing
**Revisit:** 2020-01-01
## Closed items
### Archived question
**Status:** open
**Blocks:** later
**Revisit:** 2020-01-01
""")
        report = health.report(self.repo, adc, max_open=0, today=dt.date(2026, 10, 26))
        self.assertEqual(report["unknowns"]["by_blocks"], {"later": 1, "nothing": 1})
        self.assertEqual(report["unknowns"]["open_past_revisit"], 0)
        self.assertEqual(report["unknowns"]["open_entries"], 0)
        self.assertFalse(report["max_open_exceeded"])

    def test_new_fields_in_one_paragraph_preserve_existing_threshold_counts(self):
        self.write("docs/unknowns/example.md", """### Question
**Risk:** critical before release. **Status:** blocked on review. **Blocks:** next release (acceptance). **Revisit:** 2026-10-25 (review).
""")
        report = health.report(self.repo, adc, max_open=0, today=dt.date(2026, 10, 26))
        unknowns = report["unknowns"]
        self.assertEqual(unknowns["by_status"], {"blocked": 1})
        self.assertEqual(unknowns["by_risk"], {"critical": 1})
        self.assertEqual(unknowns["by_blocks"], {"next release": 1})
        self.assertEqual(unknowns["open_entries"], 1)
        self.assertEqual(unknowns["open_high_critical"], 1)
        self.assertEqual(unknowns["open_past_revisit"], 1)
        self.assertTrue(report["max_open_exceeded"])

    def test_missing_exit_fields_remain_missing_without_changing_entry_status(self):
        self.write("docs/unknowns/example.md", "### Question\n**Concern:** A synthetic check is pending.\n")
        report = health.report(self.repo, adc, today=dt.date(2026, 10, 26))
        unknowns = report["unknowns"]
        self.assertEqual(unknowns["by_blocks"], {"missing": 1})
        self.assertEqual(unknowns["by_status"], {"missing": 1})
        self.assertEqual(unknowns["open_entries"], 1)
        self.assertEqual(unknowns["open_without_status"], 1)
        self.assertEqual(unknowns["open_past_revisit"], 0)

    def test_nested_evidence_heading_stays_with_resolved_entry(self):
        self.write("docs/unknowns/example.md", """# Unknowns
## Entries
### One unknown
**Risk:** high
**Status:** resolved
#### Evidence notes
A synthetic note explaining the resolution.
##### Supporting detail
Another note for the same unknown.
""")
        code, output = self.cli("--json", "--max-open", "0")
        unknowns = json.loads(output)["unknowns"]
        self.assertEqual(code, 0)
        self.assertEqual(unknowns["total_entries"], 1)
        self.assertEqual(unknowns["by_status"], {"resolved": 1})
        self.assertEqual(unknowns["open_entries"], 0)
        self.assertEqual(unknowns["open_without_status"], 0)

    def test_nested_notes_do_not_swallow_the_next_sibling_entry(self):
        self.write("docs/unknowns/example.md", """## Entries
### Resolved question
**Status:** resolved
#### Evidence notes
The synthetic check passed.
### Open question
**Risk:** critical
**Status:** open
#### Evidence notes
A follow-up check is pending.
""")
        unknowns = health.report(self.repo, adc)["unknowns"]
        self.assertEqual(unknowns["total_entries"], 2)
        self.assertEqual(unknowns["by_status"], {"open": 1, "resolved": 1})
        self.assertEqual(unknowns["open_high_critical"], 1)

    def test_closed_summary_entries_and_fenced_examples(self):
        self.write("docs/unknowns/example.md", """# Unknowns
```markdown
### Example
**Risk:** high
**Status:** open
```
## Closed items
- **First** - resolved after a synthetic check.
- **Second** - resolved after another check.
""")
        unknowns = health.report(self.repo, adc)["unknowns"]
        self.assertEqual(unknowns["total_entries"], 2)
        self.assertEqual(unknowns["by_status"], {"closed": 2})
        self.assertEqual(unknowns["open_entries"], 0)

    def test_closed_summaries_under_deeper_container_heading(self):
        self.write("docs/unknowns/example.md", """# Unknowns
## Legacy records
### Closed items
- **First** - resolved after a synthetic check.
- **Second** - resolved after another synthetic check.
## Current entries
### Still open
**Status:** open
""")
        unknowns = health.report(self.repo, adc)["unknowns"]
        self.assertEqual(unknowns["total_entries"], 3)
        self.assertEqual(unknowns["by_status"], {"closed": 2, "open": 1})
        self.assertEqual(unknowns["open_entries"], 1)

    def test_default_maps_dates_candidates_and_fenced_headings(self):
        text = """# Current system
## Runtime units
## 2026-10-26 observations
### Candidate June 8
## October 26th notes
## CANDIDATE alternatives
## Candidates are a separate word
~~~markdown
## candidate 2026-10-27 example
~~~
"""
        self.write("docs/architecture/system-map.md", text)
        self.write("docs/architecture/service-map.md", "# Service map\n")
        self.write("docs/architecture/coverage-ledger.md", "# Coverage\n")
        self.write("service-map.md", "# Root service map\n")
        report = health.report(self.repo, adc)
        maps = {row["path"]: row for row in report["maps"]}
        self.assertEqual(len(maps), 4)
        row = maps["docs/architecture/system-map.md"]
        self.assertEqual(row["line_count"], len(text.splitlines()))
        self.assertEqual(row["heading_count"], 7)
        self.assertEqual(row["dated_heading_count"], 3)
        self.assertEqual(row["candidate_heading_count"], 2)
        self.assertEqual(row["appended_heading_count"], 4)

    def test_calibration_paths_from_json_and_markdown_are_deduplicated(self):
        calibration = ".agents/skills/anti-dark-code/calibration"
        self.write(f"{calibration}/repo-profile.json", json.dumps({
            "docs": {"unknowns_path": "notes/questions.md", "maps": ["notes/runtime.md"]},
            "coverage_ledger": "notes/coverage.md"}))
        self.write(f"{calibration}/README.md", "Unknowns: `notes/questions.md`\nMap: [runtime](../../../../notes/runtime.md)\n")
        self.write(f"{calibration}/system-map.md", "# Calibrated map\n")
        self.write(f"{calibration}/coverage-ledger.md", "# Calibrated coverage\n")
        self.write("notes/questions.md", "## Question\n**Risk:** high\n**Status:** open\n")
        self.write("notes/runtime.md", "# Runtime\n## Candidate 2026-10-26\n")
        self.write("notes/coverage.md", "# Coverage\n")
        report = health.report(self.repo, adc)
        self.assertTrue(report["scan"]["complete"])
        self.assertEqual(report["unknowns"]["files"], ["notes/questions.md"])
        self.assertEqual(report["unknowns"]["total_entries"], 1)
        self.assertEqual({row["path"] for row in report["maps"]}, {
            f"{calibration}/system-map.md", f"{calibration}/coverage-ledger.md",
            "notes/runtime.md", "notes/coverage.md"})

    def test_calibration_markdown_link_labels_identify_document_roles(self):
        self.write(".anti-dark-code/calibration/README.md", """- [Unknowns](../../notes/questions.md)
- [System map](../../notes/runtime.md)
""")
        self.write("notes/questions.md", "### Question\n**Risk:** high\n**Status:** open\n")
        self.write("notes/runtime.md", "# Runtime\n")
        report = health.report(self.repo, adc)
        self.assertEqual(report["unknowns"]["files"], ["notes/questions.md"])
        self.assertEqual(report["unknowns"]["total_entries"], 1)
        self.assertEqual([row["path"] for row in report["maps"]], ["notes/runtime.md"])
        self.assertTrue(report["scan"]["complete"])

    def test_relative_markdown_links_resolve_from_calibration_document(self):
        self.write(".anti-dark-code/calibration/README.md", "Map: [runtime](runtime.md)\n")
        self.write(".anti-dark-code/calibration/runtime.md", "# Local runtime\n## Candidate June 8\n")
        self.write("runtime.md", "# Unrelated root document\n")
        report = health.report(self.repo, adc)
        self.assertEqual([row["path"] for row in report["maps"]], [".anti-dark-code/calibration/runtime.md"])
        self.assertEqual(report["maps"][0]["candidate_heading_count"], 1)
        self.assertTrue(report["scan"]["complete"])

    def test_fallback_calibration_and_unknowns_directory(self):
        self.write(".anti-dark-code/calibration/README.md", "Unknowns: `notes/questions`\nMap: `notes/runtime.md`\n")
        self.write("notes/questions/a.md", "### First\n**Risk:** low\n**Status:** resolved\n")
        self.write("notes/questions/b.md", "### Second\n**Risk:** high\n")
        self.write("notes/runtime.md", "# Current map\n")
        report = health.report(self.repo, adc)
        self.assertEqual(report["unknowns"]["total_entries"], 2)
        self.assertEqual(report["unknowns"]["open_entries"], 1)
        self.assertEqual([row["path"] for row in report["maps"]], ["notes/runtime.md"])

    def test_calibration_sections_local_ledgers_and_repo_relative_json_paths(self):
        self.write(".anti-dark-code/calibration/README.md", "## Maps\n- `notes/runtime.md`\n## Unknowns\n- `notes/questions.md`\n")
        self.write(".anti-dark-code/calibration/docs.json", json.dumps({"maps": "./notes/runtime.md"}))
        self.write(".anti-dark-code/calibration/unknowns-ledger.md", "### Local\n**Status:** open\n")
        self.write(".anti-dark-code/calibration/service-map.md", "# Local service\n")
        self.write("notes/runtime.md", "# Runtime\n")
        self.write("notes/questions.md", "### Question\n**Status:** resolved\n")
        report = health.report(self.repo, adc)
        self.assertEqual(report["unknowns"]["total_entries"], 2)
        self.assertEqual({row["path"] for row in report["maps"]}, {
            ".anti-dark-code/calibration/service-map.md", "notes/runtime.md"})

    def test_empty_repo_json_schema_and_default_text(self):
        code, output = self.cli("--json")
        self.assertEqual(code, 0)
        report = json.loads(output)
        self.assertEqual(set(report), {"schema_version", "evaluated_on", "unknowns", "maps", "scan", "max_open", "max_open_exceeded", "findings"})
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(dt.date.fromisoformat(report["evaluated_on"]).isoformat(), report["evaluated_on"])
        self.assertEqual(set(report["unknowns"]), {
            "rule", "files", "total_entries", "by_status", "by_risk", "by_blocks", "open_entries",
            "open_without_status", "open_high_critical", "open_past_revisit"})
        self.assertEqual(report["unknowns"]["total_entries"], 0)
        self.assertEqual(report["unknowns"]["by_status"], {})
        self.assertEqual(report["unknowns"]["by_blocks"], {})
        self.assertEqual(report["unknowns"]["open_past_revisit"], 0)
        self.assertEqual(report["maps"], [])
        self.assertTrue(report["scan"]["complete"])
        code, output = self.cli()
        self.assertEqual(code, 0)
        self.assertIn("UNKNOWNS total_entries=0 open_entries=0", output)
        self.assertIn("by_status: none", output)

    def test_max_open_is_strictly_greater_and_missing_status_is_open(self):
        self.write("docs/unknowns/a.md", "### Open\n**Risk:** high\n### Closed\n**Status:** resolved\n")
        for limit, expected in ((None, 0), (0, 1), (1, 0), (2, 0)):
            with self.subTest(limit=limit):
                args = ["--json"] + ([] if limit is None else ["--max-open", str(limit)])
                code, output = self.cli(*args)
                self.assertEqual(code, expected)
                self.assertEqual(json.loads(output)["max_open_exceeded"], expected == 1)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            self.cli("--max-open", "-1")
        self.assertEqual(caught.exception.code, 2)

    def test_findings_link_existing_instruction_lines(self):
        self.write("docs/unknowns/a.md", "### Question\n**Risk:** high\n")
        self.write("docs/architecture/system-map.md", "# Candidate 2026-10-26\n")
        report = health.report(self.repo, adc, max_open=0)
        self.assertEqual({row["code"] for row in report["findings"]}, {"missing-status", "map-heading-signal", "max-open"})
        for finding in report["findings"]:
            self.assertIn("rule:", finding["message"])
            self.assertRegex(finding["message"], r"https://github.com/LynxTWO/anti-dark-code-skill/blob/59f3dc0/.+#L\d+")

    def test_unsafe_paths_links_and_remote_urls_are_not_read(self):
        with tempfile.TemporaryDirectory() as outside:
            external = Path(outside).resolve() / "outside.md"
            external.write_text("### Outside\n**Risk:** critical\n", encoding="utf-8")
            self.write(".anti-dark-code/calibration/docs.json", json.dumps({
                "unknowns": [str(external), "../outside.md", "https://example.test/questions.md"],
                "maps": ["notes/linked.md"]}))
            link = self.repo / "notes/linked.md"
            link.parent.mkdir()
            try:
                link.symlink_to(external)
                (self.repo / "docs").symlink_to(external.parent, target_is_directory=True)
            except OSError:
                self.skipTest("symlinks unavailable")
            report = health.report(self.repo, adc)
            self.assertEqual(report["unknowns"]["total_entries"], 0)
            self.assertEqual(report["maps"], [])
            self.assertFalse(report["scan"]["complete"])
            self.assertNotIn(str(external.parent), json.dumps(report))

    def test_read_budgets_report_incomplete_and_do_not_parse_partial_files(self):
        self.write("docs/unknowns/a.md", "### Question\n**Risk:** high\n" + "x" * 100)
        with mock.patch.object(health, "MAX_FILE_BYTES", 64):
            report = health.report(self.repo, adc)
        self.assertEqual(report["unknowns"]["total_entries"], 0)
        self.assertFalse(report["scan"]["complete"])
        self.assertEqual(report["findings"][0]["code"], "read-limit")
        for index in range(3):
            self.write(f"docs/unknowns/b{index}.md", "### Question\n**Risk:** low\n")
        with mock.patch.object(health, "MAX_FILES", 1):
            report = health.report(self.repo, adc)
        self.assertFalse(report["scan"]["complete"])
        self.assertTrue(any(row["code"] == "scan-limit" for row in report["findings"]))

    def test_malformed_paths_and_deep_calibration_remain_data(self):
        self.write(".anti-dark-code/calibration/docs.json", json.dumps({
            "unknowns": ["notes/invalid\u0000.md", "//[invalid", "notes/questions.md"]}))
        self.write("notes/questions.md", "### Question\n**Status:** open\n")
        self.write(".anti-dark-code/calibration/deep.json", '{"maps":' + '[' * 1100 + '"notes/runtime.md"' + ']' * 1100 + '}')
        report = health.report(self.repo, adc)
        self.assertEqual(report["unknowns"]["total_entries"], 1)
        self.assertFalse(report["scan"]["complete"])
        self.assertEqual(sum(row["code"] == "unsafe-path" for row in report["findings"]), 2)

    def test_unknowns_walk_preserves_ignored_and_nested_repository_boundaries(self):
        entry = "### Question\n**Status:** open\n"
        self.write("docs/unknowns/current.md", entry)
        self.write("docs/unknowns/vendor/copied.md", entry)
        self.write("docs/unknowns/nested/.git", "synthetic nested checkout marker\n")
        self.write("docs/unknowns/nested/other.md", entry)
        report = health.report(self.repo, adc)
        self.assertEqual(report["unknowns"]["total_entries"], 1)
        self.assertIn("vendor", report["scan"]["ignored_directories"])
        self.assertEqual(report["scan"]["skipped_nested_repositories"], ["docs/unknowns/nested"])

    def test_command_never_writes_or_executes_or_connects(self):
        self.write("docs/unknowns/a.md", "### Question\n**Risk:** high\n")
        self.write("adc_docs_health.py", "raise RuntimeError('repository code executed')\n")
        before = {path.relative_to(self.repo): path.read_bytes() for path in self.repo.rglob("*") if path.is_file()}
        with mock.patch("subprocess.Popen", side_effect=AssertionError("execution")), \
                mock.patch("os.system", side_effect=AssertionError("execution")), \
                mock.patch("socket.socket", side_effect=AssertionError("network")), \
                mock.patch.object(Path, "write_text", side_effect=AssertionError("write")), \
                mock.patch.object(Path, "write_bytes", side_effect=AssertionError("write")), \
                mock.patch.object(Path, "mkdir", side_effect=AssertionError("write")):
            code, output = self.cli("--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)["unknowns"]["total_entries"], 1)
        self.assertEqual(before, {path.relative_to(self.repo): path.read_bytes() for path in self.repo.rglob("*") if path.is_file()})

    def test_real_cli_creates_no_repo_or_helper_bytecode_files(self):
        tool = self.repo / "trusted-tool"
        shutil.copytree(SKILL, tool, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        target = self.repo / "target"
        target.mkdir()
        self.write("target/docs/unknowns/a.md", "### Question\n**Status:** open\n")
        before = {path.relative_to(self.repo) for path in self.repo.rglob("*")}
        proc = subprocess.run([sys.executable, str(tool / "scripts/adc.py"), "docs-health", "--repo", str(target), "--json"],
                              cwd=target, capture_output=True, text=True, timeout=30,
                              env={key: value for key, value in os.environ.items() if key != "PYTHONDONTWRITEBYTECODE"})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["unknowns"]["open_entries"], 1)
        self.assertEqual(before, {path.relative_to(self.repo) for path in self.repo.rglob("*")})


if __name__ == "__main__":
    unittest.main()
