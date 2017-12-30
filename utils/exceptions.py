class PlayingEntityDoesNotExistError(Exception):
    """ Trying to access a player who do not exist. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PlayingEntityAlreadyExistsError(Exception):
    """ Trying to add a playing entity which already exists """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class OverwriteError(Exception):
    """ Trying to overwrite read-only data. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BackToTheFutureError(Exception):
    """ Trying to set information in the past when it's not allowed. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SmartIndexError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AcceptsSignatureError(Exception):
    """
    Exception for type checking decorator
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class NoMatchPlayedYetError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ReadOnlyDataError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MissingIndexError(Exception):
    """
    Some functions must be called with keyword parameter 'index'
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AussieException(Exception):
    """
    Singles and doubles mixed
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PlayingAgainstSelf(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

