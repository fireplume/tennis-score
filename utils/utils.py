import logging

from utils.exceptions import AcceptsSignatureError


class Accepts:
    """
    Decorator to be used to make sure function parameter types are as expected.
    It checks that parameters either match or are subclass of the ones specified
    in the decorator parameters. It should only be enabled during development using
    the Accepts.[enable,disable] functions.

    Example use. Note the difference between function, class member function, static class member function and
    class class member function.

        @Accepts.accepts(int, str)
        def print_x_times(a, b):
            pass

        class Base:
            pass

        class Test(Base:

            @Accepts.accepts(object, int, str)
            def func1(self, a, b):
                pass

            @staticmethod
            @Accepts.accepts(int, str)
            def func2(a, b):
                pass

            @classmethod
            @Accepts.accepts(type, int, str)
            def func3(cls, a, b):
                pass

    Example based on previous definitions:

        @Accepts.accepts(Base, Test)
        def print_obj(a, b):
            pass

        These are valid:
            print_obj(Base(), Test())
            print_obj(Test(), Test()) # because Test() 'is a' Base

        This is wrong:
            print_obj(Base(), Base()) # because Base() is not a Test object.
    """
    _DEBUG = False

    @classmethod
    def enable(cls):
        cls._DEBUG = True

    @classmethod
    def disable(cls):
        cls._DEBUG = False

    @classmethod
    def is_enabled(cls):
        return cls._DEBUG

    def accepts(*args_check, **kwargs_check):
        """
        :param args_check: types corresponding to parameter list
        :param kwargs_check: types corresponding to keyword parameters
        """
        def decorator(f):
            def f_wrapper(*args, **kwargs):
                if Accepts._DEBUG:
                    for i in range(0, len(args)):
                        if i > len(args_check)-1:
                            raise AcceptsSignatureError("Decorator args signature doesn't match that of function %s" % f.__name__)
                        if type(args[i]) != args_check[i] and \
                           not isinstance(args[i], args_check[i]):
                            raise TypeError("Parameter %d's type is wrong for %s, got '%s', expected '%s'" %
                                            (i+1, f.__name__, type(args[i]), args_check[i].__name__))
                    for kw in kwargs:
                        if kw not in kwargs_check:
                            raise AcceptsSignatureError("Decorator kwargs signature doesn't match that of function %s" % f.__name__)

                        if type(kwargs[kw]) != kwargs_check[kw] and \
                           not isinstance(kwargs[kw],  kwargs_check[kw]):
                            raise TypeError("Keyword parameter %s's type is wrong for %s, expected %s" %
                                            (kw, f.__name__, kwargs_check[kw].__name__))
                return f(*args, **kwargs)
            return f_wrapper
        return decorator


class LoggerHandler:
    _DEFAULT_LEVEL = logging.INFO
    _instance = None

    def __init__(self):
        if LoggerHandler._instance is not None:
            raise Exception("LoggerHandler singleton already instantiated")
        self._loggers = dict()

    def get_logger(self, name):
        self._loggers[name] = logging.getLogger(name)
        self._loggers[name].setLevel(LoggerHandler._DEFAULT_LEVEL)
        return self._loggers[name]

    def reset_all_level(self, level):
        for logger in self._loggers:
            self._loggers[logger].setLevel(level)

    @classmethod
    def set_default_level(cls, level: int):
        cls.DEFAULT_LEVEL = level

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = LoggerHandler()

        return cls._instance
