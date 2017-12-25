from enum import Enum
from abc import ABCMeta, abstractmethod
import re


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

    class EntityData:
        """
        This class is used to hold singles information as well as singles' doubles information. It should
        only be used for the latter when mixing doubles team constantly, making it hard to track each player's ranking
        for doubles in such a case.
        """
        def __init__(self, initial_ranking: int, initial_points=0.0):
            self.initial_ranking = initial_ranking
            self.initial_points = initial_points
            self.game_points = dict()
            self.match_index = 0
            self.cumulative_games_won = dict()
            self.cumulative_games_lost = dict()
            self.ranking = dict()
            self.games = set()

            # Cumulative games won and lost up to match index (key)
            self.cumulative_games_won[self.match_index] = 0
            self.cumulative_games_lost[self.match_index] = 0

            self.reset_rankings()
            self.reset_points()

        def reset_rankings(self):
            self.ranking = dict()
            self.ranking[0] = self.initial_ranking

        def reset_points(self):
            self.game_points = dict()
            self.game_points[0] = self.initial_points

    def __init__(self,
                 name: str,
                 play_type: PlayType,
                 play_level_scoring_factor: float,
                 initial_ranking: int,
                 initial_points=0.0,
                 name2="",
                 initial_ranking2=1,
                 initial_points2=0.0):
        self._name = name.lower()
        self._play_type = play_type
        self._name2 = name2.lower()
        # Play level scoring factor can be altered during the course of the season
        self._play_level_scoring_factor = dict()
        self._play_level_scoring_factor[0] = play_level_scoring_factor

        self._entity_data = dict()

        self._entity_data[self._play_type] = PlayingEntity.EntityData(initial_ranking, initial_points)
        if self._play_type == PlayingEntity.PlayType.SINGLES:
            # add individual player's doubles information place holder
            self._entity_data[PlayingEntity.PlayType.DOUBLES] = PlayingEntity.EntityData(initial_ranking2,
                                                                                         initial_points2)
        for play_type in self._entity_data.keys():
            self.reset_rankings(play_type)
            self.reset_points(play_type)

    def _play_type_check(self, play_type: PlayType):
        if play_type != self._play_type:
            raise Exception("You requested information for %s but the entity is for %s" % (play_type, self._play_type))

    def update_play_level_scoring_factor(self, play_level_scoring_factor: float,
                                         play_type: PlayType,
                                         match_index: int):
        if not (0.0 < play_level_scoring_factor <= 1.0):
            raise Exception("Play level scoring factor should be: '0 < value <= 1'")
        self._play_type_check(play_type)

        match_played = self.get_nb_match_played(play_type)
        if match_index > match_played:
            raise Exception("Can't set play level score factor for a game not played yet (%d)! Games Played: %d" %
                            (match_index, match_played))

        match_index = self.get_nb_match_played(play_type)
        self._play_level_scoring_factor[match_index] = play_level_scoring_factor

    def get_play_level_scoring_factor(self, play_type: PlayType, match_index=-1):
        # Need to comment out the following to make doubles info per single player work.
        # self._play_type_check(play_type)
        if match_index == -1:
            match_index = self.get_nb_match_played(play_type)
        if match_index not in self._play_level_scoring_factor:
            # get last valid level score factor
            last_index = 0
            for index in self._play_level_scoring_factor:
                if index > match_index:
                    break
                last_index = index
            match_index = last_index
        return self._play_level_scoring_factor[match_index]

    def iter_play_level_scoring_factor(self):
        for league_index in self._play_level_scoring_factor:
            yield league_index,  self._play_level_scoring_factor[league_index]

    def reset_rankings(self, play_type: PlayType):
        self._entity_data[play_type].reset_rankings()

    def reset_points(self, play_type: PlayType):
        self._entity_data[play_type].reset_points()

    def _compute_cumulative_game_standings(self, game: BaseGame, play_type: PlayType):
        games_won = game.get_games_won(self.get_name())
        games_lost = game.get_games_lost(self.get_name())

        if self._entity_data[play_type].match_index == 1:
            self._entity_data[play_type].cumulative_games_won[self._entity_data[play_type].match_index] = games_won
            self._entity_data[play_type].cumulative_games_lost[self._entity_data[play_type].match_index] = games_lost
        else:
            for i in range(1, self._entity_data[play_type].match_index):
                if i not in self._entity_data[play_type].cumulative_games_won:
                    self._entity_data[play_type].cumulative_games_won[i] = \
                        self._entity_data[play_type].cumulative_games_won[i - 1]
                    self._entity_data[play_type].cumulative_games_lost[i] = \
                        self._entity_data[play_type].cumulative_games_lost[i - 1]

            match_index = self._entity_data[play_type].match_index
            self._entity_data[play_type].cumulative_games_won[match_index] = \
                self._entity_data[play_type].cumulative_games_won[match_index - 1] + games_won
            self._entity_data[play_type].cumulative_games_lost[match_index] = \
                self._entity_data[play_type].cumulative_games_lost[match_index - 1] + games_lost

    def add_game(self, game: BaseGame, play_type: PlayType):
        self._entity_data[play_type].match_index += 1

        # Check name of playing_entity is involved in game
        if not game.has_played(self._name, self._name2):
            raise Exception("%s has not played in match: %s" % (self.get_name(), game))

        self._compute_cumulative_game_standings(game, play_type)
        self._entity_data[play_type].games.add(game)

    def set_rank(self, match_index: int, rank: int, play_type: PlayType):
        """
        Sets the player rank for given match index. It is based on all results up to and including match index.
        """
        if rank < 1:
            raise Exception("Rank must be positive and greater than or equal to 1, value given: %d" % rank)
        self._entity_data[play_type].ranking[match_index] = rank

    def set_game_points(self, match_index: int, points: float, play_type: PlayType):
        """
        Sets the player earned points for given match index.
        """
        if match_index in self._entity_data[play_type].game_points.keys():
            raise Exception("Points already set for this game (match: %d type: %s)!" % (match_index, play_type))

        self._entity_data[play_type].game_points[match_index] = points

    def latest_valid_match_index_lte(self, match_index: int, play_type: PlayType):
        last_index = 0
        index = 0
        for index in sorted(self._entity_data[play_type].cumulative_games_won.keys()):
            if index > match_index:
                return last_index
            last_index = index
        return index

    def get_cumulative_games_won(self, match_index: int, play_type: PlayType):
        valid_index = self.latest_valid_match_index_lte(match_index, play_type)
        return self._entity_data[play_type].cumulative_games_won[valid_index]

    def get_cumulative_games_lost(self, match_index: int, play_type: PlayType):
        valid_index = self.latest_valid_match_index_lte(match_index, play_type)
        return self._entity_data[play_type].cumulative_games_lost[valid_index]

    def get_cumulative_points(self, match_index: int, play_type: PlayType):
        if match_index == -1:
            match_index = self.latest_valid_match_index_lte(match_index, play_type)

        total = 0
        for i in range(0, match_index + 1):
            total += self.get_game_points(i, play_type)
        return total

    def get_average_points_per_match(self, match_index: int, play_type: PlayType):
        try:
            return self.get_cumulative_points(match_index, play_type) / match_index
        except ZeroDivisionError:
            return 0

    def get_game_points(self, match_index: int, play_type: PlayType):
        if match_index not in self._entity_data[play_type].game_points:
            return 0
        return self._entity_data[play_type].game_points[match_index]

    def get_ranking(self, match_index: int, play_type: PlayType):
        """
        To get current ranking, call without parameter.
        """
        if match_index == -1:
            return self._entity_data[play_type].ranking[max(self._entity_data[play_type].ranking.keys())]

        return self._entity_data[play_type].ranking[match_index]

    def get_name(self):
        if self.is_doubles_team:
            sorted_names = sorted([self._name.lower(), self._name2.lower()])
            return PlayingEntity.DOUBLES_NAME_FORMAT.format(*sorted_names).lower()
        return self._name.lower()

    def get_nb_match_played(self, play_type: PlayType):
        return self._entity_data[play_type].match_index

    @property
    def is_doubles_team(self):
        """Property so it is read only"""
        if self._play_type is None:
            raise Exception("Play type must be set in subclass after calling base class init.")
        if self._play_type == PlayingEntity.PlayType.SINGLES:
            return False
        return True

    def get_type(self):
        return self._play_type

    def get_names(self):
        return self._name, self._name2

    def fill_in_the_blanks(self,
                           match_index: int,
                           play_type: PlayType):
        for i in range(1, match_index + 1):
            if i not in self._entity_data[play_type].ranking:
                self._entity_data[play_type].ranking[i] = self._entity_data[play_type].ranking[i - 1]

    def __lt__(self, other):
        """
        Added to allow sorting playing entities by name
        :return:
        """
        return self.get_name() < other.get_name()
