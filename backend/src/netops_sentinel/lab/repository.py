"""In-memory repository for the synthetic Telco Digital Lab."""

from netops_sentinel.lab.models import (
    AAAAccount,
    RadiusEvent,
    Session,
    Subscriber,
)


class LabEntityNotFoundError(LookupError):
    """Raised when a requested synthetic lab entity does not exist."""


class DuplicateLabEntityError(ValueError):
    """Raised when a unique synthetic lab entity already exists."""


class TelcoLabRepository:
    """Deterministic in-memory repository for synthetic telecom state."""

    def __init__(self) -> None:
        self._subscribers: dict[str, Subscriber] = {}
        self._aaa_accounts: dict[str, AAAAccount] = {}
        self._sessions: dict[str, Session] = {}
        self._radius_events: dict[str, RadiusEvent] = {}

    def add_subscriber(self, subscriber: Subscriber) -> None:
        """Add a unique synthetic subscriber."""

        if subscriber.subscriber_id in self._subscribers:
            raise DuplicateLabEntityError(
                f"Subscriber '{subscriber.subscriber_id}' already exists."
            )

        self._subscribers[subscriber.subscriber_id] = subscriber

    def get_subscriber(self, subscriber_id: str) -> Subscriber:
        """Return a synthetic subscriber by identifier."""

        try:
            return self._subscribers[subscriber_id]
        except KeyError as exc:
            raise LabEntityNotFoundError(f"Subscriber '{subscriber_id}' was not found.") from exc

    def add_aaa_account(self, account: AAAAccount) -> None:
        """Add a unique AAA account for a synthetic subscriber."""

        self._require_subscriber(account.subscriber_id)

        if account.subscriber_id in self._aaa_accounts:
            raise DuplicateLabEntityError(
                f"AAA account for '{account.subscriber_id}' already exists."
            )

        self._aaa_accounts[account.subscriber_id] = account

    def get_aaa_account(self, subscriber_id: str) -> AAAAccount:
        """Return the AAA account associated with a subscriber."""

        try:
            return self._aaa_accounts[subscriber_id]
        except KeyError as exc:
            raise LabEntityNotFoundError(
                f"AAA account for '{subscriber_id}' was not found."
            ) from exc

    def set_session(self, session: Session) -> None:
        """Set the current synthetic session state for a subscriber."""

        self._require_subscriber(session.subscriber_id)
        self._sessions[session.subscriber_id] = session

    def get_session(self, subscriber_id: str) -> Session:
        """Return the current synthetic session state."""

        try:
            return self._sessions[subscriber_id]
        except KeyError as exc:
            raise LabEntityNotFoundError(f"Session for '{subscriber_id}' was not found.") from exc

    def add_radius_event(self, event: RadiusEvent) -> None:
        """Append a unique synthetic RADIUS event."""

        self._require_subscriber(event.subscriber_id)

        if event.event_id in self._radius_events:
            raise DuplicateLabEntityError(f"RADIUS event '{event.event_id}' already exists.")

        self._radius_events[event.event_id] = event

    def list_radius_events(
        self,
        subscriber_id: str,
    ) -> tuple[RadiusEvent, ...]:
        """Return RADIUS events for a subscriber in chronological order."""

        self._require_subscriber(subscriber_id)

        events = (
            event for event in self._radius_events.values() if event.subscriber_id == subscriber_id
        )

        return tuple(sorted(events, key=lambda event: event.timestamp))

    def list_radius_failures(
        self,
        subscriber_id: str,
    ) -> tuple[RadiusEvent, ...]:
        """Return only failed RADIUS events for a subscriber."""

        return tuple(
            event
            for event in self.list_radius_events(subscriber_id)
            if event.outcome.value == "failed"
        )

    def _require_subscriber(self, subscriber_id: str) -> None:
        """Require an existing subscriber."""

        if subscriber_id not in self._subscribers:
            raise LabEntityNotFoundError(f"Subscriber '{subscriber_id}' was not found.")
