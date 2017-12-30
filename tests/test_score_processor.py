#!/usr/bin/env python3

import unittest
import os
import sys
import importlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
utils = importlib.import_module("utils")
interfaces = importlib.import_module("interfaces")
score = importlib.import_module("score")
League = importlib.import_module("League")

from interfaces import *


CSV = os.path.join(os.path.dirname(__file__), 'score-processor.csv')


class TestScoreProcessor(unittest.TestCase):

    def setUp(self):
        # Make sure type checking is enabled
        utils.utils.Accepts.enable()
        # read test csv
        args = score.parse_command_line(['input_csv', CSV, '-i'])
        if League.League._SINGLETON is not None:
            del League.League._SINGLETON
            League.League._SINGLETON = None
        self.tennis_league = score.main(args)
        self.test_indexes = [LeagueIndex(3), LeagueIndex(6), LeagueIndex(7), LeagueIndex(9), LeagueIndex(-1), PlayerIndex(1), PlayerIndex(2), PlayerIndex(-1)]

    def test_ranking(self):
        for league_index in self.test_indexes:
            with self.subTest(str(league_index)):
                player_a = self.tennis_league.get_playing_entity('player_a')
                player_b = self.tennis_league.get_playing_entity('player_b')
                player_c = self.tennis_league.get_playing_entity('player_c')
                player_d = self.tennis_league.get_playing_entity('player_d')
                player_e = self.tennis_league.get_playing_entity('player_e')
                player_f = self.tennis_league.get_playing_entity('player_f')

                self.assertEqual(player_a.get_ranking(league_index), 1)
                self.assertEqual(player_b.get_ranking(league_index), 2)
                self.assertEqual(player_c.get_ranking(league_index), 3)
                self.assertEqual(player_d.get_ranking(league_index), 4)
                self.assertEqual(player_e.get_ranking(league_index), 4)
                self.assertEqual(player_f.get_ranking(league_index), 4)

    def test_average_points_per_match(self):
        for league_index in self.test_indexes:
            with self.subTest(str(league_index)):
                player_a = self.tennis_league.get_playing_entity('player_a')
                player_b = self.tennis_league.get_playing_entity('player_b')
                player_c = self.tennis_league.get_playing_entity('player_c')
                player_d = self.tennis_league.get_playing_entity('player_d')
                player_e = self.tennis_league.get_playing_entity('player_e')
                player_f = self.tennis_league.get_playing_entity('player_f')

                self.assertEqual(player_a.get_average_points_per_match(league_index), 10.0)
                self.assertEqual(player_b.get_average_points_per_match(league_index), 7.5)
                self.assertEqual(player_c.get_average_points_per_match(league_index), 2.5)
                self.assertEqual(player_d.get_average_points_per_match(league_index), 0.0)
                self.assertEqual(player_e.get_average_points_per_match(league_index), 0.0)
                self.assertEqual(player_f.get_average_points_per_match(league_index), 0.0)

    def test_get_match_points(self):
        """
        player_a: league_index == 1,3,5
        player_b: league_index == 2,4,6
        player_c: league_index == 2,4,6
        player_d: league_index == 1,3,5
        player_e: league_index == 7,8
        player_f: league_index == 7,8

        LeagueIndex(3), LeagueIndex(6), LeagueIndex(7), LeagueIndex(9), LeagueIndex(-1), PlayerIndex(1), PlayerIndex(2), PlayerIndex(-1)
        """

        expected_exceptions_ad = [LeagueIndex(6), LeagueIndex(7), LeagueIndex(9)]
        expected_exceptions_bc = [LeagueIndex(3), LeagueIndex(7), LeagueIndex(9)]
        expected_exceptions_ef = [LeagueIndex(3), LeagueIndex(6), LeagueIndex(9)]

        for league_index in self.test_indexes:
            with self.subTest(str(league_index)):
                player_a = self.tennis_league.get_playing_entity('player_a')
                player_b = self.tennis_league.get_playing_entity('player_b')
                player_c = self.tennis_league.get_playing_entity('player_c')
                player_d = self.tennis_league.get_playing_entity('player_d')
                player_e = self.tennis_league.get_playing_entity('player_e')
                player_f = self.tennis_league.get_playing_entity('player_f')

                if league_index in expected_exceptions_ad:
                    with self.assertRaises(SmartIndexError):
                        player_a.get_match_points(league_index)
                    with self.assertRaises(SmartIndexError):
                        player_d.get_match_points(league_index)
                else:
                    self.assertEqual(player_a.get_match_points(league_index), 10.0)
                    self.assertEqual(player_d.get_match_points(league_index), 0.0)

                if league_index in expected_exceptions_bc:
                    with self.assertRaises(SmartIndexError):
                        player_b.get_match_points(league_index)
                    with self.assertRaises(SmartIndexError):
                        player_c.get_match_points(league_index)
                else:
                    self.assertEqual(player_b.get_match_points(league_index), 7.5)
                    self.assertEqual(player_c.get_match_points(league_index), 2.5)

                if league_index in expected_exceptions_ef:
                    with self.assertRaises(SmartIndexError):
                        player_e.get_match_points(league_index)
                    with self.assertRaises(SmartIndexError):
                        player_f.get_match_points(league_index)
                else:
                    self.assertEqual(player_e.get_match_points(league_index), 0.0)
                    self.assertEqual(player_f.get_match_points(league_index), 0.0)


if __name__ == "__main__":
    unittest.main()
