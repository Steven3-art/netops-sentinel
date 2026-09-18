"""RADIUS diagnostic tools."""

from netops_sentinel.core.evidence import Evidence, EvidenceKind
from netops_sentinel.tools.base import ToolContext


class RadiusFailuresTool:
    """Read failed synthetic RADIUS authentication events."""

    name = "radius.get_failures"

    def execute(
        self,
        *,
        subscriber_id: str,
        context: ToolContext,
    ) -> Evidence:
        """Record failed authentication activity as raw AAA evidence."""

        failures = context.repository.list_radius_failures(subscriber_id)

        latest_failure = failures[-1] if failures else None

        return context.evidence_store.append(
            incident_id=context.incident_id,
            kind=EvidenceKind.RAW,
            source=self.name,
            evidence_type="aaa_diagnostic",
            payload={
                "subscriber_id": subscriber_id,
                "failure_count": len(failures),
                "latest_event_id": (
                    latest_failure.event_id if latest_failure is not None else None
                ),
                "latest_timestamp": (
                    latest_failure.timestamp.isoformat() if latest_failure is not None else None
                ),
                "message": (
                    latest_failure.diagnostic
                    if latest_failure is not None
                    else "No failed authentication event"
                ),
            },
        )
