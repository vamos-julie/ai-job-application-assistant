"""Offline integration checks: temporary counters, fake secrets, mocked OpenAI."""
import ast
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import streamlit as st
from streamlit.testing.v1 import AppTest

SOURCE = (Path(__file__).resolve().parents[1] / "app.py").read_text()


class PublicLiveTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.usage_dir = Path(self.directory.name)
        st.cache_resource.clear()
        self.addCleanup(st.cache_resource.clear)
        self.client = MagicMock()
        self.client.responses.create.return_value.output_text = "Mocked analysis result"
        self.factory = patch("openai.OpenAI", return_value=self.client).start()
        self.addCleanup(patch.stopall)
        # Redirect the existing app to temporary files, never real usage or secrets.
        source = SOURCE.replace('USAGE_DIR = Path(".usage")', f'USAGE_DIR = Path({str(self.usage_dir)!r})')
        self.app = AppTest.from_string(source, default_timeout=15)
        self.app.secrets.update({
            "OPENAI_API_KEY": "offline-test-key",
            "GUEST_PASSWORD": "test-guest",
            "OWNER_PASSWORD": "test-owner",
        })
        self.app.run()
        self.assert_clean()

    def assert_clean(self):
        self.assertEqual(list(self.app.exception), [])

    def live(self):
        self.app.radio[0].set_value("Live analysis").run()
        self.assert_clean()

    def button(self, label):
        return next(button for button in self.app.button if button.label == label)

    def run_analysis(self, jd="Example job", cv="Example CV"):
        self.app.text_area[0].set_value(jd)
        self.app.text_area[1].set_value(cv)
        self.button("Run live analysis").click().run()
        self.assert_clean()

    def unlock(self, password):
        self.app.text_input[0].set_value(password)
        self.button("Unlock live analysis").click().run()
        self.assert_clean()

    def usage(self, pool):
        path = self.usage_dir / f"{pool}_usage.json"
        return json.loads(path.read_text()) if path.exists() else {}

    def seed(self, pool, count):
        # Date is calculated exactly as the app does, using Asia/Nicosia.
        from datetime import datetime
        from zoneinfo import ZoneInfo
        today = datetime.now(ZoneInfo("Asia/Nicosia")).date().isoformat()
        (self.usage_dir / f"{pool}_usage.json").write_text(json.dumps({today: count}))

    def test_demo_never_creates_client_or_calls_api(self):
        self.factory.assert_not_called()
        self.client.responses.create.assert_not_called()
        self.assertFalse(list(self.usage_dir.iterdir()))

    def test_public_all_analysis_types_count_only_public_and_keep_download(self):
        self.live()
        for analysis_type in self.app.selectbox[0].options:
            with self.subTest(analysis_type=analysis_type):
                self.app.selectbox[0].set_value(analysis_type).run()
                self.run_analysis()
        self.assertEqual(self.client.responses.create.call_count, 5)
        self.assertEqual(sum(self.usage("public").values()), 5)
        self.assertEqual(self.usage("guest"), {})
        self.assertTrue(self.button("Run live analysis").disabled)
        self.assertIn("Mocked analysis result", self.app.session_state.last_live_output)
        self.assertTrue(self.app.get("download_button"))
        self.assertTrue(any("0 / 5" in item.value for item in self.app.info))
        self.assertTrue(any("free live analysis limit" in item.value for item in self.app.warning))
        self.app.radio[0].set_value("Demo mode").run()
        self.live()
        self.assertTrue(self.button("Run live analysis").disabled)
        self.assertEqual(self.client.responses.create.call_count, 5)

    def test_exhausted_public_allows_guest_then_owner(self):
        self.seed("public", 5)
        self.live()
        self.assertTrue(self.button("Run live analysis").disabled)
        self.unlock("test-guest")
        self.assertEqual(self.app.session_state.access_level, "guest")
        self.run_analysis()
        self.assertEqual(sum(self.usage("guest").values()), 1)
        self.assertEqual(sum(self.usage("public").values()), 5)
        self.seed("guest", 18)
        self.app.run()
        self.assertTrue(self.button("Run live analysis").disabled)
        self.unlock("test-owner")
        self.run_analysis()
        self.assertEqual(sum(self.usage("guest").values()), 18)
        self.assertEqual(sum(self.usage("public").values()), 5)
        self.assertEqual(self.client.responses.create.call_count, 2)

    def test_guest_exhaustion_does_not_block_public(self):
        self.seed("guest", 18)
        self.live()
        self.run_analysis()
        self.assertEqual(sum(self.usage("public").values()), 1)
        self.assertEqual(sum(self.usage("guest").values()), 18)

    def test_invalid_inputs_do_not_call_api(self):
        self.live()
        for jd, cv in [("", "CV"), ("JD", "  "), ("x" * 12001, "CV"), ("JD", "x" * 10001)]:
            with self.subTest(jd_length=len(jd), cv_length=len(cv)):
                self.run_analysis(jd, cv)
        self.client.responses.create.assert_not_called()
        self.assertEqual(self.usage("public"), {})

    def test_errors_and_empty_responses_do_not_count_for_public_or_guest(self):
        self.live()
        for password in [None, "test-guest"]:
            if password:
                self.unlock(password)
            for output in [None, "", "   "]:
                self.client.responses.create.return_value.output_text = output
                self.run_analysis()
                self.assertTrue(self.app.error)
            self.client.responses.create.side_effect = RuntimeError("Mock API failure")
            self.run_analysis()
            self.client.responses.create.side_effect = None
        self.assertEqual(self.usage("public"), {})
        self.assertEqual(self.usage("guest"), {})
        self.assertEqual(self.client.responses.create.call_count, 8)

    def test_mode_switches_preserve_guest_and_owner_access(self):
        self.live()
        for password, level in [("test-guest", "guest"), ("test-owner", "owner")]:
            self.unlock(password)
            self.app.radio[0].set_value("Demo mode").run()
            self.live()
            self.assertEqual(self.app.session_state.access_level, level)
            self.run_analysis()
        self.assertEqual(sum(self.usage("guest").values()), 1)
        self.assertEqual(self.usage("public"), {})

    def test_invalid_password_and_unknown_session_default_to_public(self):
        self.live()
        self.unlock("wrong")
        self.assertTrue(self.app.error)
        self.app.session_state.access_level = "invalid"
        self.app.run()
        self.run_analysis()
        self.assertEqual(sum(self.usage("public").values()), 1)
        self.assertEqual(self.usage("guest"), {})

    def test_new_visitor_shares_public_quota(self):
        self.live()
        self.run_analysis()
        # A fresh AppTest session, pointing at the same temporary storage.
        source = SOURCE.replace('USAGE_DIR = Path(".usage")', f'USAGE_DIR = Path({str(self.usage_dir)!r})')
        visitor = AppTest.from_string(source)
        visitor.run().radio[0].set_value("Live analysis").run()
        self.assertEqual(list(visitor.exception), [])
        self.assertTrue(any("4 / 5" in item.value for item in visitor.info))

    def test_prior_day_counters_reset_independently(self):
        for pool in ["public", "guest"]:
            (self.usage_dir / f"{pool}_usage.json").write_text('{"2000-01-01": 100}')
        self.live()
        self.assertTrue(any("5 / 5" in item.value for item in self.app.info))
        self.unlock("test-guest")
        self.assertTrue(any("Remaining today: 18" in item.value for item in self.app.info))


class QuotaGuardTests(unittest.TestCase):
    def test_immediate_guard_all_access_branches(self):
        # Isolate the actual guard without invoking the UI or client.
        tree = ast.parse(SOURCE)
        guard = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "check_live_quota_before_run")
        namespace = {
            "st": MagicMock(), "PUBLIC_LIMIT_MESSAGE": "Exhausted",
            "get_public_remaining_runs": MagicMock(return_value=0),
            "check_guest_quota_before_run": MagicMock(return_value=False),
        }
        exec(compile(ast.Module(body=[guard], type_ignores=[]), "app.py", "exec"), namespace)
        check = namespace[guard.name]
        self.assertFalse(check("public"))
        namespace["get_public_remaining_runs"].return_value = 1
        self.assertTrue(check("public"))
        self.assertFalse(check("guest"))
        namespace["check_guest_quota_before_run"].return_value = True
        self.assertTrue(check("guest"))
        self.assertTrue(check("owner"))
        self.assertFalse(check(None))
        self.assertFalse(check("invalid"))

    def test_no_duplicate_functions(self):
        names = [node.name for node in ast.walk(ast.parse(SOURCE)) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
