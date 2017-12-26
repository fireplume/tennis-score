import re

from Stats import *
from utils.SmartIndex import *


class BaseGame(metaclass=ABCMeta):
    @abstractmethod
    def get_name(self, entity: int):
        pass

    @abstractmethod
    def get_games_won(self, entity_name: str):
        pass

    @abstractmethod
    def get_games_lost(self, entity_name: str):
        pass

    @abstractmethod
    def has_played(self, entity_name: str, entity_name2=""):
        pass

    @abstractmethod
    def get_players_list(self):
        pass

    @property
    @abstractmethod
    def play_type(self):
        pass

    @abstractmethod
    def __str__(self):
        pass


class PlayingEntity(metaclass=ABCMeta):
    """
    To refer to a particular game entity, use name equal to "NAME1" for singles or "NAME1 and NAME2" for doubles.
    See DOUBLES_NAME_FORMAT and get_name in this class for details.
    """
    DOUBLES_NAME_FORMAT = "{:12s} and {:12s}"
    DOUBLES_NAME_RE = re.compile(r"^(\S+)\s+and\s+(\S+)\s+$")

    # Sanity test of prior two statements
    _team_name = DOUBLES_NAME_FORMAT.format("name1", "name2")
    _m = DOUBLES_NAME_RE.match(_team_name)
    if not _m:
        raise Exception("PlayingEntity.DOUBLES_NAME_RE must be able to exactly match a "
                        "PlayingEntity.DOUBLES_NAME_FORMAT formatted string")

    class PlayType(Enum):
        SINGLES = 'singles'
        DOUBLES = 'doubles'

    def __init__(self,
                 name: str,
                 play_type: PlayType,
                 play_level_scoring_factor: float,
                 initial_points=0.0):
        self._name = name.lower()
        self._play_type = play_type

        self._stats = Stats(initial_points, play_level_scoring_factor)
        self._stats.reset_data('match_points')
        self._stats.reset_data('ranking')

    def get_initial_level_scoring_factor(self):
        return self._stats.get_initial_data('level_scoring_factor')

    def update_play_level_scoring_factor(self, play_level_scoring_factor: float,
                                         index: LeagueIndex):
        if not (0.0 < play_level_scoring_factor <= 1.0):
            raise Exception("Play level scoring factor should be: '0 < value <= 1'")

        self._stats.set_data('level_scoring_factor', play_level_scoring_factor, index)

    def get_play_level_scoring_factor(self, index: SmartIndex):
        return self._stats.get_data_for_index('level_scoring_factor', index=index)

    def reset_rankings(self):
        self._stats.reset_data('ranking')

    def reset_points(self):
        self._stats.reset_data('match_points')

    def add_game(self, game: BaseGame, index: LeagueIndex):
        # Check name of playing_entity is involved in game
        if not game.has_played(self._name):
            raise Exception("%s has not played in match: %s" % (self._name, game))

        games_won = game.get_games_won(self._name)
        games_lost = game.get_games_lost(self._name)

        self._stats.set_match_results(games_won, games_lost, index)

    def set_rank(self, index: LeagueIndex, rank: int):
        """
        Sets the player rank for given match index. It is based on all results up to and including match index.
        """
        if rank < 1:
            raise Exception("Rank must be positive and greater than or equal to 1, value given: %d" % rank)
        self._stats.set_data('ranking', rank, index)

    def set_match_points(self, index: LeagueIndex, points: float):
        """
        Sets the player earned points for given match index.
        """
        if not self._stats.index_exists(index):
            raise SmartIndexError("No game set for %s" % str(index))
        self._stats.set_data('match_points', points, league_index=index)

    def get_cumulative_games_won(self, index: SmartIndex):
        try:
            return self._stats.get_cumulative_data_sum_for_index('games_won', index=index)
        except NoMatchPlayedYetError:
            return 0

    def get_cumulative_games_lost(self, index: SmartIndex):
        try:
            return self._stats.get_cumulative_data_sum_for_index('games_lost', index=index)
        except NoMatchPlayedYetError:
            return 0

    def get_cumulative_points(self, index: SmartIndex):
        try:
            return self._stats.get_cumulative_data_sum_for_index('match_points', index=index)
        except NoMatchPlayedYetError:
            return 0.0

    def get_average_points_per_match(self, index: SmartIndex):
        try:
            return self._stats.get_average_points_per_match(index=index)
        except NoMatchPlayedYetError:
            return 0.0

    def get_match_points(self, index: SmartIndex):
        try:
            return self._stats.get_data_for_index('match_points', index=index)
        except NoMatchPlayedYetError:
            return 0.0

    def get_ranking(self, index: SmartIndex):
        return self._stats.get_data_for_index('ranking', index=index)

    def get_nb_match_played(self, index: LeagueIndex):
        try:
            return self._stats.get_number_of_match_played_by_league_index_time(index=index)
        except NoMatchPlayedYetError:
            return 0

    @property
    def play_type(self):
        return self._play_type

    def get_name(self):
        return self._name

    def __lt__(self, other):
        """
        Added to allow sorting playing entities by name
        :return:
        """
        return self.get_name() < other.get_name()

    def __str__(self):
        return self.get_name()
