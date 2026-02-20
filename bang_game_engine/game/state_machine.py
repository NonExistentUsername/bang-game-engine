from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bang_game_engine.cards.card import Card
from bang_game_engine.cards.card_color import CardColor
from bang_game_engine.effects.draw_check import (
    BarrelCondition,
    DrawCheckService,
    DynamiteCondition,
    JailCondition,
)
from bang_game_engine.effects.effect import (
    EffectContext,
    EffectOutcome,
    EffectStackEntry,
    EffectState,
    ResponseWindow,
)
from bang_game_engine.effects.events import (
    DrawCheckPerformed,
    DynamiteExploded,
    DynamitePassed,
    JailEscaped,
    JailKept,
)
from bang_game_engine.game.commands import (
    DiscardCardCommand,
    EndPhaseCommand,
    GeneralStorePickCommand,
    PlayBeerWhenDyingCommand,
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
from bang_game_engine.game.game_state import GameState
from bang_game_engine.game.phase import Phase
from bang_game_engine.game.turn import TurnState
from bang_game_engine.players.events import PlayerAtZeroHP, PlayerDamaged, PlayerEliminated
from bang_game_engine.players.player import WEAPON_TYPES
from bang_game_engine.players.role import Role
from bang_game_engine.shared.commands import Command
from bang_game_engine.shared.errors import (
    CardNotPlayableError,
    DomainError,
    GameOverError,
    InvalidActionError,
    NotYourTurnError,
    TargetOutOfRangeError,
)
from bang_game_engine.shared.events import DomainEvent
from bang_game_engine.shared.types import PlayerId


class GameStateMachine:
    """
    Central orchestrator for game flow.

    Handles all commands, manages phase transitions,
    integrates the effect stack with turn flow,
    and coordinates elimination/win checking.
    """

    def __init__(self, game_state: GameState):
        self._state = game_state
        self._draw_check = DrawCheckService()
        self._all_events: list[DomainEvent] = []

    @property
    def game_state(self) -> GameState:
        return self._state

    @property
    def current_phase(self) -> Phase:
        if self._state.current_turn is None:
            return Phase.NOT_STARTED
        return self._state.current_turn.current_phase

    @property
    def active_player_id(self) -> PlayerId | None:
        if self._state.current_turn is None:
            return None
        return self._state.current_turn.active_player_id

    @property
    def all_events(self) -> list[DomainEvent]:
        return list(self._all_events)

    def _emit(self, event: DomainEvent) -> None:
        self._all_events.append(event)

    def _emit_all(self, events: list[DomainEvent]) -> None:
        self._all_events.extend(events)

    # --- Game Lifecycle ---

    def start_game(self) -> list[DomainEvent]:
        """Initialize the game and start the first turn."""
        events: list[DomainEvent] = []

        # Find sheriff (first player)
        sheriff_id = None
        for pid, player in self._state.players.items():
            if player.role == Role.SHERIFF:
                sheriff_id = pid
                break

        if sheriff_id is None:
            raise DomainError("No sheriff found among players")

        # Deal initial cards: each player gets cards = their HP
        for pid in self._state.seating.alive_players_in_order():
            player = self._state.get_player(pid)
            for _ in range(player.max_hp):
                card = self._state.deck.draw()
                player.add_to_hand(card)

        event = GameStarted(
            game_id=self._state.game_id,
            player_count=self._state.alive_count,
        )
        self._emit(event)
        events.append(event)

        # Start first turn with sheriff
        turn_events = self._start_turn(sheriff_id)
        events.extend(turn_events)

        return events

    def handle_command(self, command: Command) -> list[DomainEvent]:
        """Main entry point for all player actions."""
        if self._state.is_over:
            raise GameOverError("Game is already over")

        events: list[DomainEvent] = []

        if isinstance(command, PlayCardCommand):
            events = self._handle_play_card(command)
        elif isinstance(command, RespondToEffectCommand):
            events = self._handle_respond_to_effect(command)
        elif isinstance(command, EndPhaseCommand):
            events = self._handle_end_phase(command)
        elif isinstance(command, DiscardCardCommand):
            events = self._handle_discard_card(command)
        elif isinstance(command, GeneralStorePickCommand):
            events = self._handle_general_store_pick(command)
        elif isinstance(command, PlayBeerWhenDyingCommand):
            events = self._handle_beer_when_dying(command)
        else:
            raise InvalidActionError(f"Unknown command type: {type(command)}")

        # Collect internal events from state
        internal_events = self._state.collect_events()
        self._emit_all(internal_events)
        events.extend(internal_events)

        return events

    # --- Turn Management ---

    def _start_turn(self, player_id: PlayerId) -> list[DomainEvent]:
        """Start a new turn for the given player."""
        events: list[DomainEvent] = []

        player = self._state.get_player(player_id)
        turn_number = (
            self._state.current_turn.turn_number + 1
            if self._state.current_turn
            else 1
        )

        # Check for unlimited bangs (Volcanic equipped or Willy the Kid)
        has_unlimited = player.has_card_type_on_table(
            "volcanic"
        ) or player.character.has_ability("willy_the_kid")

        self._state.current_turn = TurnState(
            turn_number=turn_number,
            active_player_id=player_id,
            current_phase=Phase.DYNAMITE_CHECK,
            has_unlimited_bangs=has_unlimited,
        )

        event = TurnStarted(
            turn_number=turn_number, active_player_id=player_id
        )
        self._emit(event)
        events.append(event)

        # Run pre-turn checks
        check_events = self._run_pre_turn_checks(player_id)
        events.extend(check_events)

        return events

    def _run_pre_turn_checks(self, player_id: PlayerId) -> list[DomainEvent]:
        """Run Dynamite and Jail checks."""
        events: list[DomainEvent] = []
        player = self._state.get_player(player_id)
        turn = self._state.current_turn
        assert turn is not None

        # 1. Dynamite check
        if player.has_card_type_on_table("dynamite"):
            dynamite_card = None
            for c in player.table_cards:
                if c.card_type == "dynamite":
                    dynamite_card = c
                    break

            if dynamite_card:
                result = self._draw_check.perform_check(
                    self._state.deck, DynamiteCondition()
                )
                check_event = DrawCheckPerformed(
                    player_id=player_id,
                    check_type="dynamite",
                    card_face=result.card_drawn.face,
                    passed=result.passed,
                )
                self._emit(check_event)
                events.append(check_event)

                if result.passed:
                    # Explodes! 3 damage
                    player.remove_from_table(dynamite_card.id)
                    self._state.deck.discard(dynamite_card)
                    dmg_events = player.take_damage(3)
                    self._emit_all(dmg_events)
                    events.extend(dmg_events)

                    explode_event = DynamiteExploded(
                        player_id=player_id, damage=3
                    )
                    self._emit(explode_event)
                    events.append(explode_event)

                    # Check for death
                    death_events = self._check_elimination(player_id, None)
                    events.extend(death_events)

                    if not player.is_alive:
                        return events
                else:
                    # Pass dynamite to next player
                    player.remove_from_table(dynamite_card.id)
                    next_pid = self._state.seating.next_alive_after(player_id)
                    next_player = self._state.get_player(next_pid)
                    next_player.play_to_table(dynamite_card)

                    pass_event = DynamitePassed(
                        from_player_id=player_id, to_player_id=next_pid
                    )
                    self._emit(pass_event)
                    events.append(pass_event)

        # 2. Jail check
        if player.has_card_type_on_table("jail"):
            jail_card = None
            for c in player.table_cards:
                if c.card_type == "jail":
                    jail_card = c
                    break

            if jail_card:
                result = self._draw_check.perform_check(
                    self._state.deck, JailCondition()
                )
                check_event = DrawCheckPerformed(
                    player_id=player_id,
                    check_type="jail",
                    card_face=result.card_drawn.face,
                    passed=result.passed,
                )
                self._emit(check_event)
                events.append(check_event)

                # Remove jail card regardless
                player.remove_from_table(jail_card.id)
                self._state.deck.discard(jail_card)

                if result.passed:
                    # Escaped jail
                    escape_event = JailEscaped(player_id=player_id)
                    self._emit(escape_event)
                    events.append(escape_event)
                else:
                    # Jailed - skip to discard phase
                    kept_event = JailKept(player_id=player_id)
                    self._emit(kept_event)
                    events.append(kept_event)

                    turn.skip_turn = True
                    turn.current_phase = Phase.DISCARD_PHASE
                    return events

        # Move to draw phase
        turn.current_phase = Phase.DRAW_PHASE
        phase_event = PhaseChanged(
            player_id=player_id,
            from_phase=Phase.DYNAMITE_CHECK,
            to_phase=Phase.DRAW_PHASE,
        )
        self._emit(phase_event)
        events.append(phase_event)

        # Auto-draw 2 cards (default draw phase)
        draw_events = self._do_default_draw(player_id)
        events.extend(draw_events)

        return events

    def _do_default_draw(self, player_id: PlayerId) -> list[DomainEvent]:
        """Default draw phase: draw 2 cards."""
        events: list[DomainEvent] = []
        player = self._state.get_player(player_id)
        turn = self._state.current_turn
        assert turn is not None

        for _ in range(2):
            card = self._state.deck.draw()
            player.add_to_hand(card)
            turn.cards_drawn += 1

        # Move to play phase
        turn.current_phase = Phase.PLAY_PHASE
        phase_event = PhaseChanged(
            player_id=player_id,
            from_phase=Phase.DRAW_PHASE,
            to_phase=Phase.PLAY_PHASE,
        )
        self._emit(phase_event)
        events.append(phase_event)

        return events

    # --- Card Playing ---

    def _handle_play_card(self, command: PlayCardCommand) -> list[DomainEvent]:
        turn = self._state.current_turn
        if turn is None:
            raise DomainError("No turn in progress")

        if command.player_id != turn.active_player_id:
            raise NotYourTurnError("It is not your turn")

        if turn.current_phase != Phase.PLAY_PHASE:
            raise InvalidActionError(
                f"Cannot play cards during {turn.current_phase.value}"
            )

        player = self._state.get_player(command.player_id)
        card = player.get_card_from_hand(command.card_id)
        if card is None:
            raise InvalidActionError("Card not in hand")

        # Check turn rules
        allowed, reason = self._state.turn_rule_engine.can_play_card(
            card, player, turn, self._state
        )
        if not allowed:
            raise CardNotPlayableError(reason)

        # Range check for targeted cards
        if command.target_player_id is not None:
            self._validate_target(player, command.target_player_id, card)

        # Remove card from hand
        player.remove_from_hand(command.card_id)

        events: list[DomainEvent] = []
        played_event = CardPlayed(
            player_id=command.player_id,
            card_type=card.card_type,
            target_player_id=command.target_player_id,
        )
        self._emit(played_event)
        events.append(played_event)

        # Track bang count
        if card.card_type == "bang":
            turn.bangs_played += 1

        # Handle card based on color
        if card.color == CardColor.BLUE:
            # Persistent card -> play to table
            displaced = player.play_to_table(card)
            if displaced:
                self._state.deck.discard(displaced)
            # Check if weapon grants unlimited bangs
            if card.card_type == "volcanic":
                turn.has_unlimited_bangs = True
        elif card.color == CardColor.GREEN:
            # Green card -> play to table with turn marker
            card.turn_played = turn.turn_number
            player.play_to_table(card)
        else:
            # Brown card -> resolve effect, then discard
            self._state.deck.discard(card)

            if self._state.effect_registry.has_handler(card.card_type):
                effect_events = self._resolve_effect(
                    card, command.player_id, command.target_player_id
                )
                events.extend(effect_events)

        return events

    def _validate_target(
        self,
        source_player: Any,
        target_player_id: PlayerId,
        card: Card,
    ) -> None:
        """Validate target is valid for the given card."""
        if target_player_id == source_player.id:
            raise InvalidActionError("Cannot target yourself with this card")

        target = self._state.get_player(target_player_id)
        if not target.is_alive:
            raise InvalidActionError("Cannot target an eliminated player")

        # Range check for Bang!
        if card.card_type == "bang":
            if not self._state.distance_service.is_in_weapon_range(
                self._state.seating, source_player, target
            ):
                raise TargetOutOfRangeError("Target is out of weapon range")

        # Range check for Panic! (distance 1)
        if card.card_type == "panic":
            if not self._state.distance_service.is_in_range(
                self._state.seating, source_player, target, 1
            ):
                raise TargetOutOfRangeError(
                    "Panic! requires target at distance 1"
                )

        # Jail cannot target Sheriff
        if card.card_type == "jail" and target.role == Role.SHERIFF:
            raise InvalidActionError("Cannot put the Sheriff in Jail")

    # --- Effect Resolution ---

    def _resolve_effect(
        self,
        card: Card,
        source_player_id: PlayerId,
        target_player_id: PlayerId | None,
    ) -> list[DomainEvent]:
        """Start resolving a card effect."""
        events: list[DomainEvent] = []

        handler = self._state.effect_registry.get_handler(card.card_type)
        context = EffectContext(
            source_player_id=source_player_id,
            card=card,
            target_player_id=target_player_id,
        )

        # Validate
        valid, reason = handler.validate(context, self._state)
        if not valid:
            raise CardNotPlayableError(reason)

        # Begin effect
        outcome = handler.begin(context, self._state)
        effect_events = self._process_outcome(outcome, handler, context)
        events.extend(effect_events)

        return events

    def _process_outcome(
        self,
        outcome: EffectOutcome,
        handler: Any,
        context: EffectContext,
    ) -> list[DomainEvent]:
        """Process an effect outcome."""
        events = list(outcome.events)
        self._emit_all(outcome.events)

        if outcome.state == EffectState.AWAITING_RESPONSE:
            # Push onto effect stack
            entry = EffectStackEntry(
                handler=handler,
                context=context,
                state=EffectState.AWAITING_RESPONSE,
                response_window=outcome.response_window,
            )
            if outcome.remaining_targets:
                entry.remaining_targets = list(outcome.remaining_targets)
                if outcome.response_window:
                    entry.current_target_id = (
                        outcome.response_window.responding_player_id
                    )
            self._state.effect_stack.push(entry)

            # Switch to awaiting response
            assert self._state.current_turn is not None
            self._state.current_turn.current_phase = Phase.AWAITING_RESPONSE

        elif outcome.state == EffectState.COMPLETE:
            # Check for deaths
            for event in outcome.events:
                if isinstance(event, PlayerAtZeroHP):
                    death_events = self._check_elimination(
                        event.player_id, context.source_player_id
                    )
                    events.extend(death_events)

        return events

    def _handle_respond_to_effect(
        self, command: RespondToEffectCommand
    ) -> list[DomainEvent]:
        """Handle a player responding to an effect."""
        if self._state.effect_stack.is_empty:
            raise InvalidActionError("No effect to respond to")

        entry = self._state.effect_stack.peek()
        assert entry is not None

        if entry.response_window is None:
            raise InvalidActionError("No response expected")

        if command.player_id != entry.response_window.responding_player_id:
            raise NotYourTurnError("It is not your turn to respond")

        # If player is playing a card to respond, validate and remove from hand
        if command.card_id is not None:
            player = self._state.get_player(command.player_id)
            card = player.get_card_from_hand(command.card_id)
            if card is None:
                raise InvalidActionError("Card not in hand")
            player.remove_from_hand(command.card_id)
            self._state.deck.discard(card)

        # Handle the response
        outcome = entry.handler.handle_response(
            entry.context,
            self._state,
            command.card_id,
            command.player_id,
        )

        events = list(outcome.events)
        self._emit_all(outcome.events)

        if outcome.state == EffectState.COMPLETE:
            self._state.effect_stack.pop()

            # Check for deaths
            for event in outcome.events:
                if isinstance(event, PlayerAtZeroHP):
                    death_events = self._check_elimination(
                        event.player_id, entry.context.source_player_id
                    )
                    events.extend(death_events)

            # If stack is empty, return to play phase
            if self._state.effect_stack.is_empty:
                assert self._state.current_turn is not None
                self._state.current_turn.current_phase = Phase.PLAY_PHASE

        elif outcome.state == EffectState.AWAITING_RESPONSE:
            # Update entry
            entry.response_window = outcome.response_window
            entry.state = EffectState.AWAITING_RESPONSE
            if outcome.remaining_targets is not None:
                entry.remaining_targets = list(outcome.remaining_targets)
            if outcome.response_window:
                entry.current_target_id = (
                    outcome.response_window.responding_player_id
                )

        return events

    # --- Phase Transitions ---

    def _handle_end_phase(self, command: EndPhaseCommand) -> list[DomainEvent]:
        turn = self._state.current_turn
        if turn is None:
            raise DomainError("No turn in progress")

        if command.player_id != turn.active_player_id:
            raise NotYourTurnError("It is not your turn")

        events: list[DomainEvent] = []

        if turn.current_phase == Phase.PLAY_PHASE:
            # Move to discard phase
            turn.current_phase = Phase.DISCARD_PHASE
            phase_event = PhaseChanged(
                player_id=command.player_id,
                from_phase=Phase.PLAY_PHASE,
                to_phase=Phase.DISCARD_PHASE,
            )
            self._emit(phase_event)
            events.append(phase_event)

            # Auto-end if hand is within limit
            player = self._state.get_player(command.player_id)
            if player.hand_size <= player.hand_limit:
                end_events = self._end_turn()
                events.extend(end_events)

        elif turn.current_phase == Phase.DISCARD_PHASE:
            # Check hand limit
            player = self._state.get_player(command.player_id)
            if player.hand_size > player.hand_limit:
                raise InvalidActionError(
                    f"Must discard to {player.hand_limit} cards first"
                )
            end_events = self._end_turn()
            events.extend(end_events)

        else:
            raise InvalidActionError(
                f"Cannot end phase during {turn.current_phase.value}"
            )

        return events

    def _handle_discard_card(
        self, command: DiscardCardCommand
    ) -> list[DomainEvent]:
        turn = self._state.current_turn
        if turn is None:
            raise DomainError("No turn in progress")

        if command.player_id != turn.active_player_id:
            raise NotYourTurnError("It is not your turn")

        if turn.current_phase != Phase.DISCARD_PHASE:
            raise InvalidActionError("Can only discard during discard phase")

        player = self._state.get_player(command.player_id)
        card = player.remove_from_hand(command.card_id)
        self._state.deck.discard(card)

        events: list[DomainEvent] = []

        # Auto-end turn if at hand limit
        if player.hand_size <= player.hand_limit:
            end_events = self._end_turn()
            events.extend(end_events)

        return events

    def _handle_general_store_pick(
        self, command: GeneralStorePickCommand
    ) -> list[DomainEvent]:
        turn = self._state.current_turn
        if turn is None:
            raise DomainError("No turn in progress")

        if turn.current_phase != Phase.GENERAL_STORE_PICK:
            raise InvalidActionError("Not in General Store pick phase")

        if not turn.general_store_pickers:
            raise InvalidActionError("No pickers remaining")

        current_picker = turn.general_store_pickers[0]
        if command.player_id != current_picker:
            raise NotYourTurnError("It is not your turn to pick")

        # Find and remove card from store
        picked_card = None
        for i, card in enumerate(turn.general_store_cards):
            if card.id == command.card_id:
                picked_card = turn.general_store_cards.pop(i)
                break

        if picked_card is None:
            raise InvalidActionError("Card not available in General Store")

        # Add to player's hand
        player = self._state.get_player(command.player_id)
        player.add_to_hand(picked_card)

        # Advance to next picker
        turn.general_store_pickers.pop(0)

        events: list[DomainEvent] = []

        if not turn.general_store_pickers:
            # General Store resolved, return to play phase
            turn.current_phase = Phase.PLAY_PHASE
            turn.general_store_cards.clear()

        return events

    def _handle_beer_when_dying(
        self, command: PlayBeerWhenDyingCommand
    ) -> list[DomainEvent]:
        """Handle out-of-turn Beer when a player is dying."""
        player = self._state.get_player(command.player_id)

        if player.hp > 0:
            raise InvalidActionError("You are not dying")

        if self._state.alive_count <= 2:
            raise InvalidActionError("Beer has no effect with 2 players")

        card = player.get_card_from_hand(command.card_id)
        if card is None or card.card_type != "beer":
            raise InvalidActionError("Must play a Beer card")

        player.remove_from_hand(command.card_id)
        self._state.deck.discard(card)
        heal_events = player.heal(1)

        events: list[DomainEvent] = []
        self._emit_all(heal_events)
        events.extend(heal_events)
        return events

    # --- Turn End ---

    def _end_turn(self) -> list[DomainEvent]:
        """End the current turn and start the next."""
        turn = self._state.current_turn
        assert turn is not None

        events: list[DomainEvent] = []

        end_event = TurnEnded(
            turn_number=turn.turn_number,
            active_player_id=turn.active_player_id,
        )
        self._emit(end_event)
        events.append(end_event)

        # Determine next player
        next_pid = self._state.seating.next_alive_after(
            turn.active_player_id
        )

        # Start next turn
        next_events = self._start_turn(next_pid)
        events.extend(next_events)

        return events

    # --- Elimination ---

    def _check_elimination(
        self,
        dying_player_id: PlayerId,
        killer_player_id: PlayerId | None,
    ) -> list[DomainEvent]:
        """Check if player at 0 HP should be eliminated (no Beer saving here for now)."""
        events: list[DomainEvent] = []
        player = self._state.get_player(dying_player_id)

        if player.hp > 0 or not player.is_alive:
            return events

        # Eliminate the player
        elim_events = player.eliminate()
        self._emit_all(elim_events)
        events.extend(elim_events)

        # Update seating
        self._state.seating.mark_eliminated(dying_player_id)

        # Bounty: killer killed an Outlaw -> draw 3
        if player.role == Role.OUTLAW and killer_player_id is not None:
            killer = self._state.get_player(killer_player_id)
            if killer.is_alive:
                for _ in range(3):
                    card = self._state.deck.draw()
                    killer.add_to_hand(card)

        # Penalty: Sheriff killed a Deputy -> discard all
        if player.role == Role.DEPUTY and killer_player_id is not None:
            killer = self._state.get_player(killer_player_id)
            if killer.role == Role.SHERIFF:
                discarded = killer.discard_all()
                for card in discarded:
                    self._state.deck.discard(card)

        # Discard dead player's cards
        dead_cards = player.discard_all()
        for card in dead_cards:
            self._state.deck.discard(card)

        # Check win conditions
        result = self._state.win_evaluator.evaluate(
            self._state.players, self._state.seating
        )
        if result is not None:
            self._state.set_game_result(result)
            if self._state.current_turn:
                self._state.current_turn.current_phase = Phase.GAME_OVER
            game_end = GameEnded(
                game_id=self._state.game_id,
                winners=result.winners,
                winning_player_ids=result.winning_player_ids,
            )
            self._emit(game_end)
            events.append(game_end)

        return events
