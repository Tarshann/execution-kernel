import json
import hashlib
from datetime import datetime

class PolicyEngine:
    def __init__(self, policies=None):
        # Default policies for Phase 1
        self.policies = policies or {
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
        self.policy_version = hashlib.sha256(json.dumps(self.policies, sort_keys=True).encode()).hexdigest()

    def evaluate(self, request):
        """
        Evaluates an execution request against the defined policies.
        """
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
                    reason = f"{risk_level.capitalize()}-risk action in {environment} environment. Requires {approvals_required} approval(s)."

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
    # Example usage
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
