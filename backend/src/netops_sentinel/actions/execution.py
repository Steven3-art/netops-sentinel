"""Controlled execution of approved synthetic actions."""

from datetime import UTC, datetime
from ipaddress import IPv4Address

from netops_sentinel.actions.approval import Approval, ApprovalService
from netops_sentinel.actions.models import (
    ActionType,
    PolicyDecision,
    ProposedAction,
)
from netops_sentinel.actions.policy import SafetyPolicy
from netops_sentinel.core.evidence import Evidence, EvidenceKind, EvidenceStore
from netops_sentinel.lab.models import (
    AuthenticationOutcome,
    RadiusEvent,
    Session,
)
from netops_sentinel.lab.repository import TelcoLabRepository


class ActionExecutionError(RuntimeError):
    """Raised when a proposed action cannot be safely executed."""


class ControlledActionExecutor:
    """Execute explicitly approved mutations against the synthetic lab."""

    def __init__(
        self,
        *,
        approval_service: ApprovalService,
        safety_policy: SafetyPolicy,
    ) -> None:
        self._approval_service = approval_service
        self._safety_policy = safety_policy

    def execute(
        self,
        *,
        action: ProposedAction,
        approval: Approval,
        subscriber_id: str,
        repository: TelcoLabRepository,
        evidence_store: EvidenceStore,
    ) -> Evidence:
        """Validate approval and execute a controlled synthetic mutation."""

        self._approval_service.validate(
            action=action,
            approval=approval,
        )

        policy = self._safety_policy.evaluate(
            action,
            approved=True,
        )

        if policy.decision is not PolicyDecision.ALLOWED:
            raise ActionExecutionError(f"Action execution denied by safety policy: {policy.reason}")

        if action.action_type is not ActionType.REQUEST_CREDENTIAL_RESET:
            raise ActionExecutionError(f"Unsupported mutating action: {action.action_type.value}")

        return self._execute_credential_reset(
            action=action,
            subscriber_id=subscriber_id,
            repository=repository,
            evidence_store=evidence_store,
        )

    @staticmethod
    def _execute_credential_reset(
        *,
        action: ProposedAction,
        subscriber_id: str,
        repository: TelcoLabRepository,
        evidence_store: EvidenceStore,
    ) -> Evidence:
        """Simulate credential recovery in the synthetic Telco Digital Lab."""

        recovery_time = datetime(2026, 9, 17, 12, 30, tzinfo=UTC)

        repository.add_radius_event(
            RadiusEvent(
                event_id="RAD-0013",
                subscriber_id=subscriber_id,
                timestamp=recovery_time,
                outcome=AuthenticationOutcome.SUCCESS,
                diagnostic="Authentication successful",
            )
        )

        repository.set_session(
            Session(
                subscriber_id=subscriber_id,
                online=True,
                ip_address=IPv4Address("198.51.100.42"),
                started_at=recovery_time,
                traffic_bytes=4096,
            )
        )

        return evidence_store.append(
            incident_id=action.incident_id,
            kind=EvidenceKind.RAW,
            source="credentials.execute_reset",
            evidence_type="action_execution",
            payload={
                "subscriber_id": subscriber_id,
                "action": action.action_type.value,
                "status": "success",
            },
        )
