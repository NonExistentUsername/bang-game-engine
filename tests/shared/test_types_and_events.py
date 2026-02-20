"""Tests for shared kernel: types, identifiers, errors, events."""

from __future__ import annotations

import pytest
from uuid import UUID

from bang_game_engine.shared.identifiers import new_card_id, new_game_id, new_player_id
from bang_game_engine.shared.events import DomainEvent, EventCollector
from bang_game_engine.shared.errors import (
    CardNotPlayableError,
    DomainError,
    GameNotStartedError,
    GameOverError,
    InvalidActionError,
    NotYourTurnError,
    TargetOutOfRangeError,
)


class TestIdentifiers:
    def test_new_player_id_returns_uuid(self):
        pid = new_player_id()
        assert isinstance(pid, UUID)

    def test_new_card_id_returns_uuid(self):
        cid = new_card_id()
        assert isinstance(cid, UUID)

    def test_new_game_id_returns_uuid(self):
        gid = new_game_id()
        assert isinstance(gid, UUID)

    def test_ids_are_unique(self):
        ids = {new_player_id() for _ in range(100)}
        assert len(ids) == 100


class TestDomainEvent:
    def test_event_has_id_and_timestamp(self):
        event = DomainEvent()
        assert isinstance(event.event_id, UUID)
        assert event.occurred_at is not None

    def test_events_have_unique_ids(self):
        e1 = DomainEvent()
        e2 = DomainEvent()
        assert e1.event_id != e2.event_id


class TestEventCollector:
    def test_collect_empty(self):
        collector = EventCollector()
        assert collector.collect_events() == []

    def test_record_and_collect(self):
        collector = EventCollector()
        event = DomainEvent()
        collector._record_event(event)
        events = collector.collect_events()
        assert len(events) == 1
        assert events[0] is event

    def test_collect_clears_events(self):
        collector = EventCollector()
        collector._record_event(DomainEvent())
        collector.collect_events()
        assert collector.collect_events() == []


class TestErrors:
    def test_domain_error_hierarchy(self):
        assert issubclass(InvalidActionError, DomainError)
        assert issubclass(NotYourTurnError, DomainError)
        assert issubclass(TargetOutOfRangeError, DomainError)
        assert issubclass(CardNotPlayableError, DomainError)
        assert issubclass(GameOverError, DomainError)
        assert issubclass(GameNotStartedError, DomainError)

    def test_error_message(self):
        err = InvalidActionError("test message")
        assert str(err) == "test message"
