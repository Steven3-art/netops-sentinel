"""Evidence-based recovery verification."""

from dataclasses import dataclass
from enum import StrEnum

from netops_sentinel.core.evidence import Evidence


class RecoveryStatus(StrEnum):
    """Outcome of recovery verification."""

    RECOVERED = "recovered"
    NOT_RECOVERED = "not_recovered"


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    """Result of evidence-based recovery verification."""

    status: RecoveryStatus
    supporting_evidence_ids: tuple[str, ...]


class RecoveryVerifier:
    """Verify recovery using post-action observations."""

    def verify(
        self,
        *,
        session_evidence: Evidence,
        authentication_evidence: Evidence,
    ) -> RecoveryResult:
        """Determine whether service recovery is demonstrated by evidence."""

        session_recovered = (
            session_evidence.evidence_type == "online_session"
            and session_evidence.payload.get("online") is True
            and isinstance(session_evidence.payload.get("traffic_bytes"), int)
            and session_evidence.payload["traffic_bytes"] > 0
        )

        authentication_recovered = (
            authentication_evidence.evidence_type == "authentication_state"
            and authentication_evidence.payload.get("outcome") == "success"
        )

        if session_recovered and authentication_recovered:
            return RecoveryResult(
                status=RecoveryStatus.RECOVERED,
                supporting_evidence_ids=(
                    session_evidence.evidence_id,
                    authentication_evidence.evidence_id,
                ),
            )

        return RecoveryResult(
            status=RecoveryStatus.NOT_RECOVERED,
            supporting_evidence_ids=(),
        )
