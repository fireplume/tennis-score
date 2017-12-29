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

        self.assertEqual(self.tennis_league.get_league_average_points_per_match(LeagueIndex(-1), PlayingEntity.PlayType.SINGLES), 5.0)

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


if __name__ == "__main__":
    unittest.main()
