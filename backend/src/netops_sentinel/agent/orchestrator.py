"""Explicit state-machine orchestrator for NetOps Sentinel."""

from netops_sentinel.aaa import AAAEvidenceProcessor
from netops_sentinel.actions import (
    ActionRecommendationEngine,
    Approval,
    ApprovalService,
    ControlledActionExecutor,
    PolicyDecision,
    SafetyPolicy,
)
from netops_sentinel.agent.models import AgentStatus, InvestigationState
from netops_sentinel.agent.planner import (
    DeterministicPlanner,
    PlannerDecisionType,
)
from netops_sentinel.core.domain import Incident, RootCause
from netops_sentinel.core.evidence import EvidenceStore
from netops_sentinel.diagnosis import DeterministicDiagnosisEngine
from netops_sentinel.lab.repository import TelcoLabRepository
from netops_sentinel.recovery import RecoveryStatus, RecoveryVerifier
from netops_sentinel.tools import (
    AuthenticationStateTool,
    OnlineSessionTool,
    RadiusFailuresTool,
    SubscriberStatusTool,
    ToolContext,
)


class AgentOrchestrationError(RuntimeError):
    """Raised when the agent cannot safely continue its workflow."""


class InvestigationStepLimitError(AgentOrchestrationError):
    """Raised when an investigation exceeds its bounded step count."""


class AgentOrchestrator:
    """Coordinate evidence-driven investigation and controlled recovery."""

    MAX_INVESTIGATION_STEPS = 10

    def __init__(
        self,
        *,
        repository: TelcoLabRepository,
        evidence_store: EvidenceStore,
        approval_service: ApprovalService,
    ) -> None:
        self._repository = repository
        self._evidence_store = evidence_store
        self._approval_service = approval_service

        self._planner = DeterministicPlanner()
        self._aaa_processor = AAAEvidenceProcessor()
        self._diagnosis_engine = DeterministicDiagnosisEngine()
        self._recommendation_engine = ActionRecommendationEngine()
        self._safety_policy = SafetyPolicy()
        self._recovery_verifier = RecoveryVerifier()

        self._subscriber_tool = SubscriberStatusTool()
        self._session_tool = OnlineSessionTool()
        self._radius_tool = RadiusFailuresTool()
        self._authentication_tool = AuthenticationStateTool()

        self._executor = ControlledActionExecutor(
            approval_service=self._approval_service,
            safety_policy=self._safety_policy,
        )

    def investigate(
        self,
        *,
        incident: Incident,
        subscriber_id: str,
    ) -> InvestigationState:
        """Run investigation until diagnosis, escalation, or approval boundary."""

        state = InvestigationState(
            incident_id=incident.incident_id,
            subscriber_id=subscriber_id,
            status=AgentStatus.INVESTIGATING,
        )

        context = self._build_tool_context(state)

        while state.step_count < self.MAX_INVESTIGATION_STEPS:
            decision = self._planner.next_step(
                incident_id=state.incident_id,
                evidence_store=self._evidence_store,
            )

            if decision.decision_type is PlannerDecisionType.DIAGNOSE:
                return self._diagnose_and_recommend(state)

            if decision.tool_name is None:
                raise AgentOrchestrationError(
                    "Planner requested tool execution without a tool name."
                )

            state = self._execute_investigation_tool(
                state=state,
                context=context,
                tool_name=decision.tool_name,
            )

        raise InvestigationStepLimitError(
            f"Investigation exceeded {self.MAX_INVESTIGATION_STEPS} steps."
        )

    def resume_after_approval(
        self,
        *,
        state: InvestigationState,
        approval: Approval,
    ) -> InvestigationState:
        """Resume a paused workflow after explicit human approval."""

        if state.status is not AgentStatus.WAITING_APPROVAL:
            raise AgentOrchestrationError(
                "Only an investigation waiting for approval may be resumed."
            )

        if state.proposed_action is None:
            raise AgentOrchestrationError("Cannot resume without a proposed action.")

        self._approval_service.validate(
            action=state.proposed_action,
            approval=approval,
        )

        executing_state = state.model_copy(
            update={
                "status": AgentStatus.EXECUTING,
                "approval": approval,
            }
        )

        execution_evidence = self._executor.execute(
            action=state.proposed_action,
            approval=approval,
            subscriber_id=state.subscriber_id,
            repository=self._repository,
            evidence_store=self._evidence_store,
        )

        executing_state = self._record_evidence(
            executing_state,
            evidence_id=execution_evidence.evidence_id,
        )

        return self._verify_recovery(executing_state)

    def _execute_investigation_tool(
        self,
        *,
        state: InvestigationState,
        context: ToolContext,
        tool_name: str,
    ) -> InvestigationState:
        """Execute one selected diagnostic tool and record its evidence."""

        if tool_name == self._subscriber_tool.name:
            evidence = self._subscriber_tool.execute(
                subscriber_id=state.subscriber_id,
                context=context,
            )

        elif tool_name == self._session_tool.name:
            evidence = self._session_tool.execute(
                subscriber_id=state.subscriber_id,
                context=context,
            )

        elif tool_name == self._radius_tool.name:
            raw_evidence = self._radius_tool.execute(
                subscriber_id=state.subscriber_id,
                context=context,
            )

            normalized_evidence = self._aaa_processor.process(
                raw_evidence=raw_evidence,
                evidence_store=self._evidence_store,
            )

            return state.model_copy(
                update={
                    "executed_tools": (*state.executed_tools, tool_name),
                    "evidence_ids": (
                        *state.evidence_ids,
                        raw_evidence.evidence_id,
                        normalized_evidence.evidence_id,
                    ),
                    "step_count": state.step_count + 1,
                }
            )

        else:
            raise AgentOrchestrationError(f"Unsupported investigation tool: {tool_name}")

        return state.model_copy(
            update={
                "executed_tools": (*state.executed_tools, tool_name),
                "evidence_ids": (*state.evidence_ids, evidence.evidence_id),
                "step_count": state.step_count + 1,
            }
        )

    def _diagnose_and_recommend(
        self,
        state: InvestigationState,
    ) -> InvestigationState:
        """Diagnose accumulated evidence and produce a controlled recommendation."""

        diagnosing_state = state.model_copy(update={"status": AgentStatus.DIAGNOSING})

        diagnosis = self._diagnosis_engine.diagnose(
            incident_id=state.incident_id,
            evidence_store=self._evidence_store,
        )

        if diagnosis.root_cause is RootCause.UNKNOWN:
            return diagnosing_state.model_copy(
                update={
                    "status": AgentStatus.ESCALATED,
                    "diagnosis": diagnosis,
                }
            )

        recommending_state = diagnosing_state.model_copy(
            update={
                "status": AgentStatus.RECOMMENDING,
                "diagnosis": diagnosis,
            }
        )

        action = self._recommendation_engine.recommend(diagnosis)
        policy = self._safety_policy.evaluate(action)

        if policy.decision is PolicyDecision.HUMAN_APPROVAL_REQUIRED:
            return recommending_state.model_copy(
                update={
                    "status": AgentStatus.WAITING_APPROVAL,
                    "proposed_action": action,
                }
            )

        return recommending_state.model_copy(
            update={
                "status": AgentStatus.ESCALATED,
                "proposed_action": action,
            }
        )

    def _verify_recovery(
        self,
        state: InvestigationState,
    ) -> InvestigationState:
        """Re-observe the lab and verify actual post-action recovery."""

        verifying_state = state.model_copy(update={"status": AgentStatus.VERIFYING_RECOVERY})

        context = self._build_tool_context(verifying_state)

        session_evidence = self._session_tool.execute(
            subscriber_id=state.subscriber_id,
            context=context,
        )

        authentication_evidence = self._authentication_tool.execute(
            subscriber_id=state.subscriber_id,
            context=context,
        )

        recovery = self._recovery_verifier.verify(
            session_evidence=session_evidence,
            authentication_evidence=authentication_evidence,
        )

        status = (
            AgentStatus.RESOLVED
            if recovery.status is RecoveryStatus.RECOVERED
            else AgentStatus.ESCALATED
        )

        return verifying_state.model_copy(
            update={
                "status": status,
                "executed_tools": (
                    *verifying_state.executed_tools,
                    self._session_tool.name,
                    self._authentication_tool.name,
                ),
                "evidence_ids": (
                    *verifying_state.evidence_ids,
                    session_evidence.evidence_id,
                    authentication_evidence.evidence_id,
                ),
                "recovery_result": recovery,
                "step_count": verifying_state.step_count + 2,
            }
        )

    def _build_tool_context(
        self,
        state: InvestigationState,
    ) -> ToolContext:
        """Build the shared context used by diagnostic tools."""

        return ToolContext(
            incident_id=state.incident_id,
            repository=self._repository,
            evidence_store=self._evidence_store,
        )

    @staticmethod
    def _record_evidence(
        state: InvestigationState,
        *,
        evidence_id: str,
    ) -> InvestigationState:
        """Return state containing one additional evidence identifier."""

        return state.model_copy(
            update={
                "evidence_ids": (*state.evidence_ids, evidence_id),
                "step_count": state.step_count + 1,
            }
        )
