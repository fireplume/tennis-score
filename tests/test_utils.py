#!/usr/bin/env python3

import unittest
import os
import sys
import importlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
utils = importlib.import_module("utils")
from utils.utils import *


class BaseClass:
    @Accepts.accepts(object, float)
    def __init__(self, v):
        self._v = v

    def get(self):
        return self._v


class SubClass1(BaseClass):
    def __init__(self, v):
        super(SubClass1, self).__init__(v)


class SubClass2(SubClass1):
    def __init__(self, v):
        super(SubClass2, self).__init__(v)


class UnknownClass:
    def __init__(self, v):
        self._v = v

    def get(self):
        return self._v


# Setting a format error exception to distinguish between Accepts and string formatting TypeErrors
class FormatError(Exception):
    pass


class B(BaseClass):
    v = 7

    @Accepts.accepts(object, BaseClass, str, int, SubClass1, float, a=BaseClass, b=str, c=int, d=SubClass1, e=float)
    def some_function(self, a: BaseClass, b: str, c: int, d=SubClass1(0.0), e=1.0):
        try:
            return "self: %1.1f %1.1f %s %d %1.1f %1.1f" % (self.get(), a.get(), b, c, d.get(), e)
        except TypeError:
            raise FormatError("type error")

    @staticmethod
    @Accepts.accepts(BaseClass, str, int, SubClass1, float, a=BaseClass, b=str, c=int, d=SubClass1, e=float)
    def static_method(a: BaseClass, b: str, c: int, d=SubClass1(0.0), e=1.0):
        try:
            return "static: %1.1f %s %d %1.1f %1.1f" % (a.get(), b, c, d.get(), e)
        except TypeError:
            raise FormatError("type error")

    @classmethod
    @Accepts.accepts(type, BaseClass, str, int, SubClass1, float, a=BaseClass, b=str, c=int, d=SubClass1, e=float)
    def class_method(cls, a: BaseClass, b: str, c: int, d=SubClass1(0.0), e=1.0):
        try:
            return "class: %d %1.1f %s %d %1.1f %1.1f" % (cls.v, a.get(), b, c, d.get(), e)
        except TypeError:
            raise FormatError("type error")


@Accepts.accepts(BaseClass, str, int, SubClass1, float, a=BaseClass, b=str, c=int, d=SubClass1, e=float)
def no_self_function(a: BaseClass, b: str, c: int, d=SubClass1(0.0), e=1.0):
    return "no_self: %1.1f %s %d %1.1f %1.1f" % (a.get(), b, c, d.get(), e)


class TestUtilsTypeChecker(unittest.TestCase):

    def _check_proper_usage(self, my_class):
        # Some function with subclass parameters for parameter 'a'
        self.assertEqual(my_class.some_function(BaseClass(0.0), "hello", 1, d=SubClass1(2.0), e=3.0),
                         "self: 3.0 0.0 hello 1 2.0 3.0")

        self.assertEqual(my_class.some_function(SubClass1(0.0), "hello", 1, d=SubClass1(2.0), e=3.0),
                         "self: 3.0 0.0 hello 1 2.0 3.0")

        self.assertEqual(my_class.some_function(SubClass2(0.0), "hello", 1, d=SubClass1(2.0), e=3.0),
                         "self: 3.0 0.0 hello 1 2.0 3.0")

        # Static function
        self.assertEqual(my_class.static_method(SubClass1(0.0), "hello", 1, d=SubClass1(2.0), e=3.0),
                         "static: 0.0 hello 1 2.0 3.0")

        # Class function
        self.assertEqual(B.class_method(SubClass2(0.0), "hello", 1, d=SubClass1(2.0), e=3.0),
                         "class: 7 0.0 hello 1 2.0 3.0")

        # Regular function
        self.assertEqual(no_self_function(SubClass1(0.0), "hello", 1, d=SubClass1(2.0), e=3.0),
                         "no_self: 0.0 hello 1 2.0 3.0")

    def _check_wrong_usage(self, my_class, expected_exception):
        # 'd' parameter SubClass1's internal formatter expects a float, not a string
        with self.assertRaises(expected_exception):
            my_class.some_function(BaseClass(0.0), "hello", 1, d=SubClass1('a'), e=3.0)

        # 'e' parameter expects a float but is given a SubClass1 with a string as value
        with self.assertRaises(expected_exception):
            my_class.some_function(SubClass1(0.0), "hello", 1, d=SubClass1(2.0), e=SubClass1('hello'))

        # This normally would trigger an exception, but not if Accepts' type checking is disabled
        # 'd' parameter normally expects a SubClass1 parameter, but without the type checking
        # decorator enabled, it just goes through unnoticed.
        if Accepts.is_enabled():
            with self.assertRaises(TypeError):
                my_class.some_function(SubClass2(0.0), "hello", 1, d=UnknownClass(2.0), e=3.0)
        else:
            my_class.some_function(SubClass2(0.0), "hello", 1, d=UnknownClass(2.0), e=3.0)

            with self.assertRaises(FormatError):
                my_class.some_function(SubClass2(0.0), "hello", 1, d=UnknownClass('a'), e=3.0)

        # Static function
        with self.assertRaises(expected_exception):
            my_class.static_method(SubClass1('a'), "hello", 1, d=SubClass1(2.0), e=3.0)

        # Class function
        with self.assertRaises(expected_exception):
            B.class_method(SubClass2(0.0), "hello", 1, d=SubClass1(2.0), e='a')

        if Accepts.is_enabled():
            with self.assertRaises(TypeError):
                BaseClass('hello')
        else:
            BaseClass('hello')

    def test_proper_disabled_type_checking(self):
        Accepts.disable()
        my_class = B(3.0)
        self._check_proper_usage(my_class)

    def test_proper_enabled_type_checking(self):
        Accepts.disable()
        my_class = B(3.0)
        self._check_proper_usage(my_class)

    def test_disabled_type_checking_wrong_type(self):
        Accepts.disable()
        my_class = B(3.0)
        self._check_wrong_usage(my_class, FormatError)

    def test_enabled_type_checking_wrong_type(self):
        Accepts.enable()
        my_class = B(3.0)
        self._check_wrong_usage(my_class, TypeError)


if __name__ == "__main__":
    unittest.main()
