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
    BeerSavingAttempt,
    DrawCheckPerformed,
    DynamiteExploded,
    DynamitePassed,
    JailEscaped,
    JailKept,
)
from bang_game_engine.game.commands import (
    DiscardCardCommand,
    DrawPhaseChoiceCommand,
    EndPhaseCommand,
    GeneralStorePickCommand,
    KitCarlsonChoiceCommand,
    PlayBeerWhenDyingCommand,
    PlayCardCommand,
    RespondToEffectCommand,
    SidKetchumHealCommand,
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
from bang_game_engine.players.ability import AbilityContext, AbilityTiming
from bang_game_engine.players.events import (
    AbilityActivated,
    PlayerAtZeroHP,
    PlayerDamaged,
    PlayerEliminated,
)
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


# Valid response card types for each response expectation
_RESPONSE_CARD_TYPES: dict[str, set[str]] = {
    "missed": {"missed"},
    "bang": {"bang"},
    "beer": {"beer"},
    "pass": set(),  # Pass means no card
}


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
        # Beer saving state: when a player hits 0 HP, we pause to let them play Beer
        self._dying_player_id: PlayerId | None = None
        self._dying_killer_id: PlayerId | None = None

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

    @property
    def is_awaiting_beer_save(self) -> bool:
        return self._dying_player_id is not None

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

        # Deal initial cards: each player gets cards = their max HP
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

        # If we're waiting for beer saving, only allow beer or pass
        if self._dying_player_id is not None:
            if isinstance(command, PlayBeerWhenDyingCommand):
                events = self._handle_beer_when_dying(command)
            else:
                raise InvalidActionError(
                    "A player is dying - only Beer can be played right now"
                )
        elif isinstance(command, PlayCardCommand):
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
        elif isinstance(command, DrawPhaseChoiceCommand):
            events = self._handle_draw_phase_choice(command)
        elif isinstance(command, KitCarlsonChoiceCommand):
            events = self._handle_kit_carlson_choice(command)
        elif isinstance(command, SidKetchumHealCommand):
            events = self._handle_sid_ketchum_heal(command)
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

                    # Bart Cassidy: draw card per damage taken
                    dmg_events = player.take_damage(3)
                    self._emit_all(dmg_events)
                    events.extend(dmg_events)

                    # Bart Cassidy draws cards
                    bart_events = self._trigger_on_take_damage(player_id, 3, None)
                    events.extend(bart_events)

                    explode_event = DynamiteExploded(
                        player_id=player_id, damage=3
                    )
                    self._emit(explode_event)
                    events.append(explode_event)

                    # Check for death (with beer saving)
                    death_events = self._check_elimination(player_id, None)
                    events.extend(death_events)

                    if not player.is_alive:
                        # Player died from dynamite - end their turn, move to next
                        if self._state.is_over:
                            return events
                        end_event = TurnEnded(
                            turn_number=turn.turn_number,
                            active_player_id=player_id,
                        )
                        self._emit(end_event)
                        events.append(end_event)
                        next_pid = self._state.seating.next_alive_after(
                            self._find_living_neighbor(player_id)
                        ) if not self._state.seating.is_alive(player_id) else self._state.seating.next_alive_after(player_id)
                        # Don't start next turn here; the caller (_start_turn) will handle it
                        # Actually we need to handle this: player dies during their own turn start
                        return events
                else:
                    # Pass dynamite to next alive player
                    player.remove_from_table(dynamite_card.id)
                    next_pid = self._state.seating.next_alive_after(player_id)
                    next_player = self._state.get_player(next_pid)
                    next_player.play_to_table(dynamite_card)

                    pass_event = DynamitePassed(
                        from_player_id=player_id, to_player_id=next_pid
                    )
                    self._emit(pass_event)
                    events.append(pass_event)

        # If player died from dynamite, don't continue
        if not player.is_alive:
            return events

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
                    # Jailed - skip to discard phase (skip draw and play)
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

    def _find_living_neighbor(self, dead_player_id: PlayerId) -> PlayerId:
        """Find an alive player to anchor next_alive_after when the given player is dead."""
        alive = self._state.seating.alive_players_in_order()
        if alive:
            return alive[0]
        raise DomainError("No alive players")

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

        # Suzy Lafayette: if hand was empty and now has cards, this is handled elsewhere
        # Black Jack: show 2nd card drawn, if red suit draw extra
        bj_events = self._trigger_black_jack_draw(player_id)
        events.extend(bj_events)

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

        # Calamity Janet: Bang! can be played as Missed! and vice versa
        # (handled in response validation, not during play)

        # Check turn rules
        allowed, reason = self._state.turn_rule_engine.can_play_card(
            card, player, turn, self._state
        )
        if not allowed:
            raise CardNotPlayableError(reason)

        # Range check for targeted cards
        if command.target_player_id is not None:
            self._validate_target(player, command.target_player_id, card)

        # Pre-validate effect handler BEFORE removing card from hand
        if card.color == CardColor.BROWN and self._state.effect_registry.has_handler(card.card_type):
            handler = self._state.effect_registry.get_handler(card.card_type)
            context = EffectContext(
                source_player_id=command.player_id,
                card=card,
                target_player_id=command.target_player_id,
            )
            valid, reason = handler.validate(context, self._state)
            if not valid:
                raise CardNotPlayableError(reason)

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
            # Jail targets another player's table
            if card.card_type == "jail" and command.target_player_id is not None:
                target_player = self._state.get_player(command.target_player_id)
                target_player.play_to_table(card)
            else:
                # Persistent card -> play to source's table
                displaced = player.play_to_table(card)
                if displaced:
                    self._state.deck.discard(displaced)
                # Volcanic grants unlimited bangs immediately
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

        # Suzy Lafayette: draw when hand becomes empty
        suzy_events = self._trigger_suzy_lafayette(command.player_id)
        events.extend(suzy_events)

        return events

    def _validate_target(
        self,
        source_player: Any,
        target_player_id: PlayerId,
        card: Card,
    ) -> None:
        """Validate target is valid for the given card."""
        # Cat Balou and Panic! can target yourself (e.g., to discard your own Dynamite)
        if target_player_id == source_player.id:
            if card.card_type not in ("cat_balou", "panic"):
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

        # For Bang!: do Barrel check first (before asking for Missed!)
        barrel_credit = 0
        if card.card_type == "bang" and target_player_id is not None:
            barrel_events = self._do_barrel_check(target_player_id, source_player_id)
            events.extend(barrel_events)
            barrel_saved = any(
                isinstance(e, DrawCheckPerformed) and e.check_type == "barrel" and e.passed
                for e in barrel_events
            )
            if barrel_saved:
                # Check if source needs more than 1 Missed! (Slab the Killer)
                source = self._state.get_player(source_player_id)
                missed_needed = 1
                for ability in source.character.get_abilities_for_timing(
                    AbilityTiming.ON_MISSED_REQUIRED
                ):
                    ctx = AbilityContext(player_id=source.id)
                    if ability.can_activate(ctx):
                        result = ability.activate(ctx)
                        if result.modified_value is not None:
                            missed_needed = result.modified_value
                if missed_needed <= 1:
                    return events  # Barrel fully negates regular Bang!
                barrel_credit = 1  # Barrel counts as 1 Missed! toward Slab requirement

        # Begin effect
        outcome = handler.begin(context, self._state)
        effect_events = self._process_outcome(outcome, handler, context)
        events.extend(effect_events)

        # Apply barrel credit for Slab the Killer (barrel counts as 1 Missed!)
        if barrel_credit > 0 and not self._state.effect_stack.is_empty:
            entry = self._state.effect_stack.peek()
            if entry is not None and entry.handler.card_type == "bang":
                entry.missed_played += barrel_credit

        return events

    def _do_barrel_check(
        self, target_player_id: PlayerId, source_player_id: PlayerId
    ) -> list[DomainEvent]:
        """Check Barrel (blue card or Jourdonnais ability) before Missed! window."""
        events: list[DomainEvent] = []
        target = self._state.get_player(target_player_id)

        # Jourdonnais has an innate Barrel
        has_jourdonnais = target.character.has_ability("jourdonnais")
        has_barrel_card = target.has_card_type_on_table("barrel")

        # Check Jourdonnais innate Barrel first
        if has_jourdonnais:
            result = self._draw_check.perform_check(
                self._state.deck, BarrelCondition()
            )
            check_event = DrawCheckPerformed(
                player_id=target_player_id,
                check_type="barrel",
                card_face=result.card_drawn.face,
                passed=result.passed,
            )
            self._emit(check_event)
            events.append(check_event)

            if result.passed:
                ability_event = AbilityActivated(
                    player_id=target_player_id,
                    ability_name="jourdonnais",
                    character_type=target.character.character_type,
                )
                self._emit(ability_event)
                events.append(ability_event)
                return events  # Saved by innate Barrel

        # Check Barrel card on table
        if has_barrel_card:
            result = self._draw_check.perform_check(
                self._state.deck, BarrelCondition()
            )
            check_event = DrawCheckPerformed(
                player_id=target_player_id,
                check_type="barrel",
                card_face=result.card_drawn.face,
                passed=result.passed,
            )
            self._emit(check_event)
            events.append(check_event)

            if result.passed:
                return events  # Saved by Barrel card

        return events  # Not saved, proceed to Missed! window

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

            # Slab the Killer: track how many Missed! needed
            if handler.card_type == "bang":
                source = self._state.get_player(context.source_player_id)
                missed_needed = 1
                for ability in source.character.get_abilities_for_timing(
                    AbilityTiming.ON_MISSED_REQUIRED
                ):
                    ctx = AbilityContext(player_id=source.id)
                    if ability.can_activate(ctx):
                        result = ability.activate(ctx)
                        if result.modified_value is not None:
                            missed_needed = result.modified_value
                entry.missed_count_needed = missed_needed
                entry.missed_played = 0

            self._state.effect_stack.push(entry)

            # Switch to awaiting response
            assert self._state.current_turn is not None
            self._state.current_turn.current_phase = Phase.AWAITING_RESPONSE

        elif outcome.state == EffectState.COMPLETE:
            # Check for deaths from this effect
            self._process_deaths_from_events(outcome.events, context.source_player_id, events)

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

        # Validate response card type
        response_card = None
        if command.card_id is not None:
            player = self._state.get_player(command.player_id)
            response_card = player.get_card_from_hand(command.card_id)
            if response_card is None:
                raise InvalidActionError("Card not in hand")

            # Validate the card type matches what's expected
            valid_types = set(entry.response_window.valid_response_types)
            valid_types.discard("pass")  # "pass" is for no-card response

            actual_type = response_card.card_type

            # Calamity Janet: can use Bang! as Missed! and vice versa
            effective_type = actual_type
            if self._is_calamity_janet(command.player_id):
                if actual_type == "bang" and "missed" in valid_types:
                    effective_type = "missed"
                elif actual_type == "missed" and "bang" in valid_types:
                    effective_type = "bang"

            if effective_type not in valid_types and actual_type not in valid_types:
                raise InvalidActionError(
                    f"Cannot respond with {actual_type}; expected one of: {valid_types}"
                )

            player.remove_from_hand(command.card_id)
            self._state.deck.discard(response_card)

        # Handle Slab the Killer: need multiple Missed!
        if (
            entry.handler.card_type == "bang"
            and command.card_id is not None
            and entry.missed_count_needed > 1
        ):
            entry.missed_played += 1
            if entry.missed_played < entry.missed_count_needed:
                # Need more Missed! cards - stay awaiting
                entry.response_window = ResponseWindow(
                    responding_player_id=command.player_id,
                    valid_response_types=["missed", "pass"],
                    prompt=f"Play another Missed! ({entry.missed_played}/{entry.missed_count_needed}) or take 1 damage",
                )
                return []

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

            # Trigger damage-related character abilities
            for event in outcome.events:
                if isinstance(event, PlayerDamaged):
                    dmg_ability_events = self._trigger_on_take_damage(
                        event.player_id, event.amount, event.source_player_id
                    )
                    events.extend(dmg_ability_events)

            # Check deaths from this resolution
            self._process_deaths_from_events(
                outcome.events, entry.context.source_player_id, events
            )

            # Multi-target: advance to next target if there are remaining targets
            if entry.remaining_targets and not self._state.is_over:
                advance_events = self._advance_multi_target(entry)
                events.extend(advance_events)
            elif self._state.effect_stack.is_empty:
                # All effects resolved, return to play phase
                if self._state.current_turn is not None and not self._state.is_over:
                    self._state.current_turn.current_phase = Phase.PLAY_PHASE

        elif outcome.state == EffectState.AWAITING_RESPONSE:
            # Update entry (Duel alternating, etc.)
            entry.response_window = outcome.response_window
            entry.state = EffectState.AWAITING_RESPONSE
            if outcome.remaining_targets is not None:
                entry.remaining_targets = list(outcome.remaining_targets)
            if outcome.response_window:
                entry.current_target_id = (
                    outcome.response_window.responding_player_id
                )

        # Suzy Lafayette: draw when hand becomes empty (after discarding response card)
        if command.card_id is not None:
            suzy_events = self._trigger_suzy_lafayette(command.player_id)
            events.extend(suzy_events)

        return events

    def _advance_multi_target(
        self, completed_entry: EffectStackEntry
    ) -> list[DomainEvent]:
        """Advance a multi-target effect to the next target."""
        events: list[DomainEvent] = []
        remaining = completed_entry.remaining_targets

        # Filter out dead targets
        remaining = [
            t for t in remaining
            if self._state.seating.is_alive(t)
        ]

        if not remaining:
            # All targets handled, return to play phase
            if self._state.effect_stack.is_empty and self._state.current_turn is not None:
                self._state.current_turn.current_phase = Phase.PLAY_PHASE
            return events

        next_target = remaining[0]
        rest = remaining[1:]

        # Determine response type based on the effect
        card_type = completed_entry.handler.card_type
        if card_type == "indians":
            valid_responses = ["bang", "pass"]
            prompt = "Play a Bang! or lose 1 HP (Indians!)"
        elif card_type == "gatling":
            valid_responses = ["missed", "pass"]
            prompt = "Play a Missed! or take 1 damage (Gatling)"
        else:
            valid_responses = ["pass"]
            prompt = "Respond to effect"

        # For Gatling: do Barrel check for each target
        if card_type == "gatling":
            barrel_events = self._do_barrel_check(
                next_target, completed_entry.context.source_player_id
            )
            events.extend(barrel_events)
            if any(
                isinstance(e, DrawCheckPerformed) and e.check_type == "barrel" and e.passed
                for e in barrel_events
            ):
                # Barrel saved this target, advance to next
                completed_entry.remaining_targets = rest
                if rest:
                    return events + self._advance_multi_target(completed_entry)
                else:
                    if self._state.effect_stack.is_empty and self._state.current_turn is not None:
                        self._state.current_turn.current_phase = Phase.PLAY_PHASE
                    return events

        # Push new entry for next target
        new_entry = EffectStackEntry(
            handler=completed_entry.handler,
            context=completed_entry.context,
            state=EffectState.AWAITING_RESPONSE,
            response_window=ResponseWindow(
                responding_player_id=next_target,
                valid_response_types=valid_responses,
                prompt=prompt,
            ),
            remaining_targets=rest,
            current_target_id=next_target,
        )
        self._state.effect_stack.push(new_entry)

        if self._state.current_turn is not None:
            self._state.current_turn.current_phase = Phase.AWAITING_RESPONSE

        return events

    def _process_deaths_from_events(
        self,
        outcome_events: list[DomainEvent],
        killer_player_id: PlayerId | None,
        result_events: list[DomainEvent],
    ) -> None:
        """Check for PlayerAtZeroHP events and trigger elimination."""
        for event in outcome_events:
            if isinstance(event, PlayerAtZeroHP):
                death_events = self._check_elimination(
                    event.player_id, killer_player_id
                )
                result_events.extend(death_events)

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

        # Must be the dying player
        if self._dying_player_id is not None:
            if command.player_id != self._dying_player_id:
                raise InvalidActionError("Only the dying player can play Beer")
        elif player.hp > 0:
            raise InvalidActionError("You are not dying")

        if self._state.alive_count <= 2:
            raise InvalidActionError("Beer has no effect with only 2 players")

        card = player.get_card_from_hand(command.card_id)
        if card is None or card.card_type != "beer":
            raise InvalidActionError("Must play a Beer card")

        player.remove_from_hand(command.card_id)
        self._state.deck.discard(card)
        heal_events = player.heal(1)

        events: list[DomainEvent] = []
        self._emit_all(heal_events)
        events.extend(heal_events)

        save_event = BeerSavingAttempt(
            player_id=command.player_id, success=player.hp > 0
        )
        self._emit(save_event)
        events.append(save_event)

        # If player is still at 0 HP, they need more Beer or will die
        if player.hp > 0:
            # Saved! Clear dying state
            self._dying_player_id = None
            self._dying_killer_id = None

        return events

    def confirm_no_beer(self, player_id: PlayerId) -> list[DomainEvent]:
        """Player confirms they have no Beer to play (or chooses not to).
        This completes the elimination."""
        if self._dying_player_id != player_id:
            raise InvalidActionError("This player is not dying")

        killer_id = self._dying_killer_id
        self._dying_player_id = None
        self._dying_killer_id = None

        return self._complete_elimination(player_id, killer_id)

    # --- Character Ability Commands ---

    def _handle_draw_phase_choice(
        self, command: DrawPhaseChoiceCommand
    ) -> list[DomainEvent]:
        """Handle Jesse Jones / Pedro Ramirez draw phase choice."""
        turn = self._state.current_turn
        if turn is None or command.player_id != turn.active_player_id:
            raise NotYourTurnError("It is not your turn")
        # Stub for expansion - basic draw phase handled automatically
        raise InvalidActionError("Draw phase choice not applicable for this character")

    def _handle_kit_carlson_choice(
        self, command: KitCarlsonChoiceCommand
    ) -> list[DomainEvent]:
        """Handle Kit Carlson choosing which card to put back."""
        turn = self._state.current_turn
        if turn is None or command.player_id != turn.active_player_id:
            raise NotYourTurnError("It is not your turn")
        raise InvalidActionError("Kit Carlson choice not applicable")

    def _handle_sid_ketchum_heal(
        self, command: SidKetchumHealCommand
    ) -> list[DomainEvent]:
        """Sid Ketchum: discard 2 cards to heal 1 HP. Can be used any time during your turn."""
        turn = self._state.current_turn
        if turn is None:
            raise DomainError("No turn in progress")

        if command.player_id != turn.active_player_id:
            raise NotYourTurnError("It is not your turn")

        player = self._state.get_player(command.player_id)
        if not player.character.has_ability("sid_ketchum"):
            raise InvalidActionError("Only Sid Ketchum can use this ability")

        if player.hp >= player.max_hp:
            raise InvalidActionError("Already at full HP")

        # Discard 2 cards
        card1 = player.remove_from_hand(command.card_id_1)
        card2 = player.remove_from_hand(command.card_id_2)
        self._state.deck.discard(card1)
        self._state.deck.discard(card2)

        # Heal 1
        heal_events = player.heal(1)
        events: list[DomainEvent] = []
        self._emit_all(heal_events)
        events.extend(heal_events)

        ability_event = AbilityActivated(
            player_id=command.player_id,
            ability_name="sid_ketchum",
            character_type=player.character.character_type,
        )
        self._emit(ability_event)
        events.append(ability_event)

        return events

    # --- Turn End ---

    def _end_turn(self) -> list[DomainEvent]:
        """End the current turn and start the next."""
        turn = self._state.current_turn
        assert turn is not None

        if self._state.is_over:
            return []

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
        """
        Check if a player at 0 HP should be eliminated.

        Beer saving: if the player has Beer cards in hand and there are
        more than 2 players, they get a chance to play Beer before dying.
        """
        events: list[DomainEvent] = []
        player = self._state.get_player(dying_player_id)

        if player.hp > 0 or not player.is_alive:
            return events

        # Beer saving window: check if player has any Beer and >2 players alive
        has_beer = player.has_card_type_in_hand("beer")
        if has_beer and self._state.alive_count > 2:
            # Set dying state - wait for PlayBeerWhenDyingCommand or confirm_no_beer
            self._dying_player_id = dying_player_id
            self._dying_killer_id = killer_player_id
            return events  # Pause elimination, wait for Beer

        # No Beer available or only 2 players - eliminate immediately
        return self._complete_elimination(dying_player_id, killer_player_id)

    def _complete_elimination(
        self,
        dying_player_id: PlayerId,
        killer_player_id: PlayerId | None,
    ) -> list[DomainEvent]:
        """Complete the elimination of a player (after Beer saving window)."""
        events: list[DomainEvent] = []
        player = self._state.get_player(dying_player_id)

        if not player.is_alive:
            return events  # Already eliminated

        # Eliminate the player
        elim_events = player.eliminate()
        self._emit_all(elim_events)
        events.extend(elim_events)

        # Update seating
        self._state.seating.mark_eliminated(dying_player_id)

        # Vulture Sam: takes all cards from eliminated players
        vulture_events = self._trigger_vulture_sam(dying_player_id)
        events.extend(vulture_events)

        # If Vulture Sam took the cards, skip normal discard
        vulture_took = len(vulture_events) > 0

        # Bounty: killer killed an Outlaw -> draw 3
        if player.role == Role.OUTLAW and killer_player_id is not None:
            killer = self._state.get_player(killer_player_id)
            if killer.is_alive:
                for _ in range(3):
                    card = self._state.deck.draw()
                    killer.add_to_hand(card)

        # Penalty: Sheriff killed a Deputy -> Sheriff discards ALL hand + table
        if player.role == Role.DEPUTY and killer_player_id is not None:
            killer = self._state.get_player(killer_player_id)
            if killer.role == Role.SHERIFF:
                discarded = killer.discard_all()
                for card in discarded:
                    self._state.deck.discard(card)

        # Discard dead player's cards (if Vulture Sam didn't take them)
        if not vulture_took:
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

    # --- Character Ability Triggers ---

    def _is_calamity_janet(self, player_id: PlayerId) -> bool:
        """Check if player is Calamity Janet (can swap Bang!/Missed!)."""
        player = self._state.get_player(player_id)
        return player.character.has_ability("calamity_janet")

    def _trigger_on_take_damage(
        self,
        player_id: PlayerId,
        amount: int,
        source_player_id: PlayerId | None,
    ) -> list[DomainEvent]:
        """Trigger character abilities that fire on taking damage."""
        events: list[DomainEvent] = []
        player = self._state.get_player(player_id)

        # Bart Cassidy: draw a card for each damage taken
        if player.character.has_ability("bart_cassidy") and player.is_alive:
            for _ in range(amount):
                card = self._state.deck.draw()
                player.add_to_hand(card)
            ability_event = AbilityActivated(
                player_id=player_id,
                ability_name="bart_cassidy",
                character_type=player.character.character_type,
            )
            self._emit(ability_event)
            events.append(ability_event)

        # El Gringo: draw a card from the attacker's hand
        if (
            player.character.has_ability("el_gringo")
            and player.is_alive
            and source_player_id is not None
        ):
            source = self._state.get_player(source_player_id)
            if source.hand_size > 0:
                import random as _rng
                source_hand = source.hand
                stolen_card = source_hand[_rng.randint(0, len(source_hand) - 1)]
                source.remove_from_hand(stolen_card.id)
                player.add_to_hand(stolen_card)
                ability_event = AbilityActivated(
                    player_id=player_id,
                    ability_name="el_gringo",
                    character_type=player.character.character_type,
                )
                self._emit(ability_event)
                events.append(ability_event)

        return events

    def _trigger_suzy_lafayette(self, player_id: PlayerId) -> list[DomainEvent]:
        """Suzy Lafayette: draws a card when her hand becomes empty."""
        events: list[DomainEvent] = []
        player = self._state.get_player(player_id)

        if (
            player.character.has_ability("suzy_lafayette")
            and player.is_alive
            and player.hand_size == 0
        ):
            card = self._state.deck.draw()
            player.add_to_hand(card)
            ability_event = AbilityActivated(
                player_id=player_id,
                ability_name="suzy_lafayette",
                character_type=player.character.character_type,
            )
            self._emit(ability_event)
            events.append(ability_event)

        return events

    def _trigger_vulture_sam(self, eliminated_player_id: PlayerId) -> list[DomainEvent]:
        """Vulture Sam: takes all cards from eliminated players."""
        events: list[DomainEvent] = []
        eliminated = self._state.get_player(eliminated_player_id)

        # Find Vulture Sam among alive players
        for pid in self._state.seating.alive_players_in_order():
            player = self._state.get_player(pid)
            if player.character.has_ability("vulture_sam") and pid != eliminated_player_id:
                # Take all cards from eliminated player
                all_cards = eliminated.discard_all()
                for card in all_cards:
                    player.add_to_hand(card)

                if all_cards:
                    ability_event = AbilityActivated(
                        player_id=pid,
                        ability_name="vulture_sam",
                        character_type=player.character.character_type,
                    )
                    self._emit(ability_event)
                    events.append(ability_event)
                break  # Only one Vulture Sam

        return events

    def _trigger_black_jack_draw(self, player_id: PlayerId) -> list[DomainEvent]:
        """Black Jack: show 2nd drawn card; if red suit, draw an extra card."""
        events: list[DomainEvent] = []
        player = self._state.get_player(player_id)

        if not player.character.has_ability("black_jack"):
            return events

        # The 2nd card drawn (last card added to hand) is revealed
        if player.hand_size >= 1:
            second_card = player.hand[-1]  # Most recently drawn
            if second_card.face.is_hearts_or_diamonds():
                # Red suit: draw an extra card
                extra = self._state.deck.draw()
                player.add_to_hand(extra)
                ability_event = AbilityActivated(
                    player_id=player_id,
                    ability_name="black_jack",
                    character_type=player.character.character_type,
                )
                self._emit(ability_event)
                events.append(ability_event)

        return events
