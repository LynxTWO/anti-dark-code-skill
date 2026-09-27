"""Distribution structure checks, not claims about agent compliance."""
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class DocumentationContractTests(unittest.TestCase):
    def test_instruction_files_fit_per_file_budget(self):
        for path in [ROOT / "SKILL.md", *sorted((ROOT / "references").rglob("*.md"))]:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertLess(len(path.read_text(encoding="utf-8").split()), 1200)

    def test_local_markdown_links_resolve(self):
        paths = [ROOT / "SKILL.md", *sorted((ROOT / "references").rglob("*.md")),
                 ROOT.parent / "README.md", ROOT.parent / "OPERATIONS.md"]
        for path in paths:
            text = path.read_text(encoding="utf-8")
            # Check literal inline links, excluding example code fences.
            text = re.sub(r"```.*?```", "", text, flags=re.S)
            for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", text):
                target = target.strip().strip("<>")
                parsed = urlsplit(target)
                if parsed.scheme or target.startswith("#"):
                    continue
                resolved = path.parent / unquote(parsed.path)
                with self.subTest(path=path.relative_to(ROOT.parent).as_posix(), target=target):
                    self.assertTrue(resolved.exists(), f"Missing local link: {target}")

    def test_task_cards_and_product_frameworks_are_discoverable_from_core(self):
        core = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for name in ("understand", "investigate", "document", "verify", "remediate", "improve"):
            with self.subTest(task=name):
                target = f"references/tasks/{name}.md"
                self.assertIn(f"]({target})", core)
                self.assertTrue((ROOT / target).is_file())
        for target in ("references/quality-tests.md", "references/product-principles.md"):
            self.assertIn(f"]({target})", core)
            self.assertTrue((ROOT / target).is_file())


    def test_every_reference_has_an_inbound_link(self):
        """A reference nothing links to cannot be discovered from the core."""
        # 00-preflight is a declared compatibility entry reached by old pass-00 links.
        allowed_orphans = {"references/00-preflight.md"}
        sources = [ROOT / "SKILL.md", *sorted((ROOT / "references").rglob("*.md"))]
        inbound: dict[str, int] = {}
        for path in sources:
            text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
            for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", text):
                parsed = urlsplit(target.strip().strip("<>"))
                if parsed.scheme or not parsed.path:
                    continue
                resolved = (path.parent / unquote(parsed.path)).resolve()
                if resolved != path.resolve():
                    inbound[resolved.as_posix()] = inbound.get(resolved.as_posix(), 0) + 1
        for path in sorted((ROOT / "references").rglob("*.md")):
            relative = path.relative_to(ROOT).as_posix()
            with self.subTest(reference=relative):
                if relative in allowed_orphans:
                    continue
                self.assertGreater(inbound.get(path.resolve().as_posix(), 0), 0,
                                   f"No Markdown in the core links to {relative}")

    def test_assurance_recipes_share_identical_boilerplate(self):
        """Recipes load alone, so each carries the same authority sentence; drift must fail here, not in review."""
        sentence = "This recipe inherits the active task and grants no additional authority."
        expected = sorted([
            "assurance-hardware-recovery.md", "assurance-native-execution.md", "assurance-preservation.md",
            "assurance-publication-integrity.md", "assurance-release-closure.md",
            "specialist-audited-producers.md", "specialist-gate-environment.md", "specialist-mutation-restoration.md",
            "specialist-native-reachability.md", "specialist-process-verdicts.md", "specialist-remediation-edges.md",
            "specialist-restricted-builds.md", "specialist-verifier-falsifiability.md",
        ])
        carrying = sorted(p.name for p in (ROOT / "references").glob("*.md")
                          if sentence in p.read_text(encoding="utf-8"))
        self.assertEqual(carrying, expected)
        for name in expected:
            with self.subTest(recipe=name):
                self.assertEqual((ROOT / "references" / name).read_text(encoding="utf-8").count(sentence), 1)


if __name__ == "__main__":
    unittest.main()
