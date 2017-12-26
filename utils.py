import logging


def parameter_type_checking(*args_check, **kwargs_check):
    """
    Decorator to be used to make sure CLASS function parameter types are as expected.
    It checks that parameters either match or are subclass of the ones specified
    in the decorator parameters.

    This won't work for regular function as they don't have the 'self' parameter.
    It also won't work on static/class methods of classes.

    :param args_check: types corresponding to parameter list
    :param kwargs_check: types corresponding to keyword parameters
    """
    def decorator(f):
        def f_wrapper(self, *args, **kwargs):
            for i in range(0, len(args)):
                if type(args[i]) != args_check[i] and \
                        not isinstance(args[i], args_check[i]):
                    raise TypeError("Parameter %d's type is wrong for %s, expected %s" %
                                    (i+1, f.__name__, args_check[i].__name__))
            for kw in kwargs:
                if type(kwargs[kw]) != kwargs_check[kw] and \
                        not isinstance(kwargs[kw],  kwargs_check[kw]):
                    raise TypeError("Keyword parameter %s's type is wrong for %s, expected %s" %
                                    (kw, f.__name__, kwargs_check[kw].__name__))
            return f(self, *args, **kwargs)
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
