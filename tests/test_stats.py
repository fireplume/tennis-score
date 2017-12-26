#!/usr/bin/env python3

import unittest
import os
import sys
import importlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
importlib.import_module("utils")
importlib.import_module("Stats")

from Stats import *
from utils.SmartIndex import *
import utils.utils as utils


class TestStats(unittest.TestCase):

    def setUp(self):
        # Make sure type checking is enabled
        utils.Accepts.enable()

    @staticmethod
    def _setup_test_stats():
        stats = Stats(0.0, 1.0)
        index5 = LeagueIndex(5)
        stats.set_match_results(6, 3, index5)
        stats.set_data('match_points', 3.0, index5)

        # Try to corrupt internal data structure by incrementing index5 reference
        for i in range(0, 100):
            index5 += 1

        return stats

    def test_create_wrong_stats_data(self):
        with self.assertRaises(TypeError):
            StatsData("wrong_type", str)

    def test_dont_use_index_keyword(self):
        stats = self._setup_test_stats()
        with self.assertRaises(MissingIndexError):
            # Need to disable signature check for this one
            utils.Accepts.disable()
            stats.get_number_of_match_played_by_league_index_time(LeagueIndex(5))
        utils.Accepts.enable()

    def test_dont_use_wrong_index_type(self):
        stats = self._setup_test_stats()
        with self.assertRaises(TypeError):
            # Need to disable signature check for this one
            utils.Accepts.disable()
            stats.get_number_of_match_played_by_league_index_time(index=5)
        utils.Accepts.enable()

    def test_set_points_no_match(self):
        stats = Stats(initial_points=0.0, initial_level=1.0)

        # Check we can't set points before setting a match
        with self.assertRaises(NoMatchPlayedYetError):
            stats.set_data('match_points', 5.0, LeagueIndex(5))

    def test_add_match_results(self):
        stats = Stats(initial_points=0.0, initial_level=1.0)

        with self.assertRaises(TypeError):
            stats.set_match_results(6, 3, 'a')
        with self.assertRaises(TypeError):
            stats.set_match_results(6, 3, '1.0')
        stats.set_match_results(6, 3, LeagueIndex(5))

    def test_overwrite_results(self):
        stats = Stats(initial_points=0.0, initial_level=1.0)
        stats.set_match_results(6, 3, LeagueIndex(5))

        # Assert error on overwrite
        with self.assertRaises(OverwriteError):
            stats.set_match_results(6, 3, LeagueIndex(5))

    def test_set_points(self):
        stats = Stats(initial_points=0.0, initial_level=1.0)
        stats.set_match_results(6, 3, LeagueIndex(5))

        with self.assertRaises(TypeError):
            stats.set_data('match_points', 6.0, 'a')
        with self.assertRaises(TypeError):
            stats.set_data('match_points', 6.0, '1.0')

        # Set points earned for match
        stats.set_data('match_points', 3.0, LeagueIndex(5))

    def test_overwrite_points(self):
        stats = self._setup_test_stats()

        # Assert error on overwrite
        with self.assertRaises(OverwriteError):
            stats.set_data('match_points', 3.0, LeagueIndex(5))

        stats.set_data('ranking', 1, LeagueIndex(5))
        with self.assertRaises(OverwriteError):
            stats.set_data('ranking', 1, LeagueIndex(5))

        stats.reset_data('ranking')
        stats.set_data('ranking', 1, LeagueIndex(5))

    def test_get_match_played(self):
        stats = self._setup_test_stats()

        self.assertTrue(stats.get_number_of_match_played_by_league_index_time(index=LeagueIndex(-1)) == PlayerIndex(1))
        self.assertTrue(stats.get_number_of_match_played_by_league_index_time(index=LeagueIndex(5)) == PlayerIndex(1))
        self.assertTrue(stats.get_number_of_match_played_by_league_index_time(index=LeagueIndex(5)) ==
                        stats.get_number_of_match_played_by_league_index_time(index=PlayerIndex(1)))

        with self.assertRaises(MissingIndexError):
            stats.get_number_of_match_played_by_league_index_time(LeagueIndex(5))
        with self.assertRaises(TypeError):
            stats.get_number_of_match_played_by_league_index_time(index=5)

    def test_setting_results_in_the_past(self):
        stats = self._setup_test_stats()

        with self.assertRaises(BackToTheFutureError):
            stats.set_match_results(6, 3, LeagueIndex(3))

    def test_get_point_for_match(self):
        stats = self._setup_test_stats()

        self.assertTrue(stats.get_data_for_index('match_points', index=LeagueIndex(5)) ==
                        stats.get_data_for_index('match_points', index=PlayerIndex(1)))

        self.assertTrue(stats.get_data_for_index('match_points', index=LeagueIndex(5)) == 3)

        with self.assertRaises(SmartIndexError):
            stats.get_data_for_index('match_points', index=LeagueIndex(3))

        with self.assertRaises(SmartIndexError):
            stats.get_data_for_index('match_points', index=LeagueIndex(99))

    def test_set_wrong_data_type(self):
        stats = self._setup_test_stats()
        with self.assertRaises(TypeError):
            stats.set_data('match_points', "win!", LeagueIndex(5))

    def test_get_wrong_index(self):
        stats = self._setup_test_stats()
        with self.assertRaises(SmartIndexError):
            stats.get_data_for_index('match_points', index=LeagueIndex(15))

    def test_get_stats(self):
        """
        There are 3 matches set with points in this function
            league index  5: 6 - 3,  3 pts
            league index  8: 3 - 1,  2 pts
            league index 12: 5 - 8, -3 pts
        """
        stats = self._setup_test_stats()

        # add more results
        stats.set_match_results(3, 1, LeagueIndex(8))
        stats.set_data('match_points', 2.0, LeagueIndex(8))

        stats.set_match_results(5, 8, LeagueIndex(12))
        stats.set_data('match_points', -3.0, LeagueIndex(12))

        # As of match 1
        points_as_of_match_1 = stats.get_cumulative_data_sum_for_index('match_points', index=PlayerIndex(1))
        self.assertTrue(points_as_of_match_1 == 3.0)

        games_won_as_of_match_1 = stats.get_cumulative_data_sum_for_index('games_won', index=LeagueIndex(5))
        self.assertTrue(games_won_as_of_match_1 == 6)

        games_lost_as_of_match_1 = stats.get_cumulative_data_sum_for_index('games_lost', index=LeagueIndex(5))
        self.assertTrue(games_lost_as_of_match_1 == 3)

        avg_pts_per_match_as_of_match_1 = stats.get_average_points_per_match(index=LeagueIndex(5))
        self.assertTrue(avg_pts_per_match_as_of_match_1 == 3.0)

        self.assertEqual(stats.get_data_for_index('games_won', index=PlayerIndex(1)), 6)

        ######################################
        # As of last match
        points_as_of_match_3 = stats.get_cumulative_data_sum_for_index('match_points', index=PlayerIndex(-1))
        self.assertTrue(points_as_of_match_3 == 2.0)

        games_won_as_of_match_3 = stats.get_cumulative_data_sum_for_index('games_won', index=LeagueIndex(-1))
        self.assertTrue(games_won_as_of_match_3 == 14)

        games_lost_as_of_match_3 = stats.get_cumulative_data_sum_for_index('games_lost', index=LeagueIndex(12))
        self.assertTrue(games_lost_as_of_match_3 == 12)

        avg_pts_per_match_as_of_match_3 = stats.get_average_points_per_match(index=PlayerIndex(3))
        self.assertTrue(0.6666 <= avg_pts_per_match_as_of_match_3 <= 0.6667)

    def test_initial_points(self):
        index_5 = LeagueIndex(5)
        stats = Stats(initial_points=6.66, initial_level=1.0)
        stats.set_match_results(6, 3, index_5)
        stats.set_data('match_points', 3.0, index_5)

        # Try to corrupt index reference
        index_5 += 10

        self.assertEqual(stats.get_initial_data('match_points'), 6.66)
        self.assertEqual(stats.get_average_points_per_match(index=PlayerIndex(-1)), 9.66)
        self.assertEqual(stats.get_cumulative_data_sum_for_index('match_points', index=PlayerIndex(-1)), 9.66)
        self.assertEqual(stats.get_data_for_index('match_points', index=PlayerIndex(-1)), 3.0)
        self.assertEqual(stats.get_data_for_index('match_points', index=LeagueIndex(5)), 3.0)

    def test_minus_1_index(self):
        i = LeagueIndex(-1)
        i += 1
        self.assertEqual(i, 0)
        i += 1
        self.assertEqual(i, 1)

    def test_empty_stats(self):
        stats = Stats(0.0, 1.0)

        with self.assertRaises(NoMatchPlayedYetError):
            stats.get_index_for_type(PlayerIndex(10), IndexType.LEAGUE)

        with self.assertRaises(NoMatchPlayedYetError):
            stats.get_index_for_type(LeagueIndex(10), IndexType.PLAYER)

        indexes = []
        for i in [-1, 1, 10]:
            indexes.append(PlayerIndex(i))
            indexes.append(LeagueIndex(i))

        for i in indexes:
            with self.assertRaises(NoMatchPlayedYetError):
                self.assertEqual(stats.get_number_of_match_played_by_league_index_time(index=i), 0)

            with self.assertRaises(NoMatchPlayedYetError):
                stats.get_data_for_index('match_points', index=i)

            with self.assertRaises(NoMatchPlayedYetError):
                stats.get_cumulative_data_sum_for_index('match_points', index=i)

            with self.assertRaises(NoMatchPlayedYetError):
                stats.get_cumulative_data_sum_for_index('games_won', index=i)

            with self.assertRaises(NoMatchPlayedYetError):
                stats.get_cumulative_data_sum_for_index('games_lost', index=i)

            with self.assertRaises(NoMatchPlayedYetError):
                stats.get_average_points_per_match(index=i)


if __name__ == "__main__":
    unittest.main()
