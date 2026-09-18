"""Authentication state diagnostic tools."""

from netops_sentinel.core.evidence import Evidence, EvidenceKind
from netops_sentinel.tools.base import ToolContext


class AuthenticationStateTool:
    """Read the latest synthetic authentication outcome."""

    name = "auth.get_state"

    def execute(
        self,
        *,
        subscriber_id: str,
        context: ToolContext,
    ) -> Evidence:
        """Record the latest authentication state as raw evidence."""

        events = context.repository.list_radius_events(subscriber_id)
        latest_event = events[-1] if events else None

        return context.evidence_store.append(
            incident_id=context.incident_id,
            kind=EvidenceKind.RAW,
            source=self.name,
            evidence_type="authentication_state",
            payload={
                "subscriber_id": subscriber_id,
                "outcome": (latest_event.outcome.value if latest_event is not None else "unknown"),
                "event_id": (latest_event.event_id if latest_event is not None else None),
                "timestamp": (
                    latest_event.timestamp.isoformat() if latest_event is not None else None
                ),
            },
        )
