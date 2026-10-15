"""Bind the hosted brief, compatibility source and both PDF artifacts."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BriefArtifactTests(unittest.TestCase):
    def test_current_publication_copy_has_no_temporary_status_claims(self):
        for relative in ('README.md', 'docs/brief/anti-dark-code-brief.html', 'PLUGINS.md', 'docs/index.html'):
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text(encoding="utf-8").casefold()
                self.assertNotIn("for the unpublished", text)
                self.assertNotIn("unpublished preview candidate", text)
                self.assertNotIn("publishing remains on hold", text)

    def test_hosted_source_and_compatibility_copy_match(self):
        source = ROOT / 'docs/brief/anti-dark-code-brief.html'
        self.assertEqual(source.read_bytes(), (ROOT / 'brief/anti-dark-code-brief.html').read_bytes())
        self.assertNotIn('Local design preview', source.read_text(encoding="utf-8"))

    def test_both_palettes_match_source_renderer_and_artifact(self):
        version = (ROOT / 'skills/anti-dark-code/VERSION').read_text(encoding="utf-8").strip()
        for theme in ('light', 'dark'):
            with self.subTest(theme=theme):
                name = 'anti-dark-code-brief' + ('-dark' if theme == 'dark' else '') + '.pdf'
                pdf = ROOT / 'brief' / name
                record = json.loads(pdf.with_suffix('.pdf.provenance.json').read_text(encoding="utf-8"))
                self.assertTrue(pdf.read_bytes().startswith(b'%PDF-'))
                self.assertEqual(record['version'], version)
                self.assertEqual(record['color_scheme'], theme)
                self.assertEqual(record['source_path'], 'docs/brief/anti-dark-code-brief.html')
                self.assertEqual(record['source_sha256'], digest(ROOT / record['source_path']))
                self.assertEqual(record['renderer_sha256'], digest(ROOT / 'design/render-brief-pdf.py'))
                self.assertEqual(record['pdf_sha256'], digest(pdf))

    def test_readme_and_homepage_expose_the_brief(self):
        readme = (ROOT / 'README.md').read_text(encoding="utf-8")
        website = (ROOT / 'docs/index.html').read_text(encoding="utf-8")
        self.assertIn('https://lynxtwo.github.io/anti-dark-code-skill/brief/anti-dark-code-brief.html', readme)
        self.assertIn('href="brief/anti-dark-code-brief.html"', website)
        for name in ('anti-dark-code-brief.pdf', 'anti-dark-code-brief-dark.pdf'):
            self.assertIn('brief/' + name, readme)
            self.assertIn('brief/' + name, website)


if __name__ == '__main__':
    unittest.main()
