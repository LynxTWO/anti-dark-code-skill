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

    def test_five_task_cards_are_discoverable_from_core(self):
        core = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for name in ("understand", "investigate", "document", "verify", "remediate"):
            with self.subTest(task=name):
                target = f"references/tasks/{name}.md"
                self.assertIn(f"]({target})", core)
                self.assertTrue((ROOT / target).is_file())


if __name__ == "__main__":
    unittest.main()
