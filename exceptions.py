class PlayingEntityDoesNotExistError(Exception):
    """ Trying to access a player who do not exist. """
    pass


class PlayingEntityAlreadyExistsError(Exception):
    """ Trying to add a playing entity which already exists """
    pass


class InitError(Exception):
    """ Trying to access a data structure which has not been initialized yet."""
    pass


class OverwriteError(Exception):
    """ Trying to overwrite read-only data. """
    pass


class BackToTheFutureError(Exception):
    """ Trying to set information in the past when it's not allowed. """
    pass


class UnforseenError(Exception):
    """ I really didn't expected that one... """
    pass
