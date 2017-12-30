#!/usr/bin/env python3

import unittest
import os
import sys
import importlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
utils = importlib.import_module("utils")
score = importlib.import_module("score")
interfaces = importlib.import_module("interfaces")
League = importlib.import_module("League")
Player = importlib.import_module("Player")
DoublesTeam = importlib.import_module("DoublesTeam")
Game = importlib.import_module("Game")

from interfaces import *

CSV = os.path.join(os.path.dirname(__file__), 'league-avg-ppm.csv')


class TestGeneral(unittest.TestCase):
    def setUp(self):
        # Make sure type checking is enabled
        utils.utils.Accepts.enable()
        args = score.parse_command_line(['input_csv', CSV, '-i'])
        if League.League._SINGLETON is not None:
            del League.League._SINGLETON
            League.League._SINGLETON = None
        self.tennis_league = score.main(args)

    def test_league_average_ppm(self):
        # read test csv

        avg = self.tennis_league.get_league_average_points_per_match(LeagueIndex(-1), PlayingEntity.PlayType.SINGLES)
        self.assertEqual(round(avg,2), 5.0)

    def test_playing_entity_smart_index_error(self):
        entity = self.tennis_league.get_playing_entity("player_a")
        with self.assertRaises(SmartIndexError):
            entity.set_match_points(LeagueIndex(99), 1.0)

    def test_playing_entity_empty(self):
        p = Player.Player("foo", 1.0, 0.0)

        with self.assertRaises(ValueError):
            p.set_rank(LeagueIndex(1), 0)

        self.assertEqual(p.get_cumulative_games_won(LeagueIndex(1)), 0)
        self.assertEqual(p.get_cumulative_games_lost(LeagueIndex(1)), 0)
        self.assertEqual(p.get_cumulative_points(LeagueIndex(1)), 0.0)
        self.assertEqual(p.get_average_points_per_match(LeagueIndex(1)), 0.0)
        self.assertEqual(p.get_match_points(LeagueIndex(1)), 0.0)

    def test_aussie_match(self):
        pb = self.tennis_league.get_playing_entity("player_b")
        pc = self.tennis_league.get_playing_entity("player_c")
        d = DoublesTeam.DoublesTeam(pb, pc, 1.0, 1.0)
        self.tennis_league.add_playing_entity(d)
        with self.assertRaises(AussieException):
            Game.Game("player_a", 0, PlayingEntity.DOUBLES_NAME_FORMAT.format("player_b", "player_c"), 0)

    def test_singles_play_yourself(self):
        with self.assertRaises(PlayingAgainstSelf):
            Game.Game("player_a", 0, "player_a", 0)

    def test_doubles_play_yourself(self):
        pa = self.tennis_league.get_playing_entity("player_a")
        pb = self.tennis_league.get_playing_entity("player_b")
        pc = self.tennis_league.get_playing_entity("player_c")

        d = DoublesTeam.DoublesTeam(pa, pb, 1.0, 1.0)
        self.tennis_league.add_playing_entity(d)

        d = DoublesTeam.DoublesTeam(pb, pc, 1.0, 1.0)
        self.tennis_league.add_playing_entity(d)

        with self.assertRaises(PlayingAgainstSelf):
            Game.Game(PlayingEntity.DOUBLES_NAME_FORMAT.format("player_a", "player_b"), 0,
                      PlayingEntity.DOUBLES_NAME_FORMAT.format("player_b", "player_c"), 0)


if __name__ == "__main__":
    unittest.main()
