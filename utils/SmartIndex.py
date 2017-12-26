from abc import ABCMeta, abstractmethod
import copy
from enum import Enum
import sys
import os
import importlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
utils = importlib.import_module("utils")

from utils.utils import Accepts
from utils.exceptions import *


class IndexType(Enum):
    LEAGUE = "league_index"
    PLAYER = "player_index"


class SmartIndex(metaclass=ABCMeta):

    @Accepts.accepts(object, int, bool, index=int, locked=bool)
    def __init__(self, index: int, locked=False):
        if index < -1:
            raise ValueError("Index provided (%d) must be either greater than or equal to -1" % index)
        self._index = index

        # allow index to be modified
        self._lock = locked

        self._exists = True

    def set_no_exists(self):
        self._exists = False

    @property
    def exists(self):
        return self._exists

    def get_unlocked_copy(self):
        c = copy.deepcopy(self)
        c._lock = False
        return c

    def get_locked_copy(self):
        c = copy.deepcopy(self)
        c.lock()
        return c

    @property
    def index(self):
        return self._index

    def lock(self):
        # prevent index modification
        self._lock = True

    @property
    def is_locked(self):
        return self._lock

    # Only redefine the operators we need
    @Accepts.accepts(object, int, other=int)
    def __iadd__(self, other: int):
        if self.is_locked:
            raise ReadOnlyDataError("Can't modify read only index")
        self._index += other
        return self

    # @Accepts.accepts(object, int, other=int)
    # def __isub__(self, other: int):
    #     if self.is_locked:
    #         raise ReadOnlyDataError("Can't modify read only index")
    #     self._index -= other
    #     return self

    def __gt__(self, other):
        if isinstance(other, SmartIndex):
            return self._index > other.index
        elif isinstance(other, int):
            return self._index > other
        raise NotImplementedError

    def __lt__(self, other):
        if isinstance(other, SmartIndex):
            return self._index < other.index
        elif isinstance(other, int):
            return self._index < other
        raise NotImplementedError

    def __ge__(self, other):
        if isinstance(other, SmartIndex):
            return self._index >= other.index
        elif isinstance(other, int):
            return self._index >= other
        raise NotImplementedError

    def __le__(self, other):
        if isinstance(other, SmartIndex):
            return self._index <= other.index
        elif isinstance(other, int):
            return self._index <= other
        raise NotImplementedError

    def __eq__(self, other):
        if isinstance(other, SmartIndex):
            return self._index == other.index
        elif isinstance(other, int):
            return self._index == other
        raise NotImplementedError

    def __ne__(self, other):
        if isinstance(other, SmartIndex):
            return self._index != other.index
        elif isinstance(other, int):
            return self._index != other
        raise NotImplementedError

    def __int__(self):
        return self._index

    def __hash__(self):
        return hash(str(self))

    @property
    @abstractmethod
    def index_type(self):
        pass

    @property
    @abstractmethod
    def alternate_type(self):
        pass

    @abstractmethod
    def __str__(self):
        pass


class PlayerIndex(SmartIndex):
    """
    Match index from the player's (or doubles' team) perspective. Any given index represent a number
    of match played by the player and refer to that match specifically.
    """
    @property
    def index_type(self):
        return IndexType.PLAYER

    @property
    def alternate_type(self):
        return IndexType.LEAGUE

    def __str__(self):
        return "Player index %d" % self.index


class LeagueIndex(SmartIndex):
    """
    Match index from the league's perspective. Any given index represent a number of match played by
    any playing entity (note that singles and doubles are not mixed together).
    """
    @property
    def index_type(self):
        return IndexType.LEAGUE

    @property
    def alternate_type(self):
        return IndexType.PLAYER

    def __str__(self):
        return "League index %d" % self.index


class SmartIndexCache:
    """
    Class to manage conversion between PlayerIndex and LeagueIndex.
    Locks index once added to avoid corruption since we are holding references.
    """
    def __init__(self):
        self._index_to_index_map = dict()
        self._index_cache = dict()
        self._index_cache[IndexType.PLAYER] = set()
        self._index_cache[IndexType.LEAGUE] = set()

    @Accepts.accepts(object, LeagueIndex, PlayerIndex, league_index=LeagueIndex, player_index=PlayerIndex)
    def add_index(self, league_index: LeagueIndex, player_index: PlayerIndex):
        # make sure index is locked
        league_index.lock()
        player_index.lock()
        # update cache and map
        self._index_cache[player_index.index_type].add(player_index)
        self._index_cache[league_index.index_type].add(league_index)
        self._index_to_index_map[league_index] = player_index
        self._index_to_index_map[player_index] = league_index

    @Accepts.accepts(object, SmartIndex, index=SmartIndex)
    def exists(self, index: SmartIndex):
        if index in self._index_cache[index.index_type]:
            return True
        return False

    @Accepts.accepts(object, IndexType, index_type=IndexType)
    def number_of_indexes(self, index_type: IndexType):
        return len(self._index_cache[index_type])

    @Accepts.accepts(object, IndexType, index_type=IndexType)
    def max_index(self, index_type: IndexType):
        if len(self._index_cache[index_type]) == 0:
            raise SmartIndexError("No index added to cache yet")
        return max(self._index_cache[index_type])

    def get_latest_valid_index(self, index: SmartIndex):
        if index.index_type == IndexType.PLAYER:
            latest_index = PlayerIndex(0)
        else:
            latest_index = LeagueIndex(0)
        for i in sorted(self._index_cache[index.index_type]):
            if latest_index < i <= index:
                latest_index = i
        return latest_index

    @Accepts.accepts(object, SmartIndex, IndexType, index=SmartIndex, index_type=IndexType)
    def get_index_for_type(self, index: SmartIndex, index_type: IndexType):
        # Index 0 is a special case
        if index == 0:
            if index_type == IndexType.PLAYER:
                return PlayerIndex(0)
            else:
                return LeagueIndex(0)

        if len(self._index_to_index_map) == 0:
            raise NoMatchPlayedYetError("No stats were entered yet.")

        if index == -1:
            return max(self._index_cache[index_type])

        if not self.exists(index):
            # Let the data object handle the case
            c = index.get_locked_copy()
            c.set_no_exists()
            return c

        if index.index_type == index_type:
            return index
        else:
            r = self._index_to_index_map[index]
            if r.index_type != index_type:
                raise SmartIndexError("Can't find %s index for %s" % (str(index_type), str(index)))
            return r

    def __len__(self):
        # there are the same number of player and league indexes
        return len(self._index_cache[IndexType.LEAGUE])


# Decorator for proper index type selection
def player_index_selector(f):
    """
    Requirements to use this decorator:
    - must decorate class member function with 'self' parameter
    - class must support SmartIndexCache and implement _get_index_cache
    """
    def f_wrapper(self, *args, **kwargs):
        try:
            index = kwargs['index']
        except KeyError:
            raise MissingIndexError("Function %s must be called with keyword parameter 'index=StatsIndexObject'" %
                           f.__name__)

        if not isinstance(index, SmartIndex):
            raise TypeError("Function %s must be called with keyword parameter 'index' of type 'SmartIndexObject'" %
                            f.__name__)

        kwargs['index'] = self._get_index_cache().get_index_for_type(index, IndexType.PLAYER)

        return f(self, *args, **kwargs)

    return f_wrapper
