"""Interactive hero demonstration for NetOps Sentinel."""

from collections.abc import Callable, Mapping
from typing import Any

from netops_sentinel.actions import ApprovalService
from netops_sentinel.agent import AgentOrchestrator, AgentStatus, InvestigationState
from netops_sentinel.core.domain import Incident
from netops_sentinel.core.evidence import Evidence, EvidenceStore
from netops_sentinel.lab import (
    HERO_SUBSCRIBER_ID,
    build_hero_invalid_credentials_lab,
)
from netops_sentinel.recovery import RecoveryStatus

InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]

SEPARATOR = "-" * 60
BANNER_SEPARATOR = "=" * 60

HERO_INCIDENT_ID = "INC-HERO-0001"
HERO_REQUEST = "Customer DEMO-100042 has no Internet access. All ONT indicators appear normal."


def _emit(output_fn: OutputFunction, *lines: str) -> None:
    """Write one or more lines through the configured output function."""

    for line in lines:
        output_fn(line)


def _section(output_fn: OutputFunction, title: str) -> None:
    """Render a CLI section heading."""

    _emit(output_fn, "", title, SEPARATOR)


def _display_banner(output_fn: OutputFunction) -> None:
    """Render the application banner and synthetic-data notice."""

    _emit(
        output_fn,
        BANNER_SEPARATOR,
        " NETOPS SENTINEL",
        " Evidence-Driven Agentic AI for Telecom Network Operations",
        BANNER_SEPARATOR,
        "",
        "SYNTHETIC TELCO DIGITAL LAB",
        "No production or customer data is used.",
    )


def _display_incident(
    output_fn: OutputFunction,
    incident: Incident,
    subscriber_id: str,
) -> None:
    """Render the synthetic incident."""

    _section(output_fn, "INCIDENT")
    _emit(
        output_fn,
        f"ID          : {incident.incident_id}",
        f"Subscriber  : {subscriber_id}",
        f"Request     : {incident.request}",
    )


def _payload_value(payload: Mapping[str, Any], *keys: str) -> Any:
    """Return the first available payload value for the supplied keys."""

    for key in keys:
        if key in payload:
            return payload[key]

    return None


def format_evidence(evidence: Evidence) -> str:
    """Convert structured evidence into concise operator-facing text."""

    payload = evidence.payload
    evidence_type = evidence.evidence_type

    if evidence_type == "subscriber_status":
        status = _payload_value(payload, "account_status", "status")
        return f"Account status: {str(status).upper()}"

    if evidence_type == "online_session":
        online = payload.get("online", False)

        if not online:
            return "Session: OFFLINE"

        traffic = payload.get("traffic_bytes", 0)
        return f"Session: ONLINE | Traffic: {traffic} bytes"

    if evidence_type == "aaa_diagnostic":
        failure_count = payload.get("failure_count", 0)
        return f"Authentication failures: {failure_count}"

    if evidence_type == "normalized_aaa_condition":
        condition = payload.get("condition", "unknown")
        return f"Condition: {str(condition).upper()}"

    if evidence_type == "action_execution":
        status = payload.get("status", "unknown")
        return f"Synthetic credential reset: {str(status).upper()}"

    if evidence_type == "authentication_state":
        outcome = payload.get("outcome", "unknown")
        return f"Authentication: {str(outcome).upper()}"

    return f"{evidence.source}: {evidence_type}"


def _display_evidence(
    output_fn: OutputFunction,
    evidence_store: EvidenceStore,
    evidence_ids: tuple[str, ...],
) -> None:
    """Render selected evidence records."""

    for evidence_id in evidence_ids:
        evidence = evidence_store.get(evidence_id)
        _emit(
            output_fn,
            f"{evidence.evidence_id}  {format_evidence(evidence)}",
        )


def _display_investigation(
    output_fn: OutputFunction,
    state: InvestigationState,
    evidence_store: EvidenceStore,
) -> None:
    """Render the investigation trace and accumulated evidence."""

    _section(output_fn, "AGENT INVESTIGATION")

    for index, tool_name in enumerate(state.executed_tools, start=1):
        _emit(output_fn, f"[{index}] {tool_name}")

    _emit(output_fn, "")
    _display_evidence(
        output_fn,
        evidence_store,
        state.evidence_ids,
    )


def _display_diagnosis(
    output_fn: OutputFunction,
    state: InvestigationState,
) -> None:
    """Render the deterministic diagnosis."""

    if state.diagnosis is None:
        return

    diagnosis = state.diagnosis

    _section(output_fn, "DIAGNOSIS")
    _emit(
        output_fn,
        f"Root cause  : {diagnosis.root_cause.value.upper()}",
        f"Confidence  : {diagnosis.confidence:.0%}",
        "Evidence    : "
        + (
            ", ".join(diagnosis.supporting_evidence_ids)
            if diagnosis.supporting_evidence_ids
            else "none"
        ),
    )


def _display_proposed_action(
    output_fn: OutputFunction,
    state: InvestigationState,
) -> None:
    """Render the proposed action and its safety level."""

    if state.proposed_action is None:
        return

    action = state.proposed_action

    _section(output_fn, "PROPOSED ACTION")
    _emit(
        output_fn,
        f"Action      : {action.action_type.value.upper()}",
        f"Safety      : {action.safety_level.value.upper()}",
    )


def _approval_requested(
    *,
    input_fn: InputFunction,
    output_fn: OutputFunction,
) -> bool:
    """Request explicit fail-safe human approval."""

    _section(output_fn, "HUMAN APPROVAL REQUIRED")

    answer = input_fn("Approve controlled synthetic action? [y/N]: ").strip().casefold()

    return answer in {"y", "yes"}


def _display_not_approved(output_fn: OutputFunction) -> None:
    """Render the fail-safe no-mutation outcome."""

    _section(output_fn, "ACTION NOT APPROVED")
    _emit(
        output_fn,
        "No mutation was executed.",
        "Investigation remains WAITING_APPROVAL.",
    )


def _display_recovery(
    output_fn: OutputFunction,
    *,
    before: InvestigationState,
    after: InvestigationState,
    evidence_store: EvidenceStore,
) -> None:
    """Render post-approval execution and recovery evidence."""

    previous_count = len(before.evidence_ids)
    new_evidence_ids = after.evidence_ids[previous_count:]

    if new_evidence_ids:
        _section(output_fn, "CONTROLLED EXECUTION")

        execution_ids = new_evidence_ids[:1]
        _display_evidence(
            output_fn,
            evidence_store,
            execution_ids,
        )

    verification_ids = new_evidence_ids[1:]

    if verification_ids:
        _section(output_fn, "RECOVERY VERIFICATION")
        _display_evidence(
            output_fn,
            evidence_store,
            verification_ids,
        )

    _section(output_fn, "RESULT")

    recovered = (
        after.recovery_result is not None
        and after.recovery_result.status is RecoveryStatus.RECOVERED
        and after.status is AgentStatus.RESOLVED
    )

    if recovered:
        _emit(
            output_fn,
            "RECOVERED",
            "Incident lifecycle completed successfully.",
        )
    else:
        _emit(
            output_fn,
            after.status.value.upper(),
            "Recovery could not be confirmed.",
        )


def main(
    *,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> int:
    """Run the synthetic NetOps Sentinel hero scenario."""

    repository = build_hero_invalid_credentials_lab()
    evidence_store = EvidenceStore()
    approval_service = ApprovalService()

    orchestrator = AgentOrchestrator(
        repository=repository,
        evidence_store=evidence_store,
        approval_service=approval_service,
    )

    incident = Incident(
        incident_id=HERO_INCIDENT_ID,
        request=HERO_REQUEST,
        subscriber_id=HERO_SUBSCRIBER_ID,
    )

    _display_banner(output_fn)
    _display_incident(
        output_fn,
        incident,
        HERO_SUBSCRIBER_ID,
    )

    state = orchestrator.investigate(
        incident=incident,
        subscriber_id=HERO_SUBSCRIBER_ID,
    )

    _display_investigation(
        output_fn,
        state,
        evidence_store,
    )
    _display_diagnosis(output_fn, state)
    _display_proposed_action(output_fn, state)

    if state.status is not AgentStatus.WAITING_APPROVAL:
        _section(output_fn, "RESULT")
        _emit(output_fn, state.status.value.upper())
        return 0

    if state.proposed_action is None:
        _section(output_fn, "RESULT")
        _emit(output_fn, "FAILED", "No proposed action is available.")
        return 1

    if not _approval_requested(
        input_fn=input_fn,
        output_fn=output_fn,
    ):
        _display_not_approved(output_fn)
        return 0

    approval = approval_service.approve(
        state.proposed_action,
        approved_by="demo-operator",
    )

    _section(output_fn, "APPROVAL")
    _emit(
        output_fn,
        f"Approved by : {approval.approved_by}",
    )

    final_state = orchestrator.resume_after_approval(
        state=state,
        approval=approval,
    )

    _display_recovery(
        output_fn,
        before=state,
        after=final_state,
        evidence_store=evidence_store,
    )

    return 0 if final_state.status is AgentStatus.RESOLVED else 1


if __name__ == "__main__":
    raise SystemExit(main())
