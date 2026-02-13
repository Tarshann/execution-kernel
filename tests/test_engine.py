import unittest
import sys
import os
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

    def test_page_staging_missing(self):
        # Page doesn't have staging in default policies
        request = {"artifact_type": "page", "environment": "staging"}
        result = self.engine.evaluate(request)
        self.assertEqual(result["decision"], "DENY")

    def test_automation_development_missing(self):
        request = {"artifact_type": "automation", "environment": "development"}
        result = self.engine.evaluate(request)
        self.assertEqual(result["decision"], "DENY")

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

if __name__ == "__main__":
    unittest.main()
