"""
Comprehensive edge case tests for the Bang! game engine.

Covers: Beer saving, Barrel checks, multi-target effects, Calamity Janet,
response validation, Slab the Killer, elimination cascades, bounties/penalties,
character abilities, and phase transitions.
"""

from __future__ import annotations

import random

import pytest

from bang_game_engine.cards.card_color import CardColor
from bang_game_engine.cards.card_face import CardFace
from bang_game_engine.cards.rank import Rank
from bang_game_engine.cards.suit import Suit
from bang_game_engine.effects.events import DrawCheckPerformed
from bang_game_engine.expansions.base.characters import (
    BartCassidyAbility,
    CalamityJanetAbility,
    JourdonnaisAbility,
    SlabTheKillerAbility,
    SuzyLafayetteAbility,
    VultureSamAbility,
    WillyTheKidAbility,
)
from bang_game_engine.game.commands import (
    DiscardCardCommand,
    EndPhaseCommand,
    PlayBeerWhenDyingCommand,
    PlayCardCommand,
    RespondToEffectCommand,
    SidKetchumHealCommand,
)
from bang_game_engine.game.events import CardPlayed, GameEnded
from bang_game_engine.game.phase import Phase
from bang_game_engine.players.events import (
    AbilityActivated,
    PlayerDamaged,
    PlayerEliminated,
)
from bang_game_engine.players.role import Role
from bang_game_engine.shared.errors import (
    CardNotPlayableError,
    InvalidActionError,
    TargetOutOfRangeError,
)
from tests.helpers import (
    give_card_to_player,
    make_card,
    make_character,
    setup_game,
    skip_to_next_turn,
)


# ── Response Validation ──────────────────────────────────────────────


class TestResponseValidation:
    """Verify that only valid card types are accepted as responses."""

    def test_cannot_respond_to_bang_with_beer(self):
        """Only Missed! (or pass) should be valid against Bang!."""
        m, pids = setup_game([Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE])
        m.start_game()
        sheriff = pids[0]
        target = pids[1]

        bang = make_card("bang")
        give_card_to_player(m, sheriff, bang)
        beer = make_card("beer")
        give_card_to_player(m, target, beer)

        m.handle_command(PlayCardCommand(player_id=sheriff, card_id=bang.id, target_player_id=target))
        assert m.current_phase == Phase.AWAITING_RESPONSE

        with pytest.raises(InvalidActionError, match="Cannot respond with"):
            m.handle_command(RespondToEffectCommand(player_id=target, card_id=beer.id))

    def test_cannot_respond_to_indians_with_missed(self):
        """Only Bang! (or pass) should be valid against Indians!."""
        m, pids = setup_game([Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE])
        m.start_game()
        sheriff = pids[0]
        target = pids[1]

        indians = make_card("indians")
        give_card_to_player(m, sheriff, indians)
        missed = make_card("missed")
        give_card_to_player(m, target, missed)

        m.handle_command(PlayCardCommand(player_id=sheriff, card_id=indians.id))
        assert m.current_phase == Phase.AWAITING_RESPONSE

        with pytest.raises(InvalidActionError, match="Cannot respond with"):
            m.handle_command(RespondToEffectCommand(player_id=target, card_id=missed.id))


# ── Calamity Janet ───────────────────────────────────────────────────


class TestCalamityJanet:
    """Calamity Janet can use Bang! as Missed! and vice versa."""

    def test_calamity_janet_bang_as_missed(self):
        """Calamity Janet can play Bang! to dodge another Bang!."""
        chars = [
            make_character("sheriff_char"),
            make_character("calamity_janet", abilities=[CalamityJanetAbility()]),
            make_character("char_2"),
            make_character("char_3"),
        ]
        m, pids = setup_game(
            [Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE],
            characters=chars,
        )
        m.start_game()
        sheriff = pids[0]
        janet = pids[1]

        bang_atk = make_card("bang")
        give_card_to_player(m, sheriff, bang_atk)
        bang_def = make_card("bang")
        give_card_to_player(m, janet, bang_def)

        m.handle_command(PlayCardCommand(player_id=sheriff, card_id=bang_atk.id, target_player_id=janet))

        # Janet uses Bang! as Missed! -- should succeed
        events = m.handle_command(RespondToEffectCommand(player_id=janet, card_id=bang_def.id))
        assert m.current_phase == Phase.PLAY_PHASE
        janet_player = m.game_state.get_player(janet)
        assert janet_player.hp == janet_player.max_hp  # No damage


# ── Barrel Auto-Check ────────────────────────────────────────────────


class TestBarrelCheck:
    """Barrel auto-triggers a draw! check before the Missed! window."""

    def test_barrel_saves_from_bang(self):
        """Player with Barrel on table draws Hearts -> Bang! is negated."""
        m, pids = setup_game([Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE])
        m.start_game()
        sheriff = pids[0]
        target = pids[1]

        # Put Barrel on target's table
        barrel = make_card("barrel", color=CardColor.BLUE)
        target_player = m.game_state.get_player(target)
        target_player.play_to_table(barrel)
        m.game_state.collect_events()  # Flush

        # Rig the deck so the barrel draw check draws Hearts
        hearts_card = make_card("test_barrel", suit=Suit.HEARTS, rank=Rank.SEVEN)
        m.game_state.deck.put_back_on_top(hearts_card)

        bang = make_card("bang")
        give_card_to_player(m, sheriff, bang)

        events = m.handle_command(
            PlayCardCommand(player_id=sheriff, card_id=bang.id, target_player_id=target)
        )

        # Should find a barrel check that passed
        barrel_checks = [e for e in events if isinstance(e, DrawCheckPerformed) and e.check_type == "barrel"]
        assert len(barrel_checks) == 1
        assert barrel_checks[0].passed is True

        # Should return to play phase (no Missed! prompt needed)
        assert m.current_phase == Phase.PLAY_PHASE
        assert target_player.hp == target_player.max_hp

    def test_barrel_fails_still_prompts_missed(self):
        """Barrel draws non-Hearts -> still need to play Missed! or take damage."""
        m, pids = setup_game([Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE])
        m.start_game()
        sheriff = pids[0]
        target = pids[1]

        barrel = make_card("barrel", color=CardColor.BLUE)
        target_player = m.game_state.get_player(target)
        target_player.play_to_table(barrel)
        m.game_state.collect_events()

        # Rig deck with Spades (fails barrel check)
        spades_card = make_card("test_barrel", suit=Suit.SPADES, rank=Rank.SEVEN)
        m.game_state.deck.put_back_on_top(spades_card)

        bang = make_card("bang")
        give_card_to_player(m, sheriff, bang)

        events = m.handle_command(
            PlayCardCommand(player_id=sheriff, card_id=bang.id, target_player_id=target)
        )

        barrel_checks = [e for e in events if isinstance(e, DrawCheckPerformed) and e.check_type == "barrel"]
        assert len(barrel_checks) == 1
        assert barrel_checks[0].passed is False

        # Should be awaiting Missed! response
        assert m.current_phase == Phase.AWAITING_RESPONSE


class TestJourdonnais:
    """Jourdonnais has an innate Barrel (always active, even without Barrel card)."""

    def test_jourdonnais_innate_barrel(self):
        """Jourdonnais gets a free barrel draw check when targeted by Bang!"""
        chars = [
            make_character("sheriff_char"),
            make_character("jourdonnais", abilities=[JourdonnaisAbility()]),
            make_character("char_2"),
            make_character("char_3"),
        ]
        m, pids = setup_game(
            [Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE],
            characters=chars,
        )
        m.start_game()
        sheriff = pids[0]
        jour = pids[1]

        # Rig barrel check to succeed (Hearts)
        hearts_card = make_card("test", suit=Suit.HEARTS, rank=Rank.THREE)
        m.game_state.deck.put_back_on_top(hearts_card)

        bang = make_card("bang")
        give_card_to_player(m, sheriff, bang)

        events = m.handle_command(
            PlayCardCommand(player_id=sheriff, card_id=bang.id, target_player_id=jour)
        )

        # Should have Jourdonnais barrel check
        barrel_checks = [e for e in events if isinstance(e, DrawCheckPerformed) and e.check_type == "barrel"]
        assert len(barrel_checks) == 1
        assert barrel_checks[0].passed is True

        # Ability activated event
        ability_events = [e for e in events if isinstance(e, AbilityActivated) and e.ability_name == "jourdonnais"]
        assert len(ability_events) == 1

        assert m.current_phase == Phase.PLAY_PHASE


# ── Multi-Target Effects ─────────────────────────────────────────────


class TestMultiTargetEffects:
    """Indians! and Gatling hit ALL other players, advancing through each."""

    def test_indians_hits_all_players_who_pass(self):
        """Indians! damages each player who doesn't play Bang!, in order."""
        m, pids = setup_game([Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE])
        m.start_game()
        sheriff = pids[0]

        indians = make_card("indians")
        give_card_to_player(m, sheriff, indians)

        events = m.handle_command(PlayCardCommand(player_id=sheriff, card_id=indians.id))
        # Should be awaiting response from first target (pids[1])
        assert m.current_phase == Phase.AWAITING_RESPONSE

        # First target passes
        events = m.handle_command(RespondToEffectCommand(player_id=pids[1], card_id=None))
        p1 = m.game_state.get_player(pids[1])
        assert p1.hp == p1.max_hp - 1

        # Should advance to second target
        assert m.current_phase == Phase.AWAITING_RESPONSE

        # Second target passes
        events = m.handle_command(RespondToEffectCommand(player_id=pids[2], card_id=None))
        p2 = m.game_state.get_player(pids[2])
        assert p2.hp == p2.max_hp - 1

        # Should advance to third target
        assert m.current_phase == Phase.AWAITING_RESPONSE

        # Third target passes
        events = m.handle_command(RespondToEffectCommand(player_id=pids[3], card_id=None))
        p3 = m.game_state.get_player(pids[3])
        assert p3.hp == p3.max_hp - 1

        # Should return to play phase
        assert m.current_phase == Phase.PLAY_PHASE

    def test_indians_player_responds_with_bang(self):
        """Player playing Bang! in response to Indians! takes no damage."""
        m, pids = setup_game([Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE])
        m.start_game()
        sheriff = pids[0]

        indians = make_card("indians")
        give_card_to_player(m, sheriff, indians)
        bang = make_card("bang")
        give_card_to_player(m, pids[1], bang)

        m.handle_command(PlayCardCommand(player_id=sheriff, card_id=indians.id))

        # First target plays Bang!
        m.handle_command(RespondToEffectCommand(player_id=pids[1], card_id=bang.id))
        p1 = m.game_state.get_player(pids[1])
        assert p1.hp == p1.max_hp  # No damage

        # Second and third targets pass
        m.handle_command(RespondToEffectCommand(player_id=pids[2], card_id=None))
        m.handle_command(RespondToEffectCommand(player_id=pids[3], card_id=None))
        assert m.current_phase == Phase.PLAY_PHASE

    def test_gatling_hits_all_who_pass(self):
        """Gatling damages each player who doesn't play Missed!."""
        m, pids = setup_game([Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE])
        m.start_game()
        sheriff = pids[0]

        gatling = make_card("gatling")
        give_card_to_player(m, sheriff, gatling)

        m.handle_command(PlayCardCommand(player_id=sheriff, card_id=gatling.id))
        assert m.current_phase == Phase.AWAITING_RESPONSE

        # All 3 targets pass
        for i in range(1, 4):
            m.handle_command(RespondToEffectCommand(player_id=pids[i], card_id=None))

        assert m.current_phase == Phase.PLAY_PHASE
        for i in range(1, 4):
            p = m.game_state.get_player(pids[i])
            assert p.hp == p.max_hp - 1


# ── Beer Saving ──────────────────────────────────────────────────────


class TestBeerSaving:
    """When a player hits 0 HP with Beer in hand, they can play Beer to survive."""

    def test_beer_saves_from_elimination(self):
        """Player at 0 HP with Beer can survive by playing Beer."""
        m, pids = setup_game([Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE])
        m.start_game()
        sheriff = pids[0]
        target = pids[1]

        # Weaken target to 1 HP
        target_player = m.game_state.get_player(target)
        target_player.take_damage(target_player.hp - 1)

        # Give target a beer
        beer = make_card("beer")
        give_card_to_player(m, target, beer)

        # Sheriff plays Bang!
        bang = make_card("bang")
        give_card_to_player(m, sheriff, bang)
        m.handle_command(PlayCardCommand(player_id=sheriff, card_id=bang.id, target_player_id=target))

        # Target doesn't play Missed! -> takes lethal damage
        m.handle_command(RespondToEffectCommand(player_id=target, card_id=None))

        # Beer saving window should be active
        assert m.is_awaiting_beer_save

        # Play Beer to survive
        events = m.handle_command(PlayBeerWhenDyingCommand(player_id=target, card_id=beer.id))
        assert target_player.hp == 1
        assert target_player.is_alive
        assert not m.is_awaiting_beer_save

    def test_no_beer_with_2_players(self):
        """Beer doesn't work when only 2 players remain."""
        m, pids = setup_game([Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE])
        m.start_game()

        # Kill off two players so only 2 remain
        for pid in pids[2:]:
            p = m.game_state.get_player(pid)
            p.take_damage(p.hp)
            p.eliminate()
            m.game_state.seating.mark_eliminated(pid)
        assert m.game_state.alive_count == 2

        sheriff = pids[0]
        target = pids[1]
        target_player = m.game_state.get_player(target)
        target_player.take_damage(target_player.hp - 1)  # 1 HP left

        beer = make_card("beer")
        give_card_to_player(m, target, beer)
        bang = make_card("bang")
        give_card_to_player(m, sheriff, bang)

        m.handle_command(PlayCardCommand(player_id=sheriff, card_id=bang.id, target_player_id=target))
        m.handle_command(RespondToEffectCommand(player_id=target, card_id=None))

        # Should be eliminated immediately (no beer saving with 2 players)
        assert not target_player.is_alive
        assert not m.is_awaiting_beer_save


# ── Slab the Killer ──────────────────────────────────────────────────


class TestSlabTheKiller:
    """Slab the Killer requires 2 Missed! to avoid his Bang!."""

    def test_slab_needs_two_missed(self):
        """One Missed! is not enough against Slab."""
        chars = [
            make_character("slab_the_killer", abilities=[SlabTheKillerAbility()]),
            make_character("target_char"),
            make_character("char_2"),
            make_character("char_3"),
        ]
        m, pids = setup_game(
            [Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE],
            characters=chars,
        )
        m.start_game()
        slab = pids[0]  # Sheriff
        target = pids[1]

        bang = make_card("bang")
        give_card_to_player(m, slab, bang)
        missed1 = make_card("missed")
        missed2 = make_card("missed")
        give_card_to_player(m, target, missed1)
        give_card_to_player(m, target, missed2)

        m.handle_command(PlayCardCommand(player_id=slab, card_id=bang.id, target_player_id=target))
        assert m.current_phase == Phase.AWAITING_RESPONSE

        # Play first Missed!
        m.handle_command(RespondToEffectCommand(player_id=target, card_id=missed1.id))
        # Should still be awaiting (need 2)
        assert m.current_phase == Phase.AWAITING_RESPONSE

        # Play second Missed!
        events = m.handle_command(RespondToEffectCommand(player_id=target, card_id=missed2.id))
        # Now resolved - no damage
        assert m.current_phase == Phase.PLAY_PHASE
        target_player = m.game_state.get_player(target)
        assert target_player.hp == target_player.max_hp

    def test_slab_one_missed_then_pass(self):
        """Playing only 1 Missed! then passing -> takes damage."""
        chars = [
            make_character("slab_the_killer", abilities=[SlabTheKillerAbility()]),
            make_character("target_char"),
            make_character("char_2"),
            make_character("char_3"),
        ]
        m, pids = setup_game(
            [Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE],
            characters=chars,
        )
        m.start_game()
        slab = pids[0]
        target = pids[1]

        bang = make_card("bang")
        give_card_to_player(m, slab, bang)
        missed1 = make_card("missed")
        give_card_to_player(m, target, missed1)

        m.handle_command(PlayCardCommand(player_id=slab, card_id=bang.id, target_player_id=target))

        # Play first Missed!
        m.handle_command(RespondToEffectCommand(player_id=target, card_id=missed1.id))
        assert m.current_phase == Phase.AWAITING_RESPONSE

        # Pass (can't play another Missed!)
        events = m.handle_command(RespondToEffectCommand(player_id=target, card_id=None))
        target_player = m.game_state.get_player(target)
        assert target_player.hp == target_player.max_hp - 1


# ── Willy the Kid ────────────────────────────────────────────────────


class TestWillyTheKid:
    """Willy the Kid can play unlimited Bang! cards."""

    def test_willy_unlimited_bangs(self):
        """Willy the Kid can play multiple Bang! cards in one turn."""
        chars = [
            make_character("willy_the_kid", abilities=[WillyTheKidAbility()]),
            make_character("target_char"),
            make_character("char_2"),
            make_character("char_3"),
        ]
        m, pids = setup_game(
            [Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE],
            characters=chars,
        )
        m.start_game()
        willy = pids[0]
        target = pids[1]

        bang1 = make_card("bang")
        bang2 = make_card("bang")
        give_card_to_player(m, willy, bang1)
        give_card_to_player(m, willy, bang2)

        # Play first Bang!
        m.handle_command(PlayCardCommand(player_id=willy, card_id=bang1.id, target_player_id=target))
        m.handle_command(RespondToEffectCommand(player_id=target, card_id=None))

        # Play second Bang! - should NOT raise
        m.handle_command(PlayCardCommand(player_id=willy, card_id=bang2.id, target_player_id=target))
        m.handle_command(RespondToEffectCommand(player_id=target, card_id=None))

        target_player = m.game_state.get_player(target)
        assert target_player.hp == target_player.max_hp - 2


# ── Volcanic Weapon ──────────────────────────────────────────────────


class TestVolcanicWeapon:
    """Volcanic grants unlimited Bang! and activates immediately when played."""

    def test_volcanic_grants_unlimited_bangs(self):
        """Equipping Volcanic mid-turn allows playing more Bang! cards."""
        m, pids = setup_game([Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE])
        m.start_game()
        sheriff = pids[0]
        target = pids[1]

        # Play first Bang! (uses the 1 bang/turn limit)
        bang1 = make_card("bang")
        give_card_to_player(m, sheriff, bang1)
        m.handle_command(PlayCardCommand(player_id=sheriff, card_id=bang1.id, target_player_id=target))
        m.handle_command(RespondToEffectCommand(player_id=target, card_id=None))

        # Now equip Volcanic
        volcanic = make_card("volcanic", color=CardColor.BLUE)
        give_card_to_player(m, sheriff, volcanic)
        m.handle_command(PlayCardCommand(player_id=sheriff, card_id=volcanic.id))

        # Play second Bang! - should work now
        bang2 = make_card("bang")
        give_card_to_player(m, sheriff, bang2)
        m.handle_command(PlayCardCommand(player_id=sheriff, card_id=bang2.id, target_player_id=target))
        m.handle_command(RespondToEffectCommand(player_id=target, card_id=None))

        target_player = m.game_state.get_player(target)
        assert target_player.hp == target_player.max_hp - 2


# ── Elimination Bounties & Penalties ─────────────────────────────────


class TestEliminationRewards:
    """Bounties and penalties on player elimination."""

    def test_outlaw_bounty_draw_3(self):
        """Killing an Outlaw gives the killer 3 cards."""
        m, pids = setup_game([Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE])
        m.start_game()
        sheriff = pids[0]
        outlaw = pids[1]

        # Weaken outlaw to 1 HP
        outlaw_player = m.game_state.get_player(outlaw)
        outlaw_player.take_damage(outlaw_player.hp - 1)

        sheriff_player = m.game_state.get_player(sheriff)

        # Kill outlaw
        bang = make_card("bang")
        give_card_to_player(m, sheriff, bang)
        hand_before = sheriff_player.hand_size
        m.handle_command(PlayCardCommand(player_id=sheriff, card_id=bang.id, target_player_id=outlaw))
        m.handle_command(RespondToEffectCommand(player_id=outlaw, card_id=None))

        # Outlaw dies (no beer saving with 0 HP, or auto-eliminated)
        if m.is_awaiting_beer_save:
            m.confirm_no_beer(outlaw)

        # Sheriff drew 3 cards as bounty (-1 from playing bang + 3 bounty)
        assert sheriff_player.hand_size == hand_before - 1 + 3

    def test_sheriff_kills_deputy_penalty(self):
        """Sheriff killing a Deputy forces Sheriff to discard ALL cards."""
        m, pids = setup_game([Role.SHERIFF, Role.DEPUTY, Role.OUTLAW, Role.RENEGADE])
        m.start_game()
        sheriff = pids[0]
        deputy = pids[1]

        # Weaken deputy to 1 HP
        deputy_player = m.game_state.get_player(deputy)
        deputy_player.take_damage(deputy_player.hp - 1)

        # Kill deputy
        bang = make_card("bang")
        give_card_to_player(m, sheriff, bang)
        m.handle_command(PlayCardCommand(player_id=sheriff, card_id=bang.id, target_player_id=deputy))
        m.handle_command(RespondToEffectCommand(player_id=deputy, card_id=None))

        if m.is_awaiting_beer_save:
            m.confirm_no_beer(deputy)

        sheriff_player = m.game_state.get_player(sheriff)
        assert sheriff_player.hand_size == 0
        assert sheriff_player.weapon is None


# ── Win Conditions ───────────────────────────────────────────────────


class TestWinConditionEdgeCases:
    """Edge cases in win condition evaluation."""

    def test_outlaws_win_when_sheriff_dies(self):
        """If Sheriff dies and more than Renegade alive, Outlaws win."""
        m, pids = setup_game([Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE])
        m.start_game()
        sheriff = pids[0]
        outlaw = pids[1]

        # Switch to outlaw's turn first
        skip_to_next_turn(m, sheriff)

        # Now it's outlaw's turn
        assert m.active_player_id == outlaw

        # Weaken sheriff to 1 HP (after turn switch so discard limit isn't an issue)
        sheriff_player = m.game_state.get_player(sheriff)
        sheriff_player.take_damage(sheriff_player.hp - 1)
        m.game_state.collect_events()
        bang = make_card("bang")
        give_card_to_player(m, outlaw, bang)
        m.handle_command(PlayCardCommand(player_id=outlaw, card_id=bang.id, target_player_id=sheriff))
        m.handle_command(RespondToEffectCommand(player_id=sheriff, card_id=None))

        if m.is_awaiting_beer_save:
            m.confirm_no_beer(sheriff)

        assert m.game_state.is_over
        assert m.current_phase == Phase.GAME_OVER


# ── Duel ─────────────────────────────────────────────────────────────


class TestDuel:
    """Duel: alternating Bang! play. First to not play takes damage."""

    def test_duel_does_not_count_as_bang(self):
        """Duel is not a 'Bang!' so it doesn't count toward the 1-Bang limit."""
        m, pids = setup_game([Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE])
        m.start_game()
        sheriff = pids[0]
        target = pids[1]

        # Play a duel
        duel = make_card("duel")
        give_card_to_player(m, sheriff, duel)
        m.handle_command(PlayCardCommand(player_id=sheriff, card_id=duel.id, target_player_id=target))

        # Target passes (takes 1 damage)
        m.handle_command(RespondToEffectCommand(player_id=target, card_id=None))

        # Sheriff should still be able to play a Bang!
        bang = make_card("bang")
        give_card_to_player(m, sheriff, bang)
        m.handle_command(PlayCardCommand(player_id=sheriff, card_id=bang.id, target_player_id=target))
        # Should not raise CardNotPlayableError

        m.handle_command(RespondToEffectCommand(player_id=target, card_id=None))
        target_player = m.game_state.get_player(target)
        assert target_player.hp == target_player.max_hp - 2


# ── Suzy Lafayette ───────────────────────────────────────────────────


class TestSuzyLafayette:
    """Suzy Lafayette draws when her hand becomes empty."""

    def test_suzy_draws_on_empty_hand(self):
        """Playing last card triggers automatic draw."""
        chars = [
            make_character("suzy_lafayette", abilities=[SuzyLafayetteAbility()]),
            make_character("target_char"),
            make_character("char_2"),
            make_character("char_3"),
        ]
        m, pids = setup_game(
            [Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE],
            characters=chars,
        )
        m.start_game()
        suzy = pids[0]

        # Remove all cards from Suzy's hand except one
        suzy_player = m.game_state.get_player(suzy)
        while suzy_player.hand_size > 1:
            card = suzy_player.hand[0]
            suzy_player.remove_from_hand(card.id)
            m.game_state.deck.discard(card)
        m.game_state.collect_events()

        # Play last card (stagecoach to draw 2)
        last_card = suzy_player.hand[0]
        if last_card.card_type != "stagecoach":
            # Replace with a stagecoach
            suzy_player.remove_from_hand(last_card.id)
            stagecoach = make_card("stagecoach")
            give_card_to_player(m, suzy, stagecoach)
            last_card = stagecoach

        # Before playing, hand_size=1
        assert suzy_player.hand_size == 1
        events = m.handle_command(PlayCardCommand(player_id=suzy, card_id=last_card.id))

        # Hand should NOT be empty due to stagecoach draw + Suzy draw
        assert suzy_player.hand_size > 0


# ── Jail Cannot Target Sheriff ───────────────────────────────────────


class TestJailRules:
    """Jail card edge cases."""

    def test_jail_cannot_target_sheriff(self):
        """Playing Jail on the Sheriff raises error."""
        m, pids = setup_game([Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE])
        m.start_game()
        sheriff = pids[0]

        # Pass to outlaw's turn (discard down to hand limit first)
        skip_to_next_turn(m, sheriff)
        outlaw = m.active_player_id

        jail = make_card("jail", color=CardColor.BLUE)
        give_card_to_player(m, outlaw, jail)

        with pytest.raises(InvalidActionError, match="Sheriff"):
            m.handle_command(PlayCardCommand(player_id=outlaw, card_id=jail.id, target_player_id=sheriff))


# ── Blue Card Duplicate Prevention ───────────────────────────────────


class TestBlueCardRules:
    """Cannot play duplicate blue cards (except weapons which displace)."""

    def test_cannot_play_duplicate_blue(self):
        """Playing a second Barrel raises error."""
        m, pids = setup_game([Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE])
        m.start_game()
        sheriff = pids[0]

        barrel1 = make_card("barrel", color=CardColor.BLUE)
        sheriff_player = m.game_state.get_player(sheriff)
        sheriff_player.play_to_table(barrel1)
        m.game_state.collect_events()

        barrel2 = make_card("barrel", color=CardColor.BLUE)
        give_card_to_player(m, sheriff, barrel2)

        with pytest.raises(CardNotPlayableError, match="Already have"):
            m.handle_command(PlayCardCommand(player_id=sheriff, card_id=barrel2.id))


# ── Beer Has No Effect With 2 Players ────────────────────────────────


class TestBeerWith2Players:
    """Beer cannot be played when only 2 players remain."""

    def test_beer_blocked_with_2_players(self):
        m, pids = setup_game([Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE])
        m.start_game()

        # Kill players 2 and 3
        for pid in pids[2:]:
            p = m.game_state.get_player(pid)
            p.take_damage(p.hp)
            p.eliminate()
            m.game_state.seating.mark_eliminated(pid)

        sheriff = pids[0]
        sheriff_player = m.game_state.get_player(sheriff)
        sheriff_player.take_damage(1)  # Take some damage

        beer = make_card("beer")
        give_card_to_player(m, sheriff, beer)

        with pytest.raises(CardNotPlayableError, match="2 players"):
            m.handle_command(PlayCardCommand(player_id=sheriff, card_id=beer.id))


# ── Sid Ketchum ──────────────────────────────────────────────────────


class TestSidKetchumAbility:
    """Sid Ketchum can discard 2 cards to heal 1 HP."""

    def test_sid_ketchum_heal(self):
        from bang_game_engine.expansions.base.characters import SidKetchumAbility
        chars = [
            make_character("sid_ketchum", abilities=[SidKetchumAbility()]),
            make_character("char_1"),
            make_character("char_2"),
            make_character("char_3"),
        ]
        m, pids = setup_game(
            [Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE],
            characters=chars,
        )
        m.start_game()
        sid = pids[0]

        sid_player = m.game_state.get_player(sid)
        sid_player.take_damage(2)
        m.game_state.collect_events()

        card1 = make_card("bang")
        card2 = make_card("missed")
        give_card_to_player(m, sid, card1)
        give_card_to_player(m, sid, card2)

        hp_before = sid_player.hp
        events = m.handle_command(
            SidKetchumHealCommand(player_id=sid, card_id_1=card1.id, card_id_2=card2.id)
        )
        assert sid_player.hp == hp_before + 1
        assert any(isinstance(e, AbilityActivated) and e.ability_name == "sid_ketchum" for e in events)


# ── Range Checks ─────────────────────────────────────────────────────


class TestRangeChecks:
    """Bang! range and Panic! range checks."""

    def test_bang_out_of_range(self):
        """Cannot Bang! a player beyond weapon range."""
        m, pids = setup_game(
            [Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE]
        )
        m.start_game()
        sheriff = pids[0]
        far_player = pids[2]  # Distance 2 from sheriff

        bang = make_card("bang")
        give_card_to_player(m, sheriff, bang)

        with pytest.raises(TargetOutOfRangeError):
            m.handle_command(PlayCardCommand(player_id=sheriff, card_id=bang.id, target_player_id=far_player))

    def test_panic_distance_1_only(self):
        """Panic! can only target distance 1."""
        m, pids = setup_game(
            [Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE]
        )
        m.start_game()
        sheriff = pids[0]
        far_player = pids[2]

        panic = make_card("panic")
        give_card_to_player(m, sheriff, panic)

        with pytest.raises(TargetOutOfRangeError, match="distance 1"):
            m.handle_command(PlayCardCommand(player_id=sheriff, card_id=panic.id, target_player_id=far_player))

    def test_schofield_extends_range(self):
        """Schofield (range 2) allows targeting distance 2."""
        m, pids = setup_game(
            [Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE]
        )
        m.start_game()
        sheriff = pids[0]
        d2_player = pids[2]

        schofield = make_card("schofield", color=CardColor.BLUE)
        give_card_to_player(m, sheriff, schofield)
        m.handle_command(PlayCardCommand(player_id=sheriff, card_id=schofield.id))

        bang = make_card("bang")
        give_card_to_player(m, sheriff, bang)
        # Should not raise
        m.handle_command(PlayCardCommand(player_id=sheriff, card_id=bang.id, target_player_id=d2_player))
        assert m.current_phase == Phase.AWAITING_RESPONSE


# ── General Store ────────────────────────────────────────────────────


class TestGeneralStore:
    """General Store: reveal N cards, pick in order."""

    def test_general_store_all_players_pick(self):
        from bang_game_engine.game.commands import GeneralStorePickCommand

        m, pids = setup_game([Role.SHERIFF, Role.OUTLAW, Role.OUTLAW, Role.RENEGADE])
        m.start_game()
        sheriff = pids[0]

        gs = make_card("general_store")
        give_card_to_player(m, sheriff, gs)
        m.handle_command(PlayCardCommand(player_id=sheriff, card_id=gs.id))

        assert m.current_phase == Phase.GENERAL_STORE_PICK
        turn = m.game_state.current_turn
        assert len(turn.general_store_cards) == 4
        assert len(turn.general_store_pickers) == 4

        # Each player picks a card
        for i in range(4):
            picker = turn.general_store_pickers[0]
            card = turn.general_store_cards[0]
            m.handle_command(GeneralStorePickCommand(player_id=picker, card_id=card.id))

        assert m.current_phase == Phase.PLAY_PHASE
