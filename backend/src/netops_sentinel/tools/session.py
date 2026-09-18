"""Subscriber session diagnostic tools."""

from netops_sentinel.core.evidence import Evidence, EvidenceKind
from netops_sentinel.tools.base import ToolContext


class OnlineSessionTool:
    """Read the current synthetic subscriber session."""

    name = "session.get_online_session"

    def execute(
        self,
        *,
        subscriber_id: str,
        context: ToolContext,
    ) -> Evidence:
        """Query current session state and record it as raw evidence."""

        session = context.repository.get_session(subscriber_id)

        return context.evidence_store.append(
            incident_id=context.incident_id,
            kind=EvidenceKind.RAW,
            source=self.name,
            evidence_type="online_session",
            payload={
                "subscriber_id": session.subscriber_id,
                "online": session.online,
                "ip_address": (str(session.ip_address) if session.ip_address is not None else None),
                "started_at": (
                    session.started_at.isoformat() if session.started_at is not None else None
                ),
                "traffic_bytes": session.traffic_bytes,
            },
        )
