#!/usr/bin/env python3

import unittest
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import *


class BaseClass:
    pass


class SubClass1(BaseClass):
    pass


class SubClass2(SubClass1):
    pass


class UnknownClass:
    pass


class B:
    @parameter_type_checking(int, str, c=BaseClass, d=SubClass1, e=float)
    def some_function(self, a:int, b:str, c:BaseClass(), d=SubClass1(), e=1.0):
        pass


class TestUtils(unittest.TestCase):

    def test_parameter_type_checking(self):
        my_class = B()

        # proper function call should work
        my_class.some_function(0, 'a', c=BaseClass(), d=SubClass1(), e=1.0)
        my_class.some_function(0, 'a', c=BaseClass())
        my_class.some_function(0, 'a', c=BaseClass(), e=1.0, d=SubClass1())

        with self.assertRaises(TypeError):
            my_class.some_function('a', 'a', c=BaseClass(), d=SubClass1(), e=1.0)

        with self.assertRaises(TypeError):
            my_class.some_function(0, '0', c=BaseClass(), d=BaseClass(), e=1.0)

        with self.assertRaises(TypeError):
            my_class.some_function(0, 'a', c=UnknownClass(), d=SubClass1())

        with self.assertRaises(TypeError):
            my_class.some_function(0, 'a', c=BaseClass(), d=SubClass2(), e="4.0")

        with self.assertRaises(TypeError):
            my_class.some_function(0, 'a', c=BaseClass(), e=1)

        with self.assertRaises(TypeError):
            my_class.some_function(0, 'a', c=BaseClass(), d=SubClass1(), e=2)

if __name__ == "__main__":
    unittest.main()
