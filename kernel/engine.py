import json
import hashlib
import os
from datetime import datetime

DEFAULT_POLICY_PATH = os.path.join(os.path.dirname(__file__), "policies.json")

HARDCODED_DEFAULTS = {
    "webapp": {
        "production": {
            "risk_level": "high",
            "approvals_required": 2,
            "constraints": {"no_self_approval": True, "log_all_actions": True}
        },
        "staging": {
            "risk_level": "medium",
            "approvals_required": 1,
            "constraints": {"no_self_approval": False, "log_all_actions": True}
        }
    },
    "page": {
        "production": {
            "risk_level": "medium",
            "approvals_required": 1,
            "constraints": {"no_self_approval": False, "log_all_actions": True}
        },
        "development": {
            "risk_level": "low",
            "approvals_required": 0,
            "constraints": {"no_self_approval": False, "log_all_actions": False}
        }
    },
    "automation": {
        "production": {
            "risk_level": "high",
            "approvals_required": 1,
            "constraints": {"no_self_approval": True, "log_all_actions": True, "isolation_required": True}
        }
    }
}


class PolicyEngine:
    def __init__(self, policy_path=None, policies=None):
        """
        Initialize the PolicyEngine.

        Priority order:
        1. Explicit `policies` dict (for testing)
        2. Policy file at `policy_path`
        3. Policy file at POLICY_FILE env var
        4. Default policies.json alongside this module
        5. Hardcoded defaults
        """
        self._policy_path = None
        self._policy_mtime = None

        if policies:
            self.policies = policies
        else:
            resolved_path = policy_path or os.getenv("POLICY_FILE") or DEFAULT_POLICY_PATH
            if os.path.isfile(resolved_path):
                self._policy_path = resolved_path
                self.policies = self._load_from_file(resolved_path)
            else:
                self.policies = HARDCODED_DEFAULTS

        self._update_version()

    def _load_from_file(self, path):
        """Load policies from a JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        self._policy_mtime = os.path.getmtime(path)
        return data

    def _update_version(self):
        """Compute a deterministic hash of the current policy set."""
        self.policy_version = hashlib.sha256(
            json.dumps(self.policies, sort_keys=True).encode()
        ).hexdigest()

    def reload_if_changed(self):
        """
        Hot-reload: re-read the policy file if it has been modified since last load.
        Returns True if policies were reloaded, False otherwise.
        """
        if not self._policy_path:
            return False

        try:
            current_mtime = os.path.getmtime(self._policy_path)
            if current_mtime != self._policy_mtime:
                self.policies = self._load_from_file(self._policy_path)
                old_version = self.policy_version
                self._update_version()
                print(f"[KERNEL] Policies reloaded. Version {old_version[:12]}... -> {self.policy_version[:12]}...")
                return True
        except Exception as e:
            print(f"[KERNEL] Policy reload failed: {e}")
        return False

    def evaluate(self, request):
        """
        Evaluates an execution request against the defined policies.
        Automatically checks for policy file changes before each evaluation.
        """
        # Hot-reload check
        self.reload_if_changed()

        artifact_type = request.get("artifact_type")
        environment = request.get("environment")
        actions = request.get("actions", [])

        # Default decision
        decision = "DENY"
        risk_level = "critical"
        approvals_required = 99
        constraints = {}
        reason = "No matching policy found for the given artifact type and environment."

        # Policy lookup
        if artifact_type in self.policies:
            env_policies = self.policies[artifact_type]
            if environment in env_policies:
                policy = env_policies[environment]
                risk_level = policy["risk_level"]
                approvals_required = policy["approvals_required"]
                constraints = policy["constraints"]

                if approvals_required == 0:
                    decision = "ALLOW"
                    reason = f"Low-risk action in {environment} environment. No approval required."
                else:
                    decision = "REQUIRE_APPROVAL"
                    reason = (
                        f"{risk_level.capitalize()}-risk action in {environment} environment. "
                        f"Requires {approvals_required} approval(s)."
                    )

        return {
            "decision": decision,
            "risk_level": risk_level,
            "approvals_required": approvals_required,
            "constraints": constraints,
            "policy_version": self.policy_version,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


if __name__ == "__main__":
    engine = PolicyEngine()
    sample_request = {
        "artifact_type": "webapp",
        "environment": "production",
        "actions": ["deploy"],
        "agent_id": "agent-001",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    result = engine.evaluate(sample_request)
    print(json.dumps(result, indent=2))
