#!/usr/bin/env python3
import unittest
import os
import sys
import importlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
importlib.import_module("utils")

from utils.SmartIndex import *
import utils.utils as utils


class TestSmartIndex(unittest.TestCase):

    def setUp(self):
        # Make sure type checking is enabled
        utils.Accepts.enable()

    def __index_operator_tests(self, i2: SmartIndex, i3: int, expected_results: dict):
        for i1_operator in expected_results:
            expected = expected_results[i1_operator]
            self.assertEqual(i1_operator(i2), expected)
            self.assertEqual(i1_operator(i3), expected)

    def test_stat_operators(self):
        expected_results = dict()
        i1 = PlayerIndex(1)
        i2 = LeagueIndex(1)
        i3 = 1
        expected_results[i1.__gt__] = False
        expected_results[i1.__lt__] = False
        expected_results[i1.__ge__] = True
        expected_results[i1.__le__] = True
        expected_results[i1.__eq__] = True
        expected_results[i1.__ne__] = False
        self.__index_operator_tests(i2, i3, expected_results)

        i1 += 1
        expected_results[i1.__gt__] = True
        expected_results[i1.__lt__] = False
        expected_results[i1.__ge__] = True
        expected_results[i1.__le__] = False
        expected_results[i1.__eq__] = False
        expected_results[i1.__ne__] = True
        self.__index_operator_tests(i2, i3, expected_results)

        i2 += 2
        i3 += 2
        expected_results[i1.__gt__] = False
        expected_results[i1.__lt__] = True
        expected_results[i1.__ge__] = False
        expected_results[i1.__le__] = True
        expected_results[i1.__eq__] = False
        expected_results[i1.__ne__] = True
        self.__index_operator_tests(i2, i3, expected_results)

        with self.assertRaises(TypeError):
            i1 + i2

        with self.assertRaises(TypeError):
            i1 *= 1

        with self.assertRaises(TypeError):
            i1 /= 2

    def test_not_implemented(self):
        i1 = LeagueIndex(1)

        with self.assertRaises(NotImplementedError):
            i1 > 'a'
        with self.assertRaises(NotImplementedError):
            i1 < 'a'
        with self.assertRaises(NotImplementedError):
            i1 >= 'a'
        with self.assertRaises(NotImplementedError):
            i1 <= 'a'
        with self.assertRaises(NotImplementedError):
            i1 == 'a'
        with self.assertRaises(NotImplementedError):
            i1 != 'a'

    def test_locked_index(self):
        i1 = PlayerIndex(1)
        i1_locked = PlayerIndex(1, locked=True)

        i1 += 2

        i1.lock()
        with self.assertRaises(ReadOnlyDataError):
            i1 += 1

        with self.assertRaises(ReadOnlyDataError):
            i1_locked += 1

        i2 = i1.get_unlocked_copy()
        i2 += 1

        i3_locked = i2.get_locked_copy()
        with self.assertRaises(ReadOnlyDataError):
            i3_locked += 1

    def test_stat_index(self):
        for o in [PlayerIndex(1), LeagueIndex(1)]:
            o += 1

            self.assertEqual(int(o), type(o)(2))
            self.assertEqual(o, type(o)(2))
            self.assertEqual(o, int(type(o)(2)))
            self.assertEqual(int(o), int(type(o)(2)))
            self.assertTrue(o > -1)

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

            wrong_hash = PlayerIndex(100+i)
            self.assertTrue(p.__hash__() != wrong_hash.__hash__())

    def test_empty_cache(self):
        cache = SmartIndexCache()

        with self.assertRaises(SmartIndexError):
            cache.max_index(IndexType.LEAGUE)

        self.assertFalse(cache.exists(LeagueIndex(0)))
        self.assertFalse(cache.exists(LeagueIndex(-1)))
        self.assertFalse(cache.exists(LeagueIndex(1)))
        self.assertFalse(cache.exists(PlayerIndex(0)))
        self.assertFalse(cache.exists(PlayerIndex(-1)))
        self.assertFalse(cache.exists(PlayerIndex(1)))

        self.assertEqual(cache.number_of_indexes(IndexType.PLAYER), 0)
        self.assertEqual(cache.number_of_indexes(IndexType.LEAGUE), 0)

        # TODO
        # self.assertEqual(cache.get_latest_valid_index(), 0)


if __name__ == "__main__":
    unittest.main()
