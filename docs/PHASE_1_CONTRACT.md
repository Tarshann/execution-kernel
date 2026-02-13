# Phase 1 Contract: Execution Kernel v1.1

This document defines the strict JSON schema for policy inputs and outputs for the Phase 1 implementation of the Execution Kernel.

## 1. Policy Input Schema (Execution Request)

The client (e.g., Shipping Factory) must submit a JSON object with the following fields:

```json
{
  "artifact_type": "string",      // e.g., "webapp", "page", "automation"
  "environment": "string",        // e.g., "production", "staging", "development"
  "actions": ["string"],          // e.g., ["deploy", "modify_db_schema"]
  "agent_id": "string",           // unique identifier for the agent
  "timestamp": "iso8601_string"   // current timestamp
}
```

## 2. Policy Output Schema (Governance Decision)

The Execution Kernel will return a JSON object with the following fields:

```json
{
  "decision": "string",           // "ALLOW", "DENY", "REQUIRE_APPROVAL"
  "risk_level": "string",         // "low", "medium", "high", "critical"
  "approvals_required": "integer", // number of human approvals needed
  "constraints": {
    "no_self_approval": "boolean",
    "log_all_actions": "boolean",
    "isolation_required": "boolean"
  },
  "policy_version": "string",     // hash or version string of the policy used
  "reason": "string"              // human-readable explanation of the decision
}
```

## 3. Validation Rules

- **Artifact Type**: Must be one of the pre-defined types in `CONTRACTS.md`.
- **Environment**: Must be a valid environment string.
- **Actions**: Must be a non-empty list of strings.
- **Decision**: The output must always include a clear decision.
- **Idempotency**: For the same input and policy version, the output must be identical.

---

**Version**: 1.1  
**Date**: February 12, 2026
