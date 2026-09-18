"""Subscriber diagnostic tools."""

from netops_sentinel.core.evidence import Evidence, EvidenceKind
from netops_sentinel.tools.base import ToolContext


class SubscriberStatusTool:
    """Read the current synthetic subscriber status."""

    name = "subscriber.get_status"

    def execute(
        self,
        *,
        subscriber_id: str,
        context: ToolContext,
    ) -> Evidence:
        """Query subscriber state and record it as raw evidence."""

        subscriber = context.repository.get_subscriber(subscriber_id)

        return context.evidence_store.append(
            incident_id=context.incident_id,
            kind=EvidenceKind.RAW,
            source=self.name,
            evidence_type="subscriber_status",
            payload={
                "subscriber_id": subscriber.subscriber_id,
                "service": subscriber.service.value,
                "account_status": subscriber.account_status.value,
                "bandwidth_profile": subscriber.bandwidth_profile,
            },
        )
