#!/usr/bin/env python3

import unittest
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Stats import *


class TestStats(unittest.TestCase):

    def test_stat_index(self):
        for o in [PlayerIndex(1), LeagueIndex(1)]:
            o += 1

            self.assertEqual(int(o), type(o)(2))
            self.assertEqual(o, type(o)(2))
            self.assertEqual(o, int(type(o)(2)))
            self.assertEqual(int(o), int(type(o)(2)))
            self.assertTrue(o > -1)

        with self.assertRaises(ValueError):
            PlayerIndex(0)

        with self.assertRaises(ValueError):
            PlayerIndex(-2)

        with self.assertRaises(TypeError):
            PlayerIndex('a')

        with self.assertRaises(TypeError):
            PlayerIndex(1.0)

    def test_stat_index_hashing(self):
        s = set()
        s.add(PlayerIndex(1))
        s.add(PlayerIndex(1))
        self.assertTrue(len(s) == 1)

        s.add(PlayerIndex(2))
        self.assertTrue(len(s) == 2)

        s.add(LeagueIndex(2))
        self.assertTrue(len(s) == 3)

        indexes = set([PlayerIndex(4), PlayerIndex(1), LeagueIndex(2), LeagueIndex(3)])
        m = max(indexes)
        self.assertTrue(m == PlayerIndex(4))

        p = PlayerIndex(99)
        for i in range(0, 1000):
            hash_challenge = PlayerIndex(99)
            self.assertTrue(p.__hash__() == hash_challenge.__hash__())

    @staticmethod
    def _setup_test_stats():
        stats = Stats()
        stats.set_match_results(6, 3, LeagueIndex(5))
        stats.set_match_points(3, LeagueIndex(5))
        return stats

    def test_set_points_no_match(self):
        stats = Stats()

        # Check we can't set points before setting a match
        with self.assertRaises(InitError):
            stats.set_match_points(5, LeagueIndex(5))

    def test_add_match_results(self):
        stats = Stats()

        with self.assertRaises(TypeError):
            stats.set_match_results(6, 3, 'a')
        with self.assertRaises(TypeError):
            stats.set_match_results(6, 3, '1.0')
        stats.set_match_results(6, 3, LeagueIndex(5))

    def test_overwrite_results(self):
        stats = Stats()
        stats.set_match_results(6, 3, LeagueIndex(5))

        # Assert error on overwrite
        with self.assertRaises(OverwriteError):
            stats.set_match_results(6, 3, LeagueIndex(5))

    def test_set_points(self):
        stats = Stats()
        stats.set_match_results(6, 3, LeagueIndex(5))

        with self.assertRaises(TypeError):
            stats.set_match_points(6, 3, 'a')
        with self.assertRaises(TypeError):
            stats.set_match_points(6, 3, '1.0')

        # Set points earned for match
        stats.set_match_points(3, LeagueIndex(5))

    def test_overwrite_points(self):
        stats = self._setup_test_stats()

        # Assert error on overwrite
        with self.assertRaises(OverwriteError):
            stats.set_match_points(3, LeagueIndex(5))

    def test_get_match_played(self):
        stats = self._setup_test_stats()

        self.assertTrue(stats.get_index_number_of_match_played(index=LeagueIndex(-1)) == PlayerIndex(1))
        self.assertTrue(stats.get_index_number_of_match_played(index=LeagueIndex(5)) == PlayerIndex(1))
        self.assertTrue(stats.get_index_number_of_match_played(index=LeagueIndex(5)) ==
                        stats.get_index_number_of_match_played(index=PlayerIndex(1)))

        with self.assertRaises(KeyError):
            stats.get_index_number_of_match_played(LeagueIndex(5))
        with self.assertRaises(TypeError):
            stats.get_index_number_of_match_played(index=5)

    def test_setting_results_in_the_past(self):
        stats = self._setup_test_stats()

        with self.assertRaises(BackToTheFutureError):
            stats.set_match_results(6, 3, LeagueIndex(3))

    def test_get_point_for_match(self):
        stats = self._setup_test_stats()

        self.assertTrue(stats.get_points_for_match(index=LeagueIndex(5)) ==
                        stats.get_points_for_match(index=PlayerIndex(1)))

        self.assertTrue(stats.get_points_for_match(index=LeagueIndex(5)) == 3)

        with self.assertRaises(KeyError):
            stats.get_points_for_match(index=LeagueIndex(3))

        with self.assertRaises(KeyError):
            stats.get_points_for_match(index=LeagueIndex(99))

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
        stats.set_match_points(2, LeagueIndex(8))

        stats.set_match_results(5, 8, LeagueIndex(12))
        stats.set_match_points(-3, LeagueIndex(12))

        avg_pts_per_game_as_of_match_3 = stats.get_average_points_per_game_won(index=LeagueIndex(12))
        self.assertTrue(avg_pts_per_game_as_of_match_3 == float(2)/14)

        # As of match 1
        points_as_of_match_1 = stats.get_cumulative_games_points(index=PlayerIndex(1))
        self.assertTrue(points_as_of_match_1 == 3.0)

        games_won_as_of_match_1 = stats.get_cumulative_games_won(index=LeagueIndex(5))
        self.assertTrue(games_won_as_of_match_1 == 6)

        games_lost_as_of_match_1 = stats.get_cumulative_games_lost(index=LeagueIndex(5))
        self.assertTrue(games_lost_as_of_match_1 == 3)

        avg_pts_per_match_as_of_match_1 = stats.get_average_points_per_match(index=LeagueIndex(5))
        self.assertTrue(avg_pts_per_match_as_of_match_1 == 3.0)

        avg_pts_per_game_as_of_match_1 = stats.get_average_points_per_game_won(index=LeagueIndex(5))
        self.assertTrue(avg_pts_per_game_as_of_match_1 == 0.5)

        ######################################
        # As of last match
        points_as_of_match_3 = stats.get_cumulative_games_points(index=PlayerIndex(-1))
        self.assertTrue(points_as_of_match_3 == 2.0)

        games_won_as_of_match_3 = stats.get_cumulative_games_won(index=LeagueIndex(-1))
        self.assertTrue(games_won_as_of_match_3 == 14)

        games_lost_as_of_match_3 = stats.get_cumulative_games_lost(index=LeagueIndex(12))
        self.assertTrue(games_lost_as_of_match_3 == 12)

        avg_pts_per_match_as_of_match_3 = stats.get_average_points_per_match(index=PlayerIndex(3))
        self.assertTrue(0.6666 <= avg_pts_per_match_as_of_match_3 <= 0.6667)

        avg_pts_per_game_as_of_match_3 = stats.get_average_points_per_game_won(index=LeagueIndex(12))
        self.assertTrue(avg_pts_per_game_as_of_match_3 == float(2)/14)


if __name__ == "__main__":
    unittest.main()
