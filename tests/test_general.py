#!/usr/bin/env python3

import unittest
import os
import sys
import importlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
utils = importlib.import_module("utils")
score = importlib.import_module("score")
interfaces = importlib.import_module("interfaces")

from interfaces import *

CSV = os.path.join(os.path.dirname(__file__), 'league-avg-ppm.csv')


class TestGeneral(unittest.TestCase):
    def setUp(self):
        # Make sure type checking is enabled
        utils.utils.Accepts.enable()

    def test_league_average_ppm(self):
        # read test csv
        args = score.parse_command_line(['input_csv', CSV, '-i'])
        tennis_league = score.main(args)

        self.assertEqual(tennis_league.get_league_average_points_per_match(LeagueIndex(-1), PlayingEntity.PlayType.SINGLES), 5.0)


if __name__ == "__main__":
    unittest.main()
