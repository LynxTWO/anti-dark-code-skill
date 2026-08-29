from __future__ import annotations

import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parent
CAPABILITIES = SKILL_ROOT / "assets" / "verification-capabilities.json"


def load_module(name: str, path: Path):
    """Load a helper module by path.

    The module is registered in sys.modules before execution. Without that,
    dataclasses cannot resolve a field annotation: dataclasses._is_type reads
    sys.modules.get(cls.__module__).__dict__ and finds None. Any module here
    defining a dataclass fails at import without this line.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.modules[spec.name] = module
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def load_adc():
    return load_module("adc", SKILL_ROOT / "scripts" / "adc.py")


class CapabilityCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
        self.caps = self.catalog["capabilities"]

    def test_catalog_carries_the_two_router_capabilities(self) -> None:
        by_id = {c["id"]: c for c in self.caps}
        self.assertIn("V21", by_id)
        self.assertIn("V22", by_id)
        self.assertEqual(by_id["V21"]["name"], "Affected-unit testing")
        self.assertEqual(by_id["V22"]["name"], "Input fuzz testing")

    def test_catalog_ids_are_contiguous_through_v22(self) -> None:
        ids = sorted(c["id"] for c in self.caps)
        self.assertEqual(ids, [f"V{i:02d}" for i in range(1, 23)])

    def test_every_capability_shares_one_field_shape(self) -> None:
        shapes = {tuple(sorted(c.keys())) for c in self.caps}
        self.assertEqual(len(shapes), 1, f"capability entries disagree on fields: {shapes}")

    def test_new_capabilities_carry_every_required_field(self) -> None:
        required = {"id", "slug", "name", "category", "default_level", "cost",
                    "purpose", "local_work", "agent_work", "adaptations", "selection"}
        by_id = {c["id"]: c for c in self.caps}
        for cap_id in ("V21", "V22"):
            self.assertEqual(required - set(by_id[cap_id]), set(),
                             f"{cap_id} is missing required fields")

    def test_adaptations_cover_the_same_repo_types_as_the_rest(self) -> None:
        by_id = {c["id"]: c for c in self.caps}
        reference = set(by_id["V01"]["adaptations"])
        for cap_id in ("V21", "V22"):
            self.assertEqual(set(by_id[cap_id]["adaptations"]), reference,
                             f"{cap_id} adaptations do not match the catalog")


class CapabilityCountContractTests(unittest.TestCase):
    """The count is asserted in several places. Adding an entry must update all of them."""

    def test_validator_accepts_the_live_catalog(self) -> None:
        adc = load_adc()
        errors, _warnings = adc.validate_skill(SKILL_ROOT, mode="universal")
        capability_errors = [e for e in errors if "apabilit" in e]
        self.assertEqual(capability_errors, [])

    def test_catalog_description_does_not_claim_a_stale_count(self) -> None:
        catalog = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
        count = len(catalog["capabilities"])
        description = catalog["description"]
        stale = re.findall(r"\b(\d+)\b", description)
        for number in stale:
            self.assertEqual(int(number), count,
                             f"description says {number}, catalog holds {count}")

    def test_no_shipped_code_hard_codes_a_stale_capability_count(self) -> None:
        catalog = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
        count = len(catalog["capabilities"])
        offenders: list[str] = []
        # This file states the pattern, so it always matches itself. Excluding
        # it is a false-positive fix, not a hole: nothing else here asserts a
        # capability count.
        scanned = sorted((SKILL_ROOT / "scripts").glob("*.py"))
        scanned += [p for p in sorted((SKILL_ROOT / "tests").glob("*.py"))
                    if p.name != Path(__file__).name]
        for path in scanned:
            for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if re.search(
                    r"(?i)\b20\b[^\n]{0,40}capabilit|!= 20\b|range\(1, 21\)|V01\.\.V20", line
                ):
                    offenders.append(f"{path.name}:{number}: {line.strip()}")
        self.assertEqual(offenders, [],
                         f"stale capability count, catalog holds {count}")


if __name__ == "__main__":
    unittest.main()
