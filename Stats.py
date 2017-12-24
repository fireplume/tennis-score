from abc import ABCMeta, abstractmethod
from enum import Enum
import logging
import copy
from utils import *

logger = logging.getLogger("stats")
logger.setLevel(logging.DEBUG)


class StatsIndex(metaclass=ABCMeta):
    class IndexType(Enum):
        LEAGUE = "league_index"
        PLAYER = "player_index"

    @parameter_type_checking(int)
    def __init__(self, index: int):
        if not isinstance(index, int):
            raise TypeError("Index must be an integer equals to -1 or greater than 0.")

        if index == 0 or index < -1:
            raise ValueError("Index provided (%d) must be either '-1' for last index or be > 0." % index)
        self._index = index

    @property
    def index(self):
        return self._index

    # Only redefine the operators we need
    @parameter_type_checking(int)
    def __iadd__(self, other: int):
        self._index += other
        return self

    def __gt__(self, other):
        if isinstance(other, StatsIndex):
            return self._index > other.index
        elif isinstance(other, int):
            return self._index > other
        else:
            return NotImplemented

    def __eq__(self, other):
        if isinstance(other, StatsIndex):
            return self._index == other.index
        elif isinstance(other, int):
            return self._index == other
        else:
            return NotImplemented

    def __int__(self):
        return self.index

    def __hash__(self):
        return hash(str(self))

    @property
    @abstractmethod
    def index_type(self):
        pass

    @abstractmethod
    def __str__(self):
        pass


class PlayerIndex(StatsIndex):
    @property
    def index_type(self):
        return StatsIndex.IndexType.PLAYER

    def __str__(self):
        return "Player index %d" % self.index


class LeagueIndex(StatsIndex):
    @property
    def index_type(self):
        return StatsIndex.IndexType.LEAGUE

    def __str__(self):
        return "League index %d" % self.index


# Decorator for proper index type selection
def index_selector(f):
    def f_wrapper(self, *args, **kwargs):
        try:
            index = kwargs['index']
        except KeyError:
            raise KeyError("Function %s must be called with keyword parameter 'index=StatsIndexObject'" % f.__name__)

        if not isinstance(index, StatsIndex):
            raise TypeError("Function %s must be called with keyword parameter 'index' of type 'StatsIndexObject'" %
                            f.__name__)

        kwargs['index'] = self.get_league_index(index)
        kwargs['player_index'] = self.get_player_index(index)
        return f(self, *args, **kwargs)

    return f_wrapper


class InitError(Exception):
    def __init__(self, msg):
        super(InitError, self).__init__(msg)
        self.msg = msg

    def __str__(self):
        return self.msg


class OverwriteError(Exception):
    def __init__(self, msg):
        super(OverwriteError, self).__init__(msg)
        self.msg = msg

    def __str__(self):
        return self.msg


class BackToTheFutureError(Exception):
    pass


class Stats:
    """
    Stats are set based on the league match index, not to be confused with the player's
    match index.
    """

    class ResultsType(Enum):
        INTEGER = "integer"
        FLOAT = "float"

    def __init__(self):
        self._games_won = dict()
        self._games_lost = dict()
        self._game_points = dict()
        # self._average_points_per_match = dict()
        # self._average_points_per_game_won = dict()

        # League/player match index mapping
        self._player_match_index = PlayerIndex(1)
        self._player_to_league_match_index = dict()
        self._league_to_player_match_index = dict()

    @parameter_type_checking(StatsIndex)
    def get_league_index(self, index: StatsIndex):
        if index == -1:
            return copy.deepcopy(max(self._games_won.keys()))

        if index.index_type == StatsIndex.IndexType.LEAGUE:
            return index
        else:
            return copy.deepcopy(self._player_to_league_match_index[index])

    @parameter_type_checking(StatsIndex)
    def get_player_index(self, index: StatsIndex):
        """!!! Don't return references to internal data structures !!!"""
        if index == -1:
            index = max(self._games_won.keys())

        if index.index_type == StatsIndex.IndexType.PLAYER:
            return copy.deepcopy(index)
        else:
            return copy.deepcopy(self._league_to_player_match_index[index])

    @parameter_type_checking(int, int, LeagueIndex)
    def set_match_results(self,
                          games_won: int,
                          games_lost: int,
                          league_match_index: LeagueIndex):
        """!!! Don't use reference for setting data structures !!!"""

        if league_match_index in self._games_won:
            raise OverwriteError("Trying to overwrite match results for %s" % str(league_match_index))

        if len(self._games_won) != 0:
            latest_index = max([i for i in self._games_won.keys()])
            if league_match_index < latest_index:
                raise BackToTheFutureError("Can't rewrite past, trying to set results for a game index"
                                           "lower than the latest")

        p_index = copy.deepcopy(self._player_match_index)
        l_index = copy.deepcopy(league_match_index)

        self._games_won[l_index] = games_won
        self._games_lost[l_index] = games_lost
        self._player_to_league_match_index[p_index] = l_index
        self._league_to_player_match_index[l_index] = p_index

        self._player_match_index += 1

    @parameter_type_checking(int, LeagueIndex)
    def set_match_points(self,
                         game_points: float,
                         league_match_index: LeagueIndex):
        """!!! Don't use reference for setting data structures !!!"""
        if not isinstance(league_match_index, LeagueIndex):
            raise TypeError("set_match_points league_match_index must be of type LeagueIndex")

        l_index = copy.deepcopy(league_match_index)
        if l_index not in self._games_won:
            raise InitError("You must set the match results before assigning points for: %s." % l_index)

        if l_index in self._game_points:
            raise OverwriteError("Trying to overwrite game points for %s" % str(l_index))

        self._game_points[l_index] = game_points

    ##########################################################
    # Getter functions
    # Note: index_selector decorated function must be called
    # with keyword parameter 'index=value'
    ##########################################################
    @parameter_type_checking(dict, ResultsType, LeagueIndex)
    def _get_sum(self,
                 data: dict,
                 results_type: ResultsType,
                 last_league_index: LeagueIndex):
        if results_type == Stats.ResultsType.INTEGER:
            value = 0
        else:
            value = 0.0

        for index in data:
            if index > last_league_index:
                break
            else:
                value += data[index]

        return value

    @index_selector
    def get_index_number_of_match_played(self, **kwargs):
        league_index = kwargs['index']
        game_played = 0
        for index in self._games_won:
            if index > league_index:
                return game_played
            else:
                game_played += 1
        return PlayerIndex(game_played)

    @index_selector
    def get_points_for_match(self, **kwargs):
        league_index = kwargs['index']
        if league_index not in self._game_points:
            raise KeyError("Match not played or points not set yet! Indexes: League(%d) Player(%d)" %
                           (league_index, kwargs['match_index']))
        return self._game_points[league_index]

    @index_selector
    def get_cumulative_games_points(self, **kwargs):
        league_index = kwargs['index']
        return self._get_sum(self._game_points,
                             Stats.ResultsType.FLOAT,
                             copy.deepcopy(league_index))

    @index_selector
    def get_cumulative_games_won(self, **kwargs):
        league_index = kwargs['index']
        return self._get_sum(self._games_won,
                             Stats.ResultsType.INTEGER,
                             copy.deepcopy(league_index))

    @index_selector
    def get_cumulative_games_lost(self, **kwargs):
        league_index = kwargs['index']
        return self._get_sum(self._games_lost,
                             Stats.ResultsType.INTEGER,
                             copy.deepcopy(league_index))

    @index_selector
    def get_average_points_per_match(self, **kwargs):
        league_index = kwargs['index']
        points = self.get_cumulative_games_points(index=copy.deepcopy(league_index))
        match_played = int(self.get_index_number_of_match_played(index=league_index))
        return points/match_played

    @index_selector
    def get_average_points_per_game_won(self, **kwargs):
        league_index = kwargs['index']
        points = self.get_cumulative_games_points(index=copy.deepcopy(league_index))
        games_won = self.get_cumulative_games_won(index=copy.deepcopy(league_index))
        return points/float(games_won)
