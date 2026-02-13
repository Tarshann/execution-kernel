# 06_AGENT_CONTRACT.md

## Agent Contract: Defining the Interface for Governed Execution

The Agent Contract specifies the formal agreement and interaction protocol between autonomous agents and the Execution Kernel. It outlines the responsibilities of the agent, the services provided by the Kernel, and the expected behavior for all governed operations. This contract ensures a clear, auditable, and deterministic interface for agent execution.

## Core Principles of the Agent Contract:

1.  **Explicit Request Submission**: Agents must explicitly submit all execution requests to the Execution Kernel. No implicit actions are permitted for governed operations.
2.  **Contextual Information**: Each request must include sufficient contextual information for policy evaluation, such as agent identity, requested action, target resources, and any relevant environmental data.
3.  **Decision Adherence**: Agents must strictly adhere to the decisions returned by the Execution Kernel (`ALLOW`, `DENY`, `REQUIRE_APPROVAL`). Any deviation is a violation of the contract.
4.  **Error Handling**: Agents are responsible for gracefully handling `DENY` responses and `REQUIRE_APPROVAL` directives, including appropriate logging and user notification.
5.  **Statefulness (Kernel-Managed)**: The Kernel manages the state of ongoing governed operations (e.g., pending approvals), relieving agents from maintaining complex governance state.
6.  **Secure Communication**: All communication between agents and the Kernel must be secured using established cryptographic protocols.

## Agent Interface (Conceptual):

Agents will interact with the Execution Kernel through a standardized API or SDK, which will expose functions for:

-   `kernel.request_execution(action, context)`: Submits an execution request to the Kernel.
-   `kernel.get_decision(request_id)`: Retrieves the current decision for a previously submitted request.
-   `kernel.submit_approval(request_id, approval_token)`: Submits an approval for a `REQUIRE_APPROVAL` decision.
-   `kernel.log_event(event_type, details)`: Logs relevant events to the Kernel's Decision Log.

## Contract Enforcement:

The Execution Kernel will enforce the Agent Contract through:

-   **API Validation**: Strict validation of incoming request formats and content.
-   **Policy Evaluation**: Requests are evaluated against defined policies, and non-compliant requests are denied.
-   **Runtime Monitoring**: (Future Phase) Monitoring of agent behavior to detect and mitigate contract violations.

## Benefits of the Agent Contract:

-   **Predictable Behavior**: Ensures agents operate within defined governance boundaries.
-   **Enhanced Security**: Prevents unauthorized actions and resource access.
-   **Improved Auditability**: Provides a clear record of agent-Kernel interactions.
-   **Simplified Agent Development**: Agents can focus on their core logic, offloading governance concerns to the Kernel.

---

**Author**: Strix Labs  
**Version**: 1.0  
**Date**: February 12, 2026
