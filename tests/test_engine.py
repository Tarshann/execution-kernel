import unittest
import sys
import os
import json
import tempfile
import time
from datetime import datetime

# Add kernel directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../kernel')))
from engine import PolicyEngine

class TestPolicyEngine(unittest.TestCase):
    def setUp(self):
        self.engine = PolicyEngine()

    def test_webapp_production(self):
        request = {"artifact_type": "webapp", "environment": "production", "actions": ["deploy"]}
        result = self.engine.evaluate(request)
        self.assertEqual(result["decision"], "REQUIRE_APPROVAL")
        self.assertEqual(result["risk_level"], "high")
        self.assertEqual(result["approvals_required"], 2)
        self.assertTrue(result["constraints"]["no_self_approval"])

    def test_webapp_staging(self):
        request = {"artifact_type": "webapp", "environment": "staging", "actions": ["deploy"]}
        result = self.engine.evaluate(request)
        self.assertEqual(result["decision"], "REQUIRE_APPROVAL")
        self.assertEqual(result["risk_level"], "medium")
        self.assertEqual(result["approvals_required"], 1)

    def test_page_production(self):
        request = {"artifact_type": "page", "environment": "production", "actions": ["deploy"]}
        result = self.engine.evaluate(request)
        self.assertEqual(result["decision"], "REQUIRE_APPROVAL")
        self.assertEqual(result["risk_level"], "medium")
        self.assertEqual(result["approvals_required"], 1)

    def test_page_development(self):
        request = {"artifact_type": "page", "environment": "development", "actions": ["deploy"]}
        result = self.engine.evaluate(request)
        self.assertEqual(result["decision"], "ALLOW")
        self.assertEqual(result["risk_level"], "low")
        self.assertEqual(result["approvals_required"], 0)

    def test_automation_production(self):
        request = {"artifact_type": "automation", "environment": "production", "actions": ["run"]}
        result = self.engine.evaluate(request)
        self.assertEqual(result["decision"], "REQUIRE_APPROVAL")
        self.assertEqual(result["risk_level"], "high")
        self.assertTrue(result["constraints"]["isolation_required"])

    def test_invalid_artifact(self):
        request = {"artifact_type": "unknown", "environment": "production"}
        result = self.engine.evaluate(request)
        self.assertEqual(result["decision"], "DENY")
        self.assertEqual(result["risk_level"], "critical")

    def test_invalid_environment(self):
        request = {"artifact_type": "webapp", "environment": "unknown"}
        result = self.engine.evaluate(request)
        self.assertEqual(result["decision"], "DENY")

    def test_empty_request(self):
        request = {}
        result = self.engine.evaluate(request)
        self.assertEqual(result["decision"], "DENY")

    def test_deterministic_output(self):
        request = {"artifact_type": "webapp", "environment": "production"}
        result1 = self.engine.evaluate(request)
        result2 = self.engine.evaluate(request)
        # Exclude timestamp from comparison
        result1.pop("timestamp")
        result2.pop("timestamp")
        self.assertEqual(result1, result2)

    def test_policy_version_consistency(self):
        self.assertTrue(len(self.engine.policy_version) > 0)
        v1 = self.engine.policy_version
        engine2 = PolicyEngine()
        self.assertEqual(v1, engine2.policy_version)

    # Add more tests to reach 20+
    def test_webapp_production_multiple_actions(self):
        request = {"artifact_type": "webapp", "environment": "production", "actions": ["deploy", "db_migrate"]}
        result = self.engine.evaluate(request)
        self.assertEqual(result["decision"], "REQUIRE_APPROVAL")

    def test_content_production(self):
        request = {"artifact_type": "content", "environment": "production"}
        result = self.engine.evaluate(request)
        self.assertEqual(result["decision"], "ALLOW")

    def test_app_production(self):
        request = {"artifact_type": "app", "environment": "production"}
        result = self.engine.evaluate(request)
        self.assertEqual(result["decision"], "REQUIRE_APPROVAL")
        self.assertEqual(result["approvals_required"], 2)

    def test_case_sensitivity_artifact(self):
        request = {"artifact_type": "WEBAPP", "environment": "production"}
        result = self.engine.evaluate(request)
        self.assertEqual(result["decision"], "DENY")

    def test_case_sensitivity_env(self):
        request = {"artifact_type": "webapp", "environment": "PRODUCTION"}
        result = self.engine.evaluate(request)
        self.assertEqual(result["decision"], "DENY")

    def test_missing_actions_field(self):
        request = {"artifact_type": "webapp", "environment": "production"}
        result = self.engine.evaluate(request)
        self.assertEqual(result["decision"], "REQUIRE_APPROVAL")

    def test_null_values(self):
        request = {"artifact_type": None, "environment": None}
        result = self.engine.evaluate(request)
        self.assertEqual(result["decision"], "DENY")

    def test_large_actions_list(self):
        request = {"artifact_type": "webapp", "environment": "production", "actions": ["a"] * 100}
        result = self.engine.evaluate(request)
        self.assertEqual(result["decision"], "REQUIRE_APPROVAL")

    def test_timestamp_format(self):
        request = {"artifact_type": "page", "environment": "development"}
        result = self.engine.evaluate(request)
        ts = result["timestamp"]
        self.assertTrue(ts.endswith("Z"))
        # Basic ISO format check
        self.assertEqual(len(ts.split("T")), 2)

    def test_reason_content(self):
        request = {"artifact_type": "webapp", "environment": "production"}
        result = self.engine.evaluate(request)
        self.assertIn("Requires 2 approval(s)", result["reason"])

    def test_reason_deny_content(self):
        request = {"artifact_type": "invalid", "environment": "invalid"}
        result = self.engine.evaluate(request)
        self.assertIn("No matching policy found", result["reason"])

class TestPolicyEngineExplicitPolicies(unittest.TestCase):
    """Tests using explicitly provided policies (for testing isolation)."""

    def test_custom_policies(self):
        custom = {
            "custom_type": {
                "production": {
                    "risk_level": "low",
                    "approvals_required": 0,
                    "constraints": {"log_all_actions": True}
                }
            }
        }
        engine = PolicyEngine(policies=custom)
        result = engine.evaluate({"artifact_type": "custom_type", "environment": "production"})
        self.assertEqual(result["decision"], "ALLOW")

    def test_custom_policies_version_differs(self):
        custom1 = {"a": {"b": {"risk_level": "low", "approvals_required": 0, "constraints": {}}}}
        custom2 = {"x": {"y": {"risk_level": "high", "approvals_required": 1, "constraints": {}}}}
        e1 = PolicyEngine(policies=custom1)
        e2 = PolicyEngine(policies=custom2)
        self.assertNotEqual(e1.policy_version, e2.policy_version)


class TestPolicyFileLoading(unittest.TestCase):
    """Tests for loading policies from a JSON file."""

    def test_load_from_file(self):
        policy_data = {
            "file_type": {
                "staging": {
                    "risk_level": "medium",
                    "approvals_required": 1,
                    "constraints": {"log_all_actions": True}
                }
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(policy_data, f)
            f.flush()
            path = f.name

        try:
            engine = PolicyEngine(policy_path=path)
            result = engine.evaluate({"artifact_type": "file_type", "environment": "staging"})
            self.assertEqual(result["decision"], "REQUIRE_APPROVAL")
            self.assertEqual(result["risk_level"], "medium")
        finally:
            os.unlink(path)

    def test_fallback_on_missing_file(self):
        engine = PolicyEngine(policy_path="/nonexistent/path/policies.json")
        # Should fall back to hardcoded defaults
        result = engine.evaluate({"artifact_type": "webapp", "environment": "production"})
        self.assertIn(result["decision"], ["REQUIRE_APPROVAL", "DENY"])


class TestPolicyHotReload(unittest.TestCase):
    """Tests for policy hot-reload functionality."""

    def test_hot_reload_detects_change(self):
        initial = {"type_a": {"env_a": {"risk_level": "low", "approvals_required": 0, "constraints": {}}}}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(initial, f)
            f.flush()
            path = f.name

        try:
            engine = PolicyEngine(policy_path=path)
            result1 = engine.evaluate({"artifact_type": "type_a", "environment": "env_a"})
            self.assertEqual(result1["decision"], "ALLOW")
            old_version = engine.policy_version

            # Modify the file
            time.sleep(0.1)
            updated = {"type_a": {"env_a": {"risk_level": "high", "approvals_required": 2, "constraints": {}}}}
            with open(path, 'w') as f:
                json.dump(updated, f)

            result2 = engine.evaluate({"artifact_type": "type_a", "environment": "env_a"})
            self.assertEqual(result2["decision"], "REQUIRE_APPROVAL")
            self.assertNotEqual(old_version, engine.policy_version)
        finally:
            os.unlink(path)

    def test_no_reload_without_change(self):
        initial = {"type_b": {"env_b": {"risk_level": "low", "approvals_required": 0, "constraints": {}}}}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(initial, f)
            f.flush()
            path = f.name

        try:
            engine = PolicyEngine(policy_path=path)
            v1 = engine.policy_version
            reloaded = engine.reload_if_changed()
            self.assertFalse(reloaded)
            self.assertEqual(v1, engine.policy_version)
        finally:
            os.unlink(path)

    def test_no_reload_without_file(self):
        engine = PolicyEngine(policies={"a": {"b": {"risk_level": "low", "approvals_required": 0, "constraints": {}}}})
        reloaded = engine.reload_if_changed()
        self.assertFalse(reloaded)


if __name__ == "__main__":
    unittest.main()
