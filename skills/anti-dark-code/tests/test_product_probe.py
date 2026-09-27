"""Contrasting repository fixtures test advisory evidence, not feature correctness."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "adc.py"
spec = importlib.util.spec_from_file_location("product_probe_adc", SCRIPT)
adc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adc)


class ProductProbeTests(unittest.TestCase):
    def probe(self, files):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            for name, content in files.items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            return adc.probe_repo(root)

    def capabilities(self, profile):
        return {cap["id"]: cap for cap in adc.build_plan(profile)["capabilities"]}

    def test_inline_browser_app_has_source_storage_and_ui_obligations(self):
        profile = self.probe({"index.html": '<button id="save">Save</button><script>'
            'document.querySelector("button").onclick = () => localStorage.setItem("draft", "x");'
            '</script>'})
        self.assertIn("frontend", profile["repo_types"])
        for name in ("workflow_or_ui", "persistence"):
            self.assertFalse(profile["signals"][name]["documentation_only"])
            self.assertIn("source", profile["signals"][name]["evidence_classes"])
        self.assertEqual("selected", self.capabilities(profile)["V15"]["status"])

    def test_external_script_is_configuration_and_local_source_is_scanned(self):
        profile = self.probe({"index.htm": '<button>Go</button><script src="main.js"></script>',
                              "main.js": 'localStorage.getItem("draft");'})
        self.assertIn("frontend", profile["repo_types"])
        self.assertEqual("selected", self.capabilities(profile)["V15"]["status"])

    def test_prose_and_nonexecutable_data_do_not_become_application_evidence(self):
        for html in ('<p>Billing payment uses localStorage in a future app.</p>',
                     '<script type="application/json">{"billing":"localStorage"}</script>',
                     '<pre>&lt;script&gt;localStorage.getItem("billing")&lt;/script&gt;</pre>',
                     '<!-- <script>localStorage.getItem("billing")</script> -->',
                     '<template><button onclick="localStorage.clear()">Billing</button></template>'):
            with self.subTest(html=html):
                profile = self.probe({"index.html": html})
                self.assertNotIn("frontend", profile["repo_types"])
                self.assertNotEqual("selected", self.capabilities(profile)["V15"]["status"])
                entry = profile["signals"]["financial_or_entitlement"]
                self.assertFalse(entry.get("runtime_evidence", False))

    def test_form_controls_and_event_attributes_are_runtime_markup(self):
        for html in ('<form><input name="x"><button>Submit</button></form>',
                     '<div onclick="localStorage.clear()">Clear</div>',
                     '<script type="module">localStorage.getItem("x")</script>'):
            with self.subTest(html=html):
                profile = self.probe({"index.html": html})
                self.assertIn("frontend", profile["repo_types"])
                self.assertTrue(profile["signals"]["workflow_or_ui"]["runtime_evidence"])

    def test_framework_and_plain_browser_are_both_frontend(self):
        profile = self.probe({"package.json": json.dumps({"dependencies": {"react": "1"}})})
        self.assertIn("frontend", profile["repo_types"])

    def test_small_cli_is_not_inferred_to_be_new(self):
        profile = self.probe({"tool.py": 'import argparse\nif __name__ == "__main__":\n'
            '    argparse.ArgumentParser().parse_args()\n', "CHANGELOG.md": '# Maintained releases\n'})
        self.assertIn("cli-desktop", profile["repo_types"])
        self.assertNotIn("small-new", profile["repo_types"])
        self.assertEqual("unknown", profile["characteristics"]["maturity"])
        self.assertEqual("small", profile["characteristics"]["size_band"])

    def test_quoted_cli_example_is_not_an_entrypoint(self):
        profile = self.probe({"module.py": "example = '''import argparse\nif __name__ == \"__main__\": pass'''"})
        self.assertNotIn("cli-desktop", profile["repo_types"])

    def test_verifier_quoted_patterns_do_not_prove_product_domains(self):
        profile = self.probe({"verifier.py": 'import re\npattern = re.compile("payment billing simulation")\n'
            'def check(value): return pattern.search(value)\n'})
        self.assertEqual({"source_text": 1}, profile["signals"]["financial_or_entitlement"]["evidence_classes"])
        self.assertEqual("candidate", self.capabilities(profile)["V14"]["status"])

    def test_external_script_inline_fallback_is_inert(self):
        profile = self.probe({"index.html": '<script src="main.js">localStorage.clear()</script>'})
        self.assertIn("frontend", profile["repo_types"])
        self.assertFalse(profile["signals"]["persistence"]["runtime_evidence"])

    def test_declared_python_console_script_is_a_configured_cli(self):
        profile = self.probe({"pyproject.toml": '[project.scripts]\ntool = "app:main"\n'})
        self.assertIn("cli-desktop", profile["repo_types"])

    def test_same_tool_reads_explicit_checkout_instead_of_invocation_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            first, second = root / "first", root / "second"
            first.mkdir()
            second.mkdir()
            (first / "one.py").write_text("value = 1", encoding="utf-8")
            (second / "two.js").write_text("const value = 2;", encoding="utf-8")
            nested = first / "nested"
            nested.mkdir()
            for target, language in ((first, "Python"), (second, "JavaScript")):
                result = subprocess.run([sys.executable, "-B", str(SCRIPT), "probe", "--repo", str(target), "--json"],
                    cwd=nested, capture_output=True, text=True, check=True)
                self.assertEqual([language], [entry["name"] for entry in json.loads(result.stdout)["languages"]])
            refused = subprocess.run([sys.executable, "-B", str(SCRIPT), "probe", "--repo", str(root / "absent"), "--json"],
                cwd=first, capture_output=True, check=False)
            self.assertNotEqual(0, refused.returncode)
            self.assertEqual(["nested", "one.py"], sorted(path.name for path in first.iterdir()))
            self.assertEqual(["two.js"], [path.name for path in second.iterdir()])

    def test_fixtures_examples_and_catalogs_do_not_prove_product_billing(self):
        profile = self.probe({"tool.py": 'print("hello")',
            "tests/test_hostile.py": 'sample = "billing payment simulation sqlite"',
            "evals/runner.py": 'def simulation(payment): return payment',
            "examples/payment.py": 'billing = "payment"',
            "assets/risk-catalog.json": '{"billing": "payment simulation"}'})
        entry = profile["signals"]["financial_or_entitlement"]
        self.assertFalse(entry["runtime_evidence"])
        self.assertEqual("candidate", self.capabilities(profile)["V14"]["status"])
        self.assertEqual({"test", "example", "catalog"}, set(entry["evidence_classes"]))

    def test_capped_evidence_preserves_each_class_and_runtime_locator(self):
        files = {f"docs/{n:02d}.md": 'Billing payment simulation' for n in range(20)}
        files["src/pay.py"] = 'def billing(payment): return payment'
        files["tests/test_billing.py"] = 'def test_payment(): return "payment"'
        profile = self.probe(files)
        entry = profile["signals"]["financial_or_entitlement"]
        self.assertEqual({"prose": 20, "source": 1, "test": 1}, entry["evidence_classes"])
        self.assertIn("src/pay.py", entry["evidence_by_class"]["source"])
        self.assertIn("src/pay.py", entry["evidence"])
        self.assertLessEqual(len(entry["evidence"]), 12)
        plan = self.capabilities(profile)
        selected = [cap for cap in plan.values() if "financial_or_entitlement" in cap["reason"]]
        self.assertTrue(selected)
        self.assertTrue(all("src/pay.py" in cap["evidence"] for cap in selected))


if __name__ == "__main__":
    unittest.main()
