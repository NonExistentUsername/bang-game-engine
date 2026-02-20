from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Protocol
from uuid import UUID


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events."""

    event_id: UUID = field(default_factory=uuid.uuid4, kw_only=True)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc), kw_only=True
    )


class EventBus(Protocol):
    def publish(self, event: DomainEvent) -> None: ...

    def subscribe(
        self, event_type: type[DomainEvent], handler: Callable[[DomainEvent], Any]
    ) -> None: ...


class EventCollector:
    """Mixin for aggregates to collect domain events before publishing."""

    def __init__(self) -> None:
        self._pending_events: list[DomainEvent] = []

    def _record_event(self, event: DomainEvent) -> None:
        self._pending_events.append(event)

    def collect_events(self) -> list[DomainEvent]:
        events = list(self._pending_events)
        self._pending_events.clear()
        return events
