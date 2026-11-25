import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import data
import engine
from engine import Game, IllegalAction, Loadout


def make_game(p0_troops, p1_troops, p0_cmds=(), p1_cmds=(), obstacles=()):
    """A game with explicit positions: troops are (kind, row, col). Player 0 moves first."""
    g = Game()
    g.obstacles = set(obstacles)
    for player, troops in ((0, p0_troops), (1, p1_troops)):
        for kind, r, c in troops:
            g._spawn(player, kind, r, c)
    g.commands = [list(p0_cmds), list(p1_cmds)]
    g.cooldowns = [{c: 0 for c in p0_cmds}, {c: 0 for c in p1_cmds}]
    g._start_turn(0)
    return g


def uid_at(g, r, c):
    return g.unit_at(r, c).uid


class LoadoutTests(unittest.TestCase):
    def test_budget_and_limits(self):
        lo = Loadout()
        for _ in range(5):
            lo.add_troop("champion")             # 5 x 200 = 1000
        self.assertEqual(lo.gold_left, 0)
        self.assertFalse(lo.can_add_troop("scout"))
        with self.assertRaises(IllegalAction):
            lo.add_troop("scout")
        lo.remove_troop(0)
        self.assertEqual(lo.gold_left, 200)

    def test_max_ten_troops(self):
        lo = Loadout()
        for _ in range(10):
            lo.add_troop("scout")
        with self.assertRaises(IllegalAction):
            lo.add_troop("scout")

    def test_commands_max_four_no_duplicates(self):
        lo = Loadout()
        for c in ("battle_cry", "charge", "stoicism", "vigilance"):
            lo.add_command(c)
        self.assertFalse(lo.can_add_command("bombard"))
        lo2 = Loadout()
        lo2.add_command("charge")
        self.assertFalse(lo2.can_add_command("charge"))

    def test_ready_needs_only_one_troop(self):
        lo = Loadout()
        self.assertFalse(lo.is_ready)
        lo.add_troop("scout")
        self.assertTrue(lo.is_ready)             # fewer than 10 troops / 4 commands is fine

    def test_validate_rejects_overspend(self):
        lo = Loadout(troops=["champion"] * 6)
        self.assertFalse(lo.is_ready)


class ObstacleTests(unittest.TestCase):
    def test_obstacles_obey_the_wiki(self):
        sizes = set()
        for seed in range(500):
            cells = engine.generate_obstacles(random.Random(seed))
            sizes.add(len(cells))
            self.assertTrue(1 <= len(cells) <= 12)       # 1-3 shapes of at most 4 tiles each
            for r, c in cells:
                self.assertTrue(engine.OBSTACLE_ROWS[0] <= r <= engine.OBSTACLE_ROWS[1])
                self.assertTrue(0 <= c < engine.BOARD_SIZE)
        self.assertIn(1, sizes)                          # a lone crate happens
        self.assertTrue(max(sizes) >= 8)                 # and so do big layouts

    def test_armies_have_a_clear_path_zone(self):
        for seed in range(200):
            for r, _ in engine.generate_obstacles(random.Random(seed)):
                self.assertNotIn(r, engine.START_ROWS[0] + engine.START_ROWS[1])


class FormationTests(unittest.TestCase):
    def test_auto_formation_stays_in_start_rows_and_never_overlaps(self):
        for player in (0, 1):
            for n in range(1, 11):
                spots = engine.auto_formation(["scout"] * n, player)
                self.assertEqual(len(set(spots)), n)
                for r, c in spots:
                    self.assertIn(r, engine.START_ROWS[player])
                    self.assertTrue(0 <= c < engine.BOARD_SIZE)

    def test_new_game_places_everything(self):
        lo = Loadout(troops=["scout"] * 4 + ["knight"] * 3, commands=["charge"])
        g = Game.new([lo, Loadout.from_dict(lo.to_dict())], rng=random.Random(1))
        self.assertEqual(len(g.units_of(0)), 7)
        self.assertEqual(len(g.units_of(1)), 7)
        self.assertEqual(g.current, 0)
        self.assertEqual(g.command_points[0], engine.COMMAND_POINTS_PER_TURN)

    def test_bad_formation_rejected(self):
        lo = Loadout(troops=["scout"])
        with self.assertRaises(IllegalAction):
            Game.new([lo, Loadout(troops=["scout"])], formations=[[(10, 5)], [(0, 0)]])


class MovementTests(unittest.TestCase):
    def test_reach_is_manhattan_limited_by_speed(self):
        g = make_game([("foot_soldier", 17, 5)], [("scout", 0, 5)])
        tiles = g.reachable_tiles(g.unit_at(17, 5))
        self.assertEqual(tiles[(13, 5)], 4)
        self.assertNotIn((12, 5), tiles)
        self.assertNotIn((14, 7), tiles)         # 3 + 2 = 5 steps
        self.assertIn((15, 7), tiles)            # 2 + 2 = 4 steps

    def test_obstacles_and_units_block(self):
        g = make_game([("scout", 10, 5), ("knight", 10, 6)], [("scout", 0, 0)], obstacles=[(9, 5), (11, 5)])
        scout = g.unit_at(10, 5)
        tiles = g.reachable_tiles(scout)
        self.assertNotIn((9, 5), tiles)
        self.assertNotIn((10, 6), tiles)
        self.assertIn((10, 4), tiles)
        # going around the obstacle costs extra steps
        self.assertEqual(tiles[(8, 5)], 4)       # (10,5)->(10,4)->(9,4)->(8,4)->(8,5)

    def test_move_spends_budget_and_allows_a_second_move(self):
        g = make_game([("scout", 17, 5)], [("scout", 0, 5)])
        g.select_unit(uid_at(g, 17, 5))
        g.move_unit(14, 5)
        self.assertEqual(g.moves_left, 3)
        g.move_unit(14, 8)
        self.assertEqual(g.moves_left, 0)
        with self.assertRaises(IllegalAction):
            g.move_unit(14, 9)

    def test_cannot_move_out_of_phase_or_off_range(self):
        g = make_game([("scout", 17, 5)], [("scout", 0, 5)])
        with self.assertRaises(IllegalAction):
            g.move_unit(16, 5)                   # nothing selected yet
        g.select_unit(uid_at(g, 17, 5))
        with self.assertRaises(IllegalAction):
            g.move_unit(5, 5)

    def test_cannot_select_enemy_or_twice(self):
        g = make_game([("scout", 17, 5)], [("scout", 0, 5)])
        with self.assertRaises(IllegalAction):
            g.select_unit(uid_at(g, 0, 5))
        g.select_unit(uid_at(g, 17, 5))
        with self.assertRaises(IllegalAction):
            g.select_unit(uid_at(g, 17, 5))


class CombatTests(unittest.TestCase):
    def test_knight_kills_foot_soldier_without_retaliation(self):
        g = make_game([("knight", 10, 5)], [("foot_soldier", 9, 5)])
        g.select_unit(uid_at(g, 10, 5))
        g.attack(uid_at(g, 9, 5))
        self.assertIsNone(g.unit_at(9, 5))               # 300 damage vs 300 hp
        self.assertEqual(g.unit_at(10, 5).health, 300)
        self.assertEqual(g.winner, 0)

    def test_retaliation_when_defender_survives(self):
        g = make_game([("foot_soldier", 10, 5), ("scout", 17, 0)], [("foot_soldier", 9, 5), ("scout", 0, 0)])
        g.select_unit(uid_at(g, 10, 5))
        g.attack(uid_at(g, 9, 5))
        self.assertEqual(g.unit_at(9, 5).health, 200)
        self.assertEqual(g.unit_at(10, 5).health, 200)       # took the counter-hit
        self.assertEqual(g.phase, engine.RALLY)

    def test_ranged_attacker_is_not_retaliated_against_out_of_range(self):
        g = make_game([("archer", 10, 5), ("scout", 17, 0)], [("foot_soldier", 5, 5), ("scout", 0, 0)])
        g.select_unit(uid_at(g, 10, 5))
        g.attack(uid_at(g, 5, 5))                            # distance 5, archer range 6
        self.assertEqual(g.unit_at(5, 5).health, 200)
        self.assertEqual(g.unit_at(10, 5).health, 100)

    def test_halberdier_outranges_melee(self):
        g = make_game([("halberdier", 10, 5), ("scout", 17, 0)], [("foot_soldier", 8, 5), ("scout", 0, 0)])
        g.select_unit(uid_at(g, 10, 5))
        g.attack(uid_at(g, 8, 5))
        self.assertEqual(g.unit_at(10, 5).health, 200)       # no retaliation at distance 2

    def test_out_of_range_attack_rejected(self):
        g = make_game([("knight", 10, 5)], [("scout", 5, 5), ("scout", 0, 0)])
        g.select_unit(uid_at(g, 10, 5))
        with self.assertRaises(IllegalAction):
            g.attack(uid_at(g, 5, 5))

    def test_one_attack_per_turn(self):
        g = make_game([("foot_soldier", 10, 5), ("scout", 17, 0)], [("foot_soldier", 9, 5), ("scout", 0, 0)])
        g.select_unit(uid_at(g, 10, 5))
        g.attack(uid_at(g, 9, 5))
        with self.assertRaises(IllegalAction):
            g.attack(uid_at(g, 9, 5))

    def test_attacker_killed_by_retaliation(self):
        g = make_game([("scout", 10, 5), ("scout", 17, 0)], [("champion", 9, 5), ("scout", 0, 0)])
        g.select_unit(uid_at(g, 10, 5))
        g.attack(uid_at(g, 9, 5))
        self.assertIsNone(g.unit_at(10, 5))
        self.assertIsNone(g.selected)
        self.assertEqual(g.command_points[1], 25)        # the defender is credited with the scout's cost

    def test_kill_credits_command_points(self):
        g = make_game([("knight", 10, 5)], [("scout", 9, 5), ("scout", 0, 0)])
        before = g.command_points[0]
        g.select_unit(uid_at(g, 10, 5))
        g.attack(uid_at(g, 9, 5))
        self.assertEqual(g.command_points[0], before + 25)

    def test_win_when_all_units_gone(self):
        g = make_game([("champion", 10, 5)], [("scout", 9, 5)])
        g.select_unit(uid_at(g, 10, 5))
        g.attack(uid_at(g, 9, 5))
        self.assertEqual(g.winner, 0)
        with self.assertRaises(IllegalAction):
            g.end_turn()


class CommandTests(unittest.TestCase):
    def setUp(self):
        random.seed(1)

    def give_points(self, g, player, n=1000):
        g.command_points[player] = n

    def test_battle_cry_lets_knight_one_shot_a_champion(self):
        g = make_game([("knight", 10, 5)], [("champion", 9, 5), ("scout", 0, 0)], p0_cmds=["battle_cry"])
        self.give_points(g, 0)
        g.use_command("battle_cry", uid_at(g, 10, 5))
        g.select_unit(uid_at(g, 10, 5))
        g.attack(uid_at(g, 9, 5))
        self.assertIsNone(g.unit_at(9, 5))                   # 300 + 200 = 500 damage

    def test_cost_cooldown_and_points(self):
        g = make_game([("knight", 10, 5)], [("scout", 0, 0)], p0_cmds=["battle_cry"])
        g.command_points[0] = 100
        g.use_command("battle_cry", uid_at(g, 10, 5))
        self.assertEqual(g.command_points[0], 25)
        self.assertEqual(g.cooldowns[0]["battle_cry"], 5)
        self.assertIn("cooldown", g.command_status(0, "battle_cry"))

    def test_not_enough_points(self):
        g = make_game([("knight", 10, 5)], [("scout", 0, 0)], p0_cmds=["bombard"])
        with self.assertRaises(IllegalAction):
            g.use_command("bombard", uid_at(g, 0, 0))

    def test_cooldown_counts_down_on_own_turns(self):
        g = make_game([("knight", 10, 5)], [("scout", 0, 0)], p0_cmds=["chastise"])
        g.command_points[0] = 500
        g.cooldowns[0]["chastise"] = 3
        for expected in (2, 1, 0):
            g.end_turn(); g.end_turn()
            self.assertEqual(g.cooldowns[0]["chastise"], expected)

    def test_stoicism_grants_temporary_health_not_real_health(self):
        g = make_game([("scout", 17, 0)], [("foot_soldier", 3, 5), ("scout", 0, 0)], p1_cmds=["stoicism"])
        g.end_turn()
        g.command_points[1] = 500
        fs = g.unit_at(3, 5)
        g.use_command("stoicism", fs.uid)
        self.assertEqual((fs.health, fs.temp_health), (300, 400))

    def test_damage_drains_temporary_health_first_then_spills_over(self):
        g = make_game([("champion", 10, 5), ("scout", 17, 0)], [("foot_soldier", 9, 5), ("scout", 0, 0)])
        fs = g.unit_at(9, 5)
        fs.effects["stoicism"] = 1
        fs.temp_health = 400
        g.select_unit(uid_at(g, 10, 5))
        g.attack(fs.uid)                                     # champion hits for 400: all absorbed
        self.assertEqual((fs.health, fs.temp_health), (300, 0))
        g2 = make_game([("champion", 10, 5), ("scout", 17, 0)], [("foot_soldier", 9, 5), ("scout", 0, 0)])
        fs2 = g2.unit_at(9, 5)
        fs2.effects["battle_cry"] = 1
        fs2.temp_health = 200
        g2.select_unit(uid_at(g2, 10, 5))
        g2.attack(fs2.uid)                                   # 400 damage: 200 absorbed, 200 real
        self.assertEqual((fs2.health, fs2.temp_health), (100, 0))

    def test_temporary_health_is_stripped_at_the_casters_next_turn(self):
        g = make_game([("scout", 17, 0)], [("foot_soldier", 3, 5), ("scout", 0, 0)], p1_cmds=["stoicism"])
        g.end_turn()
        g.command_points[1] = 500
        fs = g.unit_at(3, 5)
        g.use_command("stoicism", fs.uid)
        g.end_turn()                                         # player 1's turn: buff still there
        self.assertEqual(fs.temp_health, 400)
        self.assertIn("stoicism", fs.effects)
        g.end_turn()                                         # player 2's next turn: stripped
        self.assertEqual(fs.temp_health, 0)
        self.assertNotIn("stoicism", fs.effects)
        self.assertEqual(fs.health, 300)

    def test_partially_spent_temporary_health_never_leaves_you_healthier(self):
        g = make_game([("scout", 17, 0)], [("foot_soldier", 3, 5), ("scout", 0, 0)], p1_cmds=["stoicism"])
        g.end_turn()
        g.command_points[1] = 500
        fs = g.unit_at(3, 5)
        g.use_command("stoicism", fs.uid)
        g._damage(fs, 150)                                   # absorbed by the temporary pool
        self.assertEqual((fs.health, fs.temp_health), (300, 250))
        g.end_turn(); g.end_turn()
        self.assertEqual((fs.health, fs.temp_health), (300, 0))   # same real health as before the buff

    def test_buff_never_heals_a_damaged_troop(self):
        g = make_game([("scout", 17, 0)], [("knight", 3, 5), ("scout", 0, 0)], p1_cmds=["battle_cry"])
        g.end_turn()
        g.command_points[1] = 500
        knight = g.unit_at(3, 5)
        knight.health = 120
        g.use_command("battle_cry", knight.uid)
        self.assertEqual(knight.health, 120)
        g.end_turn(); g.end_turn()
        self.assertEqual(knight.health, 120)

    def test_health_after_a_buff_is_never_more_than_before_it(self):
        """Whatever the damage in between, expiry leaves real health <= what it was when the buff was cast."""
        rng = random.Random(3)
        for _ in range(200):
            g = make_game([("scout", 17, 0)], [("champion", 3, 5), ("scout", 0, 0)], p1_cmds=["stoicism", "battle_cry"])
            g.end_turn()
            g.command_points[1] = 1000
            champ = g.unit_at(3, 5)
            champ.health = rng.randint(1, 500)
            before = champ.health
            for cmd in ("stoicism", "battle_cry"):
                if rng.random() < 0.7:
                    g.use_command(cmd, champ.uid)
            g.end_turn()                                     # the opponent's turn: damage lands here
            for _ in range(rng.randint(0, 4)):
                if champ.uid in g.units:
                    g._damage(champ, rng.choice([50, 100, 200, 400]))
            if champ.uid not in g.units or champ.health <= 0:
                continue
            g.end_turn()                                     # back to the caster: the buff expires
            self.assertEqual(champ.temp_health, 0)
            self.assertLessEqual(champ.health, before)

    def test_two_temporary_health_buffs_stack_and_expire_together(self):
        g = make_game([("scout", 17, 0)], [("champion", 3, 5), ("scout", 0, 0)], p1_cmds=["stoicism", "battle_cry"])
        g.end_turn()
        g.command_points[1] = 1000
        champ = g.unit_at(3, 5)
        g.use_command("stoicism", champ.uid)
        g.use_command("battle_cry", champ.uid)
        self.assertEqual(champ.temp_health, 600)
        g.end_turn(); g.end_turn()
        self.assertEqual((champ.health, champ.temp_health), (500, 0))

    def test_bombard_hits_temporary_health_first(self):
        g = make_game([("scout", 17, 0)], [("knight", 0, 0), ("scout", 0, 5)], p0_cmds=["bombard"])
        self.give_points(g, 0, 400)
        knight = g.unit_at(0, 0)
        knight.effects["battle_cry"] = 1
        knight.temp_health = 200
        g.use_command("bombard", knight.uid)
        self.assertEqual((knight.health, knight.temp_health), (300, 100))

    def test_regenerate_restores_to_max(self):
        g = make_game([("champion", 10, 5)], [("scout", 0, 0)], p0_cmds=["regenerate"])
        self.give_points(g, 0)
        c = g.unit_at(10, 5)
        c.health = 50
        g.use_command("regenerate", c.uid)
        self.assertEqual(c.health, 500)

    def test_regenerate_restores_real_health_and_leaves_temporary_health_alone(self):
        g = make_game([("champion", 10, 5)], [("scout", 0, 0)], p0_cmds=["regenerate"])
        self.give_points(g, 0)
        c = g.unit_at(10, 5)
        c.health, c.temp_health = 50, 120
        c.effects["stoicism"] = 0
        g.use_command("regenerate", c.uid)
        self.assertEqual((c.health, c.temp_health), (500, 120))

    def test_bombard_reduces_health_and_kill_gives_no_points(self):
        g = make_game([("scout", 17, 0)], [("scout", 0, 0), ("knight", 0, 5)], p0_cmds=["bombard"])
        self.give_points(g, 0, 400)
        g.use_command("bombard", uid_at(g, 0, 0))
        self.assertIsNone(g.unit_at(0, 0))
        self.assertEqual(g.command_points[0], 200)           # 400 - 200 cost, no 25 refund

    def test_bombard_ignores_shield_wall(self):
        g = make_game([("scout", 17, 0)], [("knight", 0, 0), ("scout", 0, 5)],
                      p0_cmds=["bombard"], p1_cmds=["shield_wall"])
        self.give_points(g, 0, 400)
        knight = g.unit_at(0, 0)
        knight.effects["shield_wall"] = 1
        g.use_command("bombard", knight.uid)
        self.assertEqual(knight.health, 200)

    def test_shield_wall_caps_damage(self):
        g = make_game([("champion", 10, 5), ("scout", 17, 0)], [("foot_soldier", 9, 5), ("scout", 0, 0)])
        g.unit_at(9, 5).effects["shield_wall"] = 1
        g.select_unit(uid_at(g, 10, 5))
        g.attack(uid_at(g, 9, 5))
        self.assertEqual(g.unit_at(9, 5).health, 200)        # took 100, not 400

    def test_chastise_blocks_selection_but_not_retaliation(self):
        g = make_game([("foot_soldier", 10, 5), ("scout", 17, 0)], [("foot_soldier", 9, 5), ("scout", 0, 0)],
                      p0_cmds=["chastise"])
        self.give_points(g, 0)
        victim = uid_at(g, 9, 5)
        g.use_command("chastise", victim)
        g.select_unit(uid_at(g, 10, 5))
        g.attack(victim)
        self.assertEqual(g.units[uid_at(g, 10, 5)].health, 200)   # the chastised unit still hit back
        g.end_turn()                                              # player 2's turn
        with self.assertRaises(IllegalAction):
            g.select_unit(victim)
        self.assertEqual(g.reachable_tiles(g.units[victim]), {})
        g.select_unit(uid_at(g, 0, 0))                            # but its sibling can act
        g.end_turn()                                              # player 1: chastise wears off
        g.end_turn()                                              # player 2 again
        g.select_unit(victim)

    def test_cannot_chastise_last_troop(self):
        g = make_game([("knight", 10, 5)], [("scout", 0, 0)], p0_cmds=["chastise"])
        self.give_points(g, 0)
        with self.assertRaises(IllegalAction):
            g.use_command("chastise", uid_at(g, 0, 0))

    def test_vigilance_makes_defender_strike_first(self):
        g = make_game([("foot_soldier", 10, 5), ("scout", 17, 0)], [("champion", 9, 5), ("scout", 0, 0)])
        g.unit_at(9, 5).effects["vigilance"] = 1
        g.select_unit(uid_at(g, 10, 5))
        g.attack(uid_at(g, 9, 5))
        self.assertIsNone(g.unit_at(10, 5))                  # champion hit first for 400 and killed it
        self.assertEqual(g.unit_at(9, 5).health, 500)

    def test_charge_doubles_movement_before_and_during_selection(self):
        g = make_game([("scout", 17, 5), ("knight", 17, 10)], [("scout", 0, 0)], p0_cmds=["charge"])
        self.give_points(g, 0)
        g.use_command("charge", uid_at(g, 17, 10))
        g.select_unit(uid_at(g, 17, 10))
        self.assertEqual(g.moves_left, 8)
        g2 = make_game([("scout", 17, 5)], [("scout", 0, 0)], p0_cmds=["charge"])
        self.give_points(g2, 0)
        g2.select_unit(uid_at(g2, 17, 5))
        g2.move_unit(14, 5)
        g2.use_command("charge", uid_at(g2, 14, 5))
        self.assertEqual(g2.moves_left, 3 + 6)

    def test_charge_not_allowed_after_movement_and_wears_off(self):
        g = make_game([("scout", 17, 5)], [("scout", 0, 0)], p0_cmds=["charge"])
        self.give_points(g, 0)
        g.select_unit(uid_at(g, 17, 5))
        g.end_phase()                                        # -> COMBAT
        self.assertIn("Charge", g.command_status(0, "charge"))
        g3 = make_game([("scout", 17, 5)], [("scout", 0, 0)], p0_cmds=["charge"])
        self.give_points(g3, 0)
        g3.use_command("charge", uid_at(g3, 17, 5))
        g3.end_turn()
        self.assertNotIn("charge", g3.unit_at(17, 5).effects)

    def test_winds_of_fate_resets_another_cooldown(self):
        g = make_game([("scout", 17, 5)], [("scout", 0, 0)], p0_cmds=["winds_of_fate", "charge"])
        self.give_points(g, 0)
        self.assertIsNotNone(g.command_status(0, "winds_of_fate"))   # nothing on cooldown yet
        g.cooldowns[0]["charge"] = 4
        g.use_command("winds_of_fate")
        self.assertEqual(g.cooldowns[0]["charge"], 0)
        self.assertEqual(g.cooldowns[0]["winds_of_fate"], 2)

    def test_wrong_target_kinds_rejected(self):
        g = make_game([("knight", 10, 5)], [("scout", 0, 0)], p0_cmds=["battle_cry", "bombard"])
        self.give_points(g, 0)
        with self.assertRaises(IllegalAction):
            g.use_command("battle_cry", uid_at(g, 0, 0))
        with self.assertRaises(IllegalAction):
            g.use_command("bombard", uid_at(g, 10, 5))
        with self.assertRaises(IllegalAction):
            g.use_command("battle_cry")

    def test_cannot_double_stack_a_buff(self):
        g = make_game([("knight", 10, 5)], [("scout", 0, 0)], p0_cmds=["battle_cry"])
        self.give_points(g, 0)
        k = g.unit_at(10, 5)
        g.use_command("battle_cry", k.uid)
        g.cooldowns[0]["battle_cry"] = 0
        with self.assertRaises(IllegalAction):
            g.use_command("battle_cry", k.uid)


class TurnFlowTests(unittest.TestCase):
    def test_phases_advance_and_turn_passes(self):
        # an enemy within reach keeps the combat phase alive, so every phase is visible
        g = make_game([("scout", 17, 5)], [("scout", 16, 5), ("scout", 0, 5)])
        self.assertEqual(g.phase, engine.SELECTION)
        g.select_unit(uid_at(g, 17, 5))
        self.assertEqual(g.phase, engine.MOVEMENT)
        g.end_phase()
        self.assertEqual(g.phase, engine.COMBAT)
        g.end_phase()
        self.assertEqual(g.phase, engine.RALLY)
        g.end_phase()
        self.assertEqual(g.current, 1)
        self.assertEqual(g.phase, engine.SELECTION)
        self.assertIsNone(g.selected)

    def test_skip_selection_goes_to_rally(self):
        g = make_game([("scout", 17, 5)], [("scout", 0, 5)])
        g.end_phase()
        self.assertEqual(g.phase, engine.RALLY)

    def test_command_points_accumulate_each_turn(self):
        g = make_game([("scout", 17, 5)], [("scout", 0, 5)])
        self.assertEqual(g.command_points, [25, 0])
        g.end_turn()
        self.assertEqual(g.command_points, [25, 25])
        g.end_turn()
        self.assertEqual(g.command_points, [50, 25])

    def test_resign(self):
        g = make_game([("scout", 17, 5)], [("scout", 0, 5)])
        g.resign(0)
        self.assertEqual(g.winner, 1)


class AutoAdvanceTests(unittest.TestCase):
    def test_movement_ends_by_itself_when_the_steps_run_out(self):
        g = make_game([("scout", 17, 5)], [("scout", 16, 9), ("scout", 0, 5)])
        g.select_unit(uid_at(g, 17, 5))
        g.move_unit(15, 5)                                   # 2 of 6 steps: still moving
        self.assertEqual(g.phase, engine.MOVEMENT)
        g.move_unit(15, 9)                                   # 4 more steps -> 0 left, enemy at (16,9) is adjacent
        self.assertEqual(g.moves_left, 0)
        self.assertEqual(g.phase, engine.COMBAT)

    def test_combat_is_skipped_when_nothing_is_in_range(self):
        g = make_game([("scout", 17, 5)], [("scout", 0, 5)])
        g.select_unit(uid_at(g, 17, 5))
        g.move_unit(11, 5)                                   # all 6 steps, nobody near
        self.assertEqual(g.phase, engine.RALLY)

    def test_ending_movement_early_also_skips_an_empty_combat(self):
        g = make_game([("scout", 17, 5)], [("scout", 0, 5)])
        g.select_unit(uid_at(g, 17, 5))
        g.end_phase()
        self.assertEqual(g.phase, engine.RALLY)

    def test_combat_waits_for_the_player_when_a_target_is_in_range(self):
        g = make_game([("knight", 10, 5)], [("foot_soldier", 9, 5), ("scout", 0, 0)])
        g.select_unit(uid_at(g, 10, 5))
        g.end_phase()
        self.assertEqual(g.phase, engine.COMBAT)

    def test_a_boxed_in_troop_skips_movement_straight_away(self):
        g = make_game([("scout", 10, 5)], [("scout", 0, 0)], obstacles=[(9, 5), (11, 5), (10, 4), (10, 6)])
        g.select_unit(uid_at(g, 10, 5))
        self.assertEqual(g.phase, engine.RALLY)              # no way out, nobody to hit

    def test_movement_waits_while_a_charge_could_still_help(self):
        g = make_game([("scout", 17, 5)], [("scout", 0, 5)], p0_cmds=["charge"])
        g.command_points[0] = 500
        g.select_unit(uid_at(g, 17, 5))
        g.move_unit(11, 5)                                   # steps spent, but Charge would give 6 more
        self.assertEqual(g.phase, engine.MOVEMENT)
        g.use_command("charge", uid_at(g, 11, 5))
        self.assertEqual(g.moves_left, 6)
        g.move_unit(5, 5)                                    # now truly out of steps
        self.assertNotEqual(g.phase, engine.MOVEMENT)

    def test_movement_does_not_wait_for_a_charge_the_player_cannot_use(self):
        for kwargs in (dict(p0_cmds=[]), dict(p0_cmds=["charge"])):
            g = make_game([("scout", 17, 5)], [("scout", 0, 5)], **kwargs)
            g.command_points[0] = 0                          # no command points either way
            g.select_unit(uid_at(g, 17, 5))
            g.move_unit(11, 5)
            self.assertEqual(g.phase, engine.RALLY, kwargs)

    def test_rally_never_ends_the_turn_by_itself(self):
        g = make_game([("scout", 17, 5)], [("scout", 0, 5)])
        g.select_unit(uid_at(g, 17, 5))
        g.move_unit(11, 5)
        self.assertEqual((g.phase, g.current), (engine.RALLY, 0))
        g.end_phase()
        self.assertEqual(g.current, 1)

    def test_selection_is_skipped_when_every_troop_is_chastised(self):
        g = make_game([("scout", 17, 5)], [("scout", 0, 5), ("scout", 0, 8)])
        for unit in g.units_of(1):
            unit.effects["chastise"] = 0                     # cast by player 0
        g.end_turn()                                         # player 1: nobody can act
        self.assertEqual((g.current, g.phase), (1, engine.RALLY))
        g.end_turn(); g.end_turn()                           # chastise wears off on player 0's next turn
        self.assertEqual(g.phase, engine.SELECTION)

    def test_attacking_still_goes_straight_to_rally(self):
        g = make_game([("foot_soldier", 10, 5), ("scout", 17, 0)], [("foot_soldier", 9, 5), ("scout", 0, 0)])
        g.select_unit(uid_at(g, 10, 5))
        g.attack(uid_at(g, 9, 5))
        self.assertEqual(g.phase, engine.RALLY)


class SerialisationTests(unittest.TestCase):
    def test_round_trip_through_json(self):
        import json
        lo = Loadout(troops=["scout", "knight", "archer"], commands=["charge", "battle_cry"])
        g = Game.new([lo, Loadout.from_dict(lo.to_dict())], rng=random.Random(7))
        g.command_points[0] = 500
        g.use_command("battle_cry", g.units_of(0)[0].uid)
        g.select_unit(g.units_of(0)[1].uid)
        snapshot = json.loads(json.dumps(g.to_dict()))
        self.assertEqual(Game.from_dict(snapshot).to_dict(), g.to_dict())

    def test_apply_action_enforces_turn_and_types(self):
        g = make_game([("scout", 17, 5)], [("scout", 0, 5)])
        with self.assertRaises(IllegalAction):
            g.apply_action(1, {"type": "select", "unit": uid_at(g, 0, 5)})   # not their turn
        with self.assertRaises(IllegalAction):
            g.apply_action(0, {"type": "select", "unit": [1]})                # junk type
        with self.assertRaises(IllegalAction):
            g.apply_action(0, {"type": "warp"})
        with self.assertRaises(IllegalAction):
            g.apply_action(0, "select")
        g.apply_action(0, {"type": "select", "unit": uid_at(g, 17, 5)})
        g.apply_action(0, {"type": "move", "row": 16, "col": 5})
        self.assertEqual(g.unit_at(16, 5).uid, 1)

    def test_resign_allowed_out_of_turn(self):
        g = make_game([("scout", 17, 5)], [("scout", 0, 5)])
        g.apply_action(1, {"type": "resign"})
        self.assertEqual(g.winner, 0)

    def test_illegal_actions_do_not_change_state(self):
        g = make_game([("knight", 10, 5)], [("scout", 0, 0)], p0_cmds=["bombard"])
        before = g.to_dict()
        for bad in ({"type": "command", "command": "bombard", "target": uid_at(g, 0, 0)},
                    {"type": "move", "row": 0, "col": 0},
                    {"type": "attack", "target": 99}):
            with self.assertRaises(IllegalAction):
                g.apply_action(0, bad)
        self.assertEqual(g.to_dict(), before)


class DataTests(unittest.TestCase):
    def test_every_command_has_the_fields_the_ui_needs(self):
        for key, spec in data.COMMANDS.items():
            for field in ("name", "cost", "cooldown", "target", "text", "icon"):
                self.assertIn(field, spec, key)
            self.assertIn(spec["target"], ("ally", "enemy", "none"))

    def test_champion_health_matches_wiki(self):
        self.assertEqual(data.TROOPS["champion"]["health"], 500)


if __name__ == "__main__":
    unittest.main()
