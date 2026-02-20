"""Tests for game flow: GameFactory, GameStateMachine, win conditions, turn rules."""

from __future__ import annotations

import random

import pytest

from bang_game_engine.cards.card import Card
from bang_game_engine.cards.card_color import CardColor
from bang_game_engine.cards.card_face import CardFace
from bang_game_engine.cards.rank import Rank
from bang_game_engine.cards.suit import Suit
from bang_game_engine.effects.events import DrawCheckPerformed
from bang_game_engine.game.commands import (
    DiscardCardCommand,
    EndPhaseCommand,
    PlayCardCommand,
    RespondToEffectCommand,
)
from bang_game_engine.game.events import (
    CardPlayed,
    GameEnded,
    GameStarted,
    PhaseChanged,
    TurnEnded,
    TurnStarted,
)
from bang_game_engine.game.game_factory import GameFactory
from bang_game_engine.game.phase import Phase
from bang_game_engine.game.state_machine import GameStateMachine
from bang_game_engine.game.win_condition import GameResult, WinConditionEvaluator
from bang_game_engine.players.character import Character
from bang_game_engine.players.events import PlayerDamaged, PlayerEliminated
from bang_game_engine.players.player import Player
from bang_game_engine.players.role import Role
from bang_game_engine.players.seating import Seating
from bang_game_engine.shared.errors import (
    CardNotPlayableError,
    DomainError,
    GameOverError,
    InvalidActionError,
    NotYourTurnError,
    TargetOutOfRangeError,
)
from bang_game_engine.shared.identifiers import new_card_id, new_player_id


def _make_card(
    card_type: str = "bang",
    suit: Suit = Suit.HEARTS,
    rank: Rank = Rank.ACE,
    color: CardColor = CardColor.BROWN,
) -> Card:
    return Card(
        id=new_card_id(),
        card_type=card_type,
        face=CardFace(suit=suit, rank=rank),
        color=color,
    )


def _make_character(name: str = "Test", base_hp: int = 4) -> Character:
    return Character(character_type=name.lower(), name=name, base_hp=base_hp)


class TestGameFactory:
    def test_create_4_player_game(self):
        factory = GameFactory()
        machine = factory.create_game(player_count=4, rng=random.Random(42))
        assert len(machine.game_state.players) == 4

    def test_create_7_player_game(self):
        factory = GameFactory()
        machine = factory.create_game(player_count=7, rng=random.Random(42))
        assert len(machine.game_state.players) == 7

    def test_invalid_player_count(self):
        factory = GameFactory()
        with pytest.raises(DomainError, match="No role distribution"):
            factory.create_game(player_count=3)

    def test_start_game_emits_events(self):
        factory = GameFactory()
        machine = factory.create_game(player_count=4, rng=random.Random(42))
        events = machine.start_game()
        assert any(isinstance(e, GameStarted) for e in events)
        assert any(isinstance(e, TurnStarted) for e in events)

    def test_sheriff_has_extra_hp(self):
        factory = GameFactory()
        machine = factory.create_game(player_count=4, rng=random.Random(42))
        for player in machine.game_state.players.values():
            if player.role == Role.SHERIFF:
                assert player.max_hp == player.character.base_hp + 1

    def test_deterministic_with_seed(self):
        factory = GameFactory()
        m1 = factory.create_game(player_count=4, rng=random.Random(42))
        m2 = factory.create_game(player_count=4, rng=random.Random(42))
        # Same seed should give same roles
        roles1 = sorted(p.role.value for p in m1.game_state.players.values())
        roles2 = sorted(p.role.value for p in m2.game_state.players.values())
        assert roles1 == roles2

    def test_create_game_with_setup(self):
        factory = GameFactory()
        roles = [Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE]
        characters = [_make_character() for _ in range(4)]
        machine = factory.create_game_with_setup(roles=roles, characters=characters)
        assert len(machine.game_state.players) == 4
        role_set = {p.role for p in machine.game_state.players.values()}
        assert role_set == {Role.SHERIFF, Role.OUTLAW, Role.RENEGADE}


class TestGameStateMachine:
    def _setup_game(self, seed: int = 42) -> GameStateMachine:
        factory = GameFactory()
        machine = factory.create_game(player_count=4, rng=random.Random(seed))
        machine.start_game()
        return machine

    def test_game_starts_in_play_phase(self):
        machine = self._setup_game()
        assert machine.current_phase == Phase.PLAY_PHASE

    def test_active_player_is_sheriff(self):
        machine = self._setup_game()
        active_pid = machine.active_player_id
        player = machine.game_state.get_player(active_pid)
        assert player.role == Role.SHERIFF

    def test_sheriff_dealt_cards_equal_to_hp(self):
        machine = self._setup_game()
        active_pid = machine.active_player_id
        player = machine.game_state.get_player(active_pid)
        # Sheriff draws initial cards = max_hp, then draws 2 more for draw phase
        # So hand should be max_hp + 2
        assert player.hand_size == player.max_hp + 2

    def test_not_your_turn_raises(self):
        machine = self._setup_game()
        active_pid = machine.active_player_id
        # Find a non-active player
        other_pid = None
        for pid in machine.game_state.players:
            if pid != active_pid:
                other_pid = pid
                break
        with pytest.raises(NotYourTurnError):
            machine.handle_command(
                EndPhaseCommand(player_id=other_pid)
            )

    def test_end_phase_transitions(self):
        machine = self._setup_game()
        pid = machine.active_player_id
        # End play phase -> discard phase
        events = machine.handle_command(EndPhaseCommand(player_id=pid))
        # Should auto-end turn if within hand limit
        # (player has max_hp + 2 cards, hand limit = max_hp)
        # So it goes to discard phase first (no auto-end)
        # Actually depends on hand_size vs hand_limit
        player = machine.game_state.get_player(pid)
        # After the end phase, if hand > limit, we're in discard phase
        # If hand <= limit, turn ended automatically
        if player.hand_size > player.hand_limit:
            assert machine.current_phase in (Phase.DISCARD_PHASE, Phase.PLAY_PHASE)
        else:
            # New turn started
            assert machine.current_phase == Phase.PLAY_PHASE

    def test_play_bang_card(self):
        machine = self._setup_game()
        pid = machine.active_player_id
        player = machine.game_state.get_player(pid)

        # Find a bang card in hand
        bang_cards = player.find_cards_in_hand_by_type("bang")
        if not bang_cards:
            pytest.skip("No bang cards in hand for this seed")

        # Find a valid target (adjacent player)
        next_pid = machine.game_state.seating.next_alive_after(pid)

        events = machine.handle_command(
            PlayCardCommand(
                player_id=pid,
                card_id=bang_cards[0].id,
                target_player_id=next_pid,
            )
        )
        assert any(isinstance(e, CardPlayed) for e in events)
        # Should be awaiting response (Missed!)
        assert machine.current_phase == Phase.AWAITING_RESPONSE

    def test_respond_with_missed(self):
        machine = self._setup_game()
        pid = machine.active_player_id
        player = machine.game_state.get_player(pid)

        bang_cards = player.find_cards_in_hand_by_type("bang")
        if not bang_cards:
            pytest.skip("No bang cards in hand for this seed")

        next_pid = machine.game_state.seating.next_alive_after(pid)
        machine.handle_command(
            PlayCardCommand(
                player_id=pid,
                card_id=bang_cards[0].id,
                target_player_id=next_pid,
            )
        )

        target = machine.game_state.get_player(next_pid)
        missed_cards = target.find_cards_in_hand_by_type("missed")
        if missed_cards:
            # Respond with Missed!
            events = machine.handle_command(
                RespondToEffectCommand(
                    player_id=next_pid,
                    card_id=missed_cards[0].id,
                )
            )
            # Should return to play phase
            assert machine.current_phase == Phase.PLAY_PHASE
            # Target should not have taken damage (still at max HP)
            assert target.hp == target.max_hp

    def test_respond_pass_takes_damage(self):
        machine = self._setup_game()
        pid = machine.active_player_id
        player = machine.game_state.get_player(pid)

        bang_cards = player.find_cards_in_hand_by_type("bang")
        if not bang_cards:
            pytest.skip("No bang cards in hand for this seed")

        next_pid = machine.game_state.seating.next_alive_after(pid)
        target_hp_before = machine.game_state.get_player(next_pid).hp

        machine.handle_command(
            PlayCardCommand(
                player_id=pid,
                card_id=bang_cards[0].id,
                target_player_id=next_pid,
            )
        )

        # Pass (no card)
        events = machine.handle_command(
            RespondToEffectCommand(
                player_id=next_pid,
                card_id=None,
            )
        )
        target = machine.game_state.get_player(next_pid)
        assert target.hp == target_hp_before - 1

    def test_only_one_bang_per_turn(self):
        machine = self._setup_game()
        pid = machine.active_player_id
        player = machine.game_state.get_player(pid)

        bang_cards = player.find_cards_in_hand_by_type("bang")
        if len(bang_cards) < 2:
            pytest.skip("Need 2+ bang cards for this test")

        next_pid = machine.game_state.seating.next_alive_after(pid)

        # Play first bang
        machine.handle_command(
            PlayCardCommand(
                player_id=pid,
                card_id=bang_cards[0].id,
                target_player_id=next_pid,
            )
        )
        # Resolve (pass)
        machine.handle_command(
            RespondToEffectCommand(player_id=next_pid, card_id=None)
        )

        # Try second bang - should fail
        with pytest.raises(CardNotPlayableError, match="Already played a Bang"):
            machine.handle_command(
                PlayCardCommand(
                    player_id=pid,
                    card_id=bang_cards[1].id,
                    target_player_id=next_pid,
                )
            )


class TestWinConditions:
    def _make_players(self, roles: list[Role]) -> dict[PlayerId, Player]:
        players = {}
        for role in roles:
            pid = new_player_id()
            players[pid] = Player(
                player_id=pid,
                role=role,
                character=_make_character(base_hp=4),
            )
        return players

    def test_outlaws_win_when_sheriff_dies(self):
        players = self._make_players(
            [Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE]
        )
        pids = list(players.keys())
        seating = Seating(pids)

        # Kill sheriff
        players[pids[0]].eliminate()
        seating.mark_eliminated(pids[0])

        evaluator = WinConditionEvaluator()
        result = evaluator.evaluate(players, seating)
        assert result is not None
        assert Role.OUTLAW in result.winners

    def test_renegade_wins_alone(self):
        players = self._make_players(
            [Role.SHERIFF, Role.OUTLAW, Role.RENEGADE]
        )
        pids = list(players.keys())
        seating = Seating(pids)

        # Kill sheriff and outlaw, only renegade alive
        players[pids[0]].eliminate()
        seating.mark_eliminated(pids[0])
        players[pids[1]].eliminate()
        seating.mark_eliminated(pids[1])

        evaluator = WinConditionEvaluator()
        result = evaluator.evaluate(players, seating)
        assert result is not None
        assert Role.RENEGADE in result.winners

    def test_sheriff_wins_when_all_baddies_dead(self):
        players = self._make_players(
            [Role.SHERIFF, Role.DEPUTY, Role.OUTLAW, Role.RENEGADE]
        )
        pids = list(players.keys())
        seating = Seating(pids)

        # Kill outlaw and renegade
        players[pids[2]].eliminate()
        seating.mark_eliminated(pids[2])
        players[pids[3]].eliminate()
        seating.mark_eliminated(pids[3])

        evaluator = WinConditionEvaluator()
        result = evaluator.evaluate(players, seating)
        assert result is not None
        assert Role.SHERIFF in result.winners
        assert Role.DEPUTY in result.winners

    def test_game_continues_if_no_winner(self):
        players = self._make_players(
            [Role.SHERIFF, Role.DEPUTY, Role.OUTLAW, Role.RENEGADE]
        )
        pids = list(players.keys())
        seating = Seating(pids)

        # Kill only one outlaw -- game should continue
        players[pids[2]].eliminate()
        seating.mark_eliminated(pids[2])

        evaluator = WinConditionEvaluator()
        result = evaluator.evaluate(players, seating)
        assert result is None  # Game continues
