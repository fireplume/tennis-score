#!/usr/bin/env python3
from abc import ABCMeta
from enum import Enum
import re
import logging
import argparse

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("tennis")
logger.setLevel(logging.INFO)

DEFAULT_POINTS_PER_GAME = 100
RANKING_FACTOR_CONSTANT = 1.0
RANKING_DIFF_FACTOR_CONSTANT = 1.0
RANKING_FACTOR_BREAK_IN_PERIOD = 3
LEAGUE_BREAK_IN_SCORE_FACTOR = 0.1
REPLACEMENT_PLAYER_PREFIX = 'RPL'


class Game:
    """ Forward declaration for PlayingEntity, will be defined later """
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

    def reset_rankings(self, play_type: PlayType):
        self._entity_data[play_type].reset_rankings()

    def reset_points(self, play_type: PlayType):
        self._entity_data[play_type].reset_points()

    def _compute_cumulative_game_standings(self, game: Game, play_type: PlayType):
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

    def add_game(self, game: Game, play_type: PlayType):
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


class Player(PlayingEntity):
    """
    Initial ranking is only meaningful if break in period is 0, see options for details.
    """
    def __init__(self, name: str, play_level_scoring_factor: float, initial_ranking: int, initial_points=0.0):
        super(Player, self).__init__(name,
                                     PlayingEntity.PlayType.SINGLES,
                                     play_level_scoring_factor,
                                     initial_ranking,
                                     initial_points)

    def __str__(self):
        return self.get_name()


class DoublesTeam(PlayingEntity):
    """
    Initial ranking is only meaningful if break in period is 0, see options for details.
    """
    def __init__(self, player1: PlayingEntity, player2: PlayingEntity,
                 play_level_scoring_factor: float,
                 initial_ranking: int,
                 initial_points: float):
        super(DoublesTeam, self).__init__(player1.get_name(),
                                          PlayingEntity.PlayType.DOUBLES,
                                          play_level_scoring_factor,
                                          0, 0,
                                          player2.get_name(),
                                          initial_ranking,
                                          initial_points)

        self._players = [player1, player2]

    def is_in_team(self, player_name):
        if player_name.lower() == self._players[0].get_name() or \
           player_name.lower() == self._players[1].get_name():
            return True
        return False

    def get_play_level_scoring_factor(self, play_type: PlayingEntity.PlayType, match_index=-1):
        """
        Override the play level scoring factor to be that of the product of
        the team's players'.
        """

        if play_type != PlayingEntity.PlayType.DOUBLES:
            raise Exception("Asking for singles play level score factor for a doubles team!")

        # We want the SINGLES playing factor
        factor1 = self._players[0].get_play_level_scoring_factor(PlayingEntity.PlayType.SINGLES, match_index)
        factor2 = self._players[1].get_play_level_scoring_factor(PlayingEntity.PlayType.SINGLES, match_index)

        return factor1 * factor2

    def get_player(self, index: int):
        if index != 1 and index != 2:
            raise Exception("You can only ask for player 1 or 2 in a doubles team. You requested: %d" % index)
        return self._players[index-1]


class Game:
    """
    Game class to hold game results.
    """
    # LEAGUE must be set to a valid League object before being instantiated!
    LEAGUE = None

    def __init__(self, p1: str, p1_games_won: int, p2: str, p2_games_won: int):
        if Game.LEAGUE is None:
            raise Exception("You must initialize Game.LEAGUE before instantiating a Game object!")

        self._players_list = set()
        self._play_type = PlayingEntity.PlayType.SINGLES
        self._p1 = p1.lower()
        self._p2 = p2.lower()
        self._p1_games_won = p1_games_won
        self._p2_games_won = p2_games_won

        self._data = dict()
        self._data['name'] = dict()
        self._data['games_won'] = dict()
        self._data['games_lost'] = dict()

        self._init_data()

    def _init_data(self):
        # Extract player's names from the entity's names in case it's a doubles match
        team_1_names = PlayingEntity.DOUBLES_NAME_RE.match(self._p1)
        team_2_names = PlayingEntity.DOUBLES_NAME_RE.match(self._p2)
        if team_1_names and not team_2_names or not team_2_names and team_1_names:
            raise Exception("Playing entity caters to different match type '%s' vs '%s'" % (self._p1, self._p2))

        # Add doubles players names to the player list
        if team_1_names:
            self._play_type = PlayingEntity.PlayType.DOUBLES
            self._players_list.add(team_1_names.group(1).lower())
            self._players_list.add(team_1_names.group(2).lower())
            self._players_list.add(team_2_names.group(1).lower())
            self._players_list.add(team_2_names.group(2).lower())

        # Add singles players' names or doubles' team names to the list too
        self._players_list.add(self._p1.lower())
        self._players_list.add(self._p2.lower())

        exception_string = []
        if not Game.LEAGUE.playing_entity_name_exists(self._p1):
            exception_string.append("Playing entity '%s' is not registered with the league!" % self._p1)
        if not Game.LEAGUE.playing_entity_name_exists(self._p2):
            exception_string.append("Playing entity '%s' is not registered with the league!" % self._p2)
        if exception_string:
            raise Exception("\n".join(exception_string))

        self._data['name'][1] = self._p1.lower()
        self._data['games_won'][self._p1.lower()] = self._p1_games_won
        self._data['games_lost'][self._p1.lower()] = self._p2_games_won
        self._data['name'][2] = self._p2.lower()
        self._data['games_won'][self._p2.lower()] = self._p2_games_won
        self._data['games_lost'][self._p2.lower()] = self._p1_games_won

        if self._play_type == PlayingEntity.PlayType.DOUBLES:
            # Allow doubles players to ask for their score by their individual name
            # instead of the team's name.
            self._data['games_won'][team_1_names.group(1).lower()] = self._p1_games_won
            self._data['games_won'][team_1_names.group(2).lower()] = self._p1_games_won
            self._data['games_lost'][team_1_names.group(1).lower()] = self._p2_games_won
            self._data['games_lost'][team_1_names.group(2).lower()] = self._p2_games_won

            self._data['games_won'][team_2_names.group(1).lower()] = self._p2_games_won
            self._data['games_won'][team_2_names.group(2).lower()] = self._p2_games_won
            self._data['games_lost'][team_2_names.group(1).lower()] = self._p1_games_won
            self._data['games_lost'][team_2_names.group(2).lower()] = self._p1_games_won

    def get_name(self, entity: int):
        if entity != 1 and entity != 2:
            raise Exception("Game.get_name: entity must be either 1 or 2, value given: %d" % entity)
        return self._data['name'][entity]

    def get_games_won(self, entity_name: str):
        if not self.has_played(entity_name):
            raise Exception("Game.get_games_won: player %s didn't play in this game" % entity_name)
        return self._data['games_won'][entity_name]

    def get_games_lost(self, entity_name: str):
        if not self.has_played(entity_name):
            raise Exception("Game.get_games_won: player %s didn't play in this game" % entity_name)
        return self._data['games_lost'][entity_name]

    def has_played(self, entity_name: str, entity_name2=""):
        if entity_name.lower() in self._players_list:
            if entity_name2 != "" and entity_name2.lower() not in self._players_list:
                return False
            else:
                return True
        return False

    def get_players_list(self):
        return self._players_list

    @property
    def play_type(self):
        return self._play_type

    def __str__(self):
        name1 = self._data['name'][1]
        name2 = self._data['name'][2]
        return "{:<12s} vs {:<12s}: {:d}-{:d}".format(self._data['name'][1], self._data['name'][2],
                                                      self._data['games_won'][name1], self._data['games_won'][name2])


class League:
    def __init__(self):
        self._playing_entity = dict()
        self._playing_entity[PlayingEntity.PlayType.SINGLES] = dict()
        self._playing_entity[PlayingEntity.PlayType.DOUBLES] = dict()

        self._games = dict()
        self._games[PlayingEntity.PlayType.SINGLES] = dict()
        self._games[PlayingEntity.PlayType.DOUBLES] = dict()

        self._name_to_entity = dict()

        self._match_index = dict()
        self._match_index[PlayingEntity.PlayType.SINGLES] = 0
        self._match_index[PlayingEntity.PlayType.DOUBLES] = 0

        self._players_matches_played = dict()
        self._players_matches_played[PlayingEntity.PlayType.SINGLES] = dict()
        self._players_matches_played[PlayingEntity.PlayType.DOUBLES] = dict()

    def last_match_index(self, play_type: PlayingEntity.PlayType):
        return max(self._games[play_type].keys())

    def playing_entity_name_exists(self, playing_entity_name: str):
        if playing_entity_name.lower() in self._name_to_entity:
            return True
        return False

    def add_playing_entity(self, playing_entity: PlayingEntity):
        self._playing_entity[playing_entity.get_type()][playing_entity.get_name()] = playing_entity
        self._name_to_entity[playing_entity.get_name()] = playing_entity

        self._players_matches_played[playing_entity.get_type()][playing_entity.get_name()] = dict()
        self._players_matches_played[playing_entity.get_type()][playing_entity.get_name()][0] = 0

        # If playing entity is SINGLES, also add place holder for doubles information
        if playing_entity.get_type() == PlayingEntity.PlayType.SINGLES:
            self._players_matches_played[PlayingEntity.PlayType.DOUBLES][playing_entity.get_name()] = dict()
            self._players_matches_played[PlayingEntity.PlayType.DOUBLES][playing_entity.get_name()][0] = 0

    def add_game(self, game: Game):
        p1_entity = self._name_to_entity[game.get_name(1)]
        p2_entity = self._name_to_entity[game.get_name(2)]

        if p1_entity.get_type() != p2_entity.get_type():
            print("ERROR: Trying to add game between %s and %s" % (game.get_name(1), game.get_name(2)))
            raise Exception("You can't mix singles and doubles in a Game object!")

        play_type = p1_entity.get_type()
        self._match_index[play_type] += 1

        if self._match_index[play_type] in self._games[play_type].keys():
            raise Exception("Internal error: game overwrite attempt at match index %d" % self._match_index[play_type])
        self._games[play_type][self._match_index[play_type]] = game

        # Add game to player objects too
        self._playing_entity[play_type][game.get_name(1)].add_game(game, play_type)
        self._playing_entity[play_type][game.get_name(2)].add_game(game, play_type)

        # If it's a doubles game, also add the game to each singles player
        if play_type == PlayingEntity.PlayType.DOUBLES:
            for doubles_entity in [p1_entity, p2_entity]:
                doubles_entity.get_player(1).add_game(game, PlayingEntity.PlayType.DOUBLES)
                doubles_entity.get_player(2).add_game(game, PlayingEntity.PlayType.DOUBLES)
            # Set how many doubles games each singles player have played as of this league match index
            for entity in self.iter_playing_entities(PlayingEntity.PlayType.SINGLES):
                self._players_matches_played[play_type][entity.get_name()][self._match_index[play_type]] = \
                    entity.get_nb_match_played(play_type)

        # How many games have each playing entity played as of this league's match index
        for entity in self.iter_playing_entities(play_type):
            self._players_matches_played[play_type][entity.get_name()][self._match_index[play_type]] = \
                entity.get_nb_match_played(play_type)

    def get_player_matches_played(self, league_match_index: int,
                                  play_type: PlayingEntity.PlayType,
                                  player: str):
        """
        Returns the number of matches a player has played at the time the league has hit 'league_match_index'
        :param league_match_index: league match index for which player's number of played matches is requested
        :param play_type: singles or doubles
        :param player: name
        :return:
        """
        if league_match_index == -1:
            league_match_index = self._match_index[play_type]
        return self._players_matches_played[play_type][player][league_match_index]

    def fill_in_the_blanks(self, match_index, play_type):
        for playing_entity_name in self._playing_entity[play_type]:
            entity = self._name_to_entity[playing_entity_name]
            player_match_index = self.get_player_matches_played(match_index, play_type, entity.get_name())
            entity.fill_in_the_blanks(player_match_index, play_type)

    def get_playing_entity(self, name):
        if name not in self._name_to_entity:
            raise Exception("Playing entity %s does not exist!" % name)
        entity = self._name_to_entity[name]
        return self._playing_entity[entity.get_type()][name]

    def iter_games(self, play_type: PlayingEntity.PlayType):
        """
        Cycles over the games from oldest to newest for given play type
        """
        for match_index in sorted(self._games[play_type].keys()):
            yield self._games[play_type][match_index]

    def iter_playing_entities(self, play_type: PlayingEntity.PlayType):
        for name in self._playing_entity[play_type].keys():
            yield self._playing_entity[play_type][name]

    def get_league_average_points_per_match(self, match_index: int, play_type: PlayingEntity.PlayType, data=None):
        league_points = 0
        league_match_played = 0
        games_won = 0
        games_lost = 0

        for player in self.iter_playing_entities(play_type):
            player_matches_played = self.get_player_matches_played(match_index, play_type, player.get_name())
            player_points = player.get_cumulative_points(player_matches_played, play_type)
            if player_matches_played == 0:
                continue
            league_points += player_points
            league_match_played += player_matches_played
            games_won += player.get_cumulative_games_won(player_matches_played, play_type)
            games_lost += player.get_cumulative_games_lost(player_matches_played, play_type)

        # Matches are counted twice for the league, once for each playing entity, so divide by 2
        league_match_played = int(league_match_played/2)

        if data is not None:
            data['league_points'] = league_points
            data['league_matches'] = int(league_match_played)
            data['games_won'] = games_won
            data['games_lost'] = games_lost
            data['total_games'] = games_won + games_lost
            try:
                data['games_percent'] = games_won/data['total_games']
            except ZeroDivisionError:
                data['games_percent'] = 0

        try:
            avg = league_points/league_match_played
        except ZeroDivisionError:
            avg = 0
        return avg

    def generate_doubles_team_combination(self):
        logger.debug("############################################")
        logger.debug("Creating all possible combination of doubles")
        logger.debug("team based on list of singles players")
        logger.debug("############################################")
        singles_type = PlayingEntity.PlayType.SINGLES
        singles_players = []
        for playing_entity in self.iter_playing_entities(singles_type):
            singles_players.append(playing_entity)

        singles_players = sorted(singles_players)

        for i in range(0, len(singles_players) - 1):
            for j in range(i + 1, len(singles_players)):
                play_level_scoring_factor = singles_players[i].get_play_level_scoring_factor(singles_type, 0) * \
                    singles_players[j].get_play_level_scoring_factor(singles_type, 0)

                team = DoublesTeam(singles_players[i], singles_players[j],
                                   play_level_scoring_factor, 1, 0)
                if team.get_name() not in self._playing_entity[PlayingEntity.PlayType.DOUBLES]:
                    self.add_playing_entity(team)
                logger.debug("  Doubles team created: %s" % team.get_name())

    def get_doubles_team(self, player_name_1, player_name_2):
        for team_name in self._playing_entity[PlayingEntity.PlayType.DOUBLES]:
            team = self._playing_entity[PlayingEntity.PlayType.DOUBLES][team_name]
            if team.is_in_team(player_name_1) and team.is_in_team(player_name_2):
                return team
        raise Exception("Team composed of %s and %s does not exist!" % (player_name_1, player_name_2))

    def reset_rankings(self, play_type: PlayingEntity.PlayType):
        for entity in self._name_to_entity.values():
            if entity.get_type() == play_type:
                entity.reset_rankings(play_type)

    def reset_points(self, play_type: PlayingEntity.PlayType):
        for entity in self._name_to_entity.values():
            if entity.get_type() == play_type:
                entity.reset_points(play_type)


class LeagueStatsPrinter:
    def __init__(self, league: League, player_filter: list):
        self._league = league
        self._player_filter = player_filter

    def _get_largest_score_width(self,
                                 play_type: PlayingEntity.PlayType,
                                 match_index: int,
                                 rankings: dict):
        largest_score_width = 0
        for r in sorted(rankings.keys()):
            for entity in rankings[r]:
                match_played = self._league.get_player_matches_played(match_index, play_type, entity.get_name())
                points = entity.get_cumulative_points(match_played, play_type)
                l = len("{:.3f}".format(points))
                if l > largest_score_width:
                    largest_score_width = l
        return largest_score_width

    def _process_rankings(self,
                          play_type: PlayingEntity.PlayType,
                          match_index: int,
                          rankings: dict):
        for playing_entity in self._league.iter_playing_entities(play_type):
            player_index = self._league.get_player_matches_played(match_index, play_type, playing_entity.get_name())
            r = playing_entity.get_ranking(player_index, play_type)

            if r not in rankings:
                rankings[r] = []

            rankings[r].append(playing_entity)

    def _format_setup(self,
                      play_type: PlayingEntity.PlayType,
                      match_index: int,
                      rankings: dict):
        header_name_index = 1
        header_points_index = 4

        longest_name_length = 0
        for name in [i.get_name() for i in self._league.iter_playing_entities(play_type)] + ['league']:
            if len(name) > longest_name_length:
                longest_name_length = len(name)

        headers = ["Rank", "Name", "Play Level", "Points/Match", "Points", "Matches Played", "Games Won",
                   "Games Lost", "% games won"]
        headers_length = [len(i) for i in headers]
        headers_length[header_name_index] = longest_name_length
        headers_length[header_points_index] = self._get_largest_score_width(play_type, match_index, rankings)
        headers_length = [i+2 for i in headers_length]

        header_format_str = "{{:<{:d}s}} {{:<{:d}s}} {{:>{:d}s}} {{:>{:d}s}} {{:>{:d}s}}   {{:<{:d}s}} " + \
                            "{{:<{:d}s}} {{:<{:d}s}} {{:>{:d}s}}"
        header_format_str = header_format_str.format(*headers_length)
        header_str = header_format_str.format(*headers)

        rank_format = "{{rank:<{:d}d}} {{name:<{:d}s}} {{play_level:>{:d}.3f}} {{ppm:{:d}.3f}} " + \
                      "{{points:>{:d}.3f}}   {{match_played:<{:d}d}} {{games_won:<{:d}d}} " + \
                      "{{games_lost:<{:d}d}} {{games_won_percent:>{:d}.3f}}"
        rank_format = rank_format.format(*headers_length)

        return header_str, rank_format

    def _in_filter(self,
                   entity):
        def _in_list(playing_entity):
            if str(playing_entity) in self._player_filter:
                return True
            else:
                return False

        if self._player_filter == []:
            return True

        if isinstance(entity, str) or isinstance(entity, Player):
            if _in_list(entity):
                return True
            return False
        else:
            for i in range(1,3):
                player = entity.get_player(i)
                if _in_list(player):
                    return True
            return False

    def print_rankings(self,
                       play_type: PlayingEntity.PlayType,
                       title:str,
                       match_index=-1):
        """
        Print ranking for given match index.
        Prints latest ranking if not parameter is specified.
        """
        if match_index == -1:
            match_index = self._league.last_match_index(play_type)
        if match_index > self._league.last_match_index(play_type):
            match_index = self._league.last_match_index(play_type)

        rankings = dict()
        self._process_rankings(play_type, match_index, rankings)
        header, ranking_format = self._format_setup(play_type, match_index, rankings)

        print('-'*len(header))
        print(title)
        print('-'*len(header))
        print(header)
        for rank in sorted(rankings.keys()):
            for entity in rankings[rank]:
                if not self._in_filter(entity):
                    continue

                match_played = self._league.get_player_matches_played(match_index, play_type, entity.get_name())
                if match_index != 0 and match_played == 0:
                    continue
                games_won = entity.get_cumulative_games_won(match_played, play_type)
                games_lost = entity.get_cumulative_games_lost(match_played, play_type)
                try:
                    games_won_percent = float(games_won) / (games_won + games_lost) * 100
                except ZeroDivisionError:
                    games_won_percent = 0
                points = entity.get_cumulative_points(match_played, play_type)
                try:
                    ppm = points/match_played
                except ZeroDivisionError:
                    ppm = 0

                print(ranking_format.format(rank=rank,
                                            name=entity.get_name(),
                                            play_level=entity.get_play_level_scoring_factor(play_type, match_played),
                                            ppm=ppm,
                                            points=points,
                                            match_played=match_played,
                                            games_won=games_won,
                                            games_lost=games_lost,
                                            games_won_percent=games_won_percent))

        data = dict()
        ppm = self._league.get_league_average_points_per_match(match_index, play_type, data)
        try:
            games_won_percent = data['games_won']/data['total_games']*100
        except ZeroDivisionError:
            games_won_percent = 0

        print('-'*len(header))
        print(ranking_format.format(rank=0,
                                    name='league',
                                    play_level=0,
                                    ppm=ppm,
                                    points=data['league_points'],
                                    match_played=data['league_matches'],
                                    games_won=data['games_won'],
                                    games_lost=data['games_lost'],
                                    games_won_percent=games_won_percent))

    def print_games(self,
                    play_type: PlayingEntity.PlayType,
                    match_index=-1):
        print("----------------------------------------------------------------------")
        print("MATCH PLAYED")
        print("----------------------------------------------------------------------")
        index = 0
        if match_index == -1:
            match_index = self._league.last_match_index(play_type)
        if match_index > self._league.last_match_index(play_type):
            match_index = self._league.last_match_index(play_type)

        for game in self._league.iter_games(play_type):
            in_filter = False
            for player in game.get_players_list():
                if self._in_filter(player):
                    in_filter = True
                    break

            if not in_filter:
                continue

            index += 1
            print(game)
            if index >= match_index:
                break
        print()


class LeagueDoublesStatsPerPlayerPrinter(LeagueStatsPrinter):
    def __init__(self, tennis_league: League, player_filter: list):
        super(LeagueDoublesStatsPerPlayerPrinter, self).__init__(tennis_league, player_filter)

    def _process_rankings(self,
                          play_type: PlayingEntity.PlayType,
                          match_index: int,
                          rankings: dict):

        for playing_entity in self._league.iter_playing_entities(PlayingEntity.PlayType.SINGLES):
            player_index = self._league.get_player_matches_played(match_index,
                                                                  PlayingEntity.PlayType.DOUBLES,
                                                                  playing_entity.get_name())
            r = playing_entity.get_ranking(player_index, PlayingEntity.PlayType.DOUBLES)

            if r not in rankings:
                rankings[r] = []

            rankings[r].append(playing_entity)


class ScoreProcessor:
    def __init__(self,
                 league: League,
                 points_per_game: int,
                 ranking_factor_constant: float,
                 ranking_diff_factor_constant: float,
                 league_break_in_score_factor: float,
                 ranking_factor_break_in_period: int,
                 ignore_ranking_factors: bool):
        self._league = league
        self._points_per_game = points_per_game
        self._ranking_factor_constant = ranking_factor_constant
        self._ranking_diff_factor_constant = ranking_diff_factor_constant
        self._ranking_factor_break_in_period = ranking_factor_break_in_period
        self._ignore_ranking_factors = ignore_ranking_factors
        self._league_break_in_score_factor = league_break_in_score_factor

        self._player_filter = []
        self._game_breaking_in_flag = False

    def set_player_filter(self, player_filter: list):
        """
        Restricts debugging information output to listed players (needs -v option)
        :param player_filter:
        :return:
        """
        self._player_filter = player_filter

    def _process_ranks(self,
                       play_type: PlayingEntity.PlayType,
                       league_match_index: int):
        """
        Ranking is based on points per match average
        """
        players_points = dict()

        for entity in self._league.iter_playing_entities(play_type):
            player_matches_played = self._league.get_player_matches_played(league_match_index,
                                                                           play_type,
                                                                           entity.get_name())
            # If player has not played any games, don't set rank
            if player_matches_played == 0:
                continue

            # get total number of points up to match index
            points_per_match = entity.get_cumulative_points(player_matches_played, play_type)/player_matches_played
            if points_per_match not in players_points:
                players_points[points_per_match] = []

            players_points[points_per_match].append(entity)

        rank = 1
        for score in sorted(players_points.keys(), reverse=True):
            # Set the player ranking for current match index
            for entity in players_points[score]:
                player_match_index = self._league.get_player_matches_played(league_match_index,
                                                                            play_type,
                                                                            entity.get_name())
                entity.set_rank(player_match_index, rank, play_type)

            rank += 1

    def _print_debug(self, player1, player2, league_match_index, play_type, compute_data):

        if not logger.isEnabledFor(logging.DEBUG):
            return

        if self._player_filter != [] and \
           player1.get_name() not in self._player_filter and \
           player2.get_name() not in self._player_filter:
            return

        p1_match_played = self._league.get_player_matches_played(league_match_index, play_type, player1.get_name())
        p2_match_played = self._league.get_player_matches_played(league_match_index, play_type, player2.get_name())

        logger.debug("######################################################")
        logger.debug("Stats for game prior to current one")
        logger.debug("League match index: %d" % league_match_index)
        logger.debug("Player 1 match index: %d" % p1_match_played)
        logger.debug("Player 2 match index: %d" % p2_match_played)
        logger.debug("Ranking breaking in (factors == 1 if True) %s" % self._game_breaking_in_flag)
        logger.debug("-------------------")
        logger.debug("%-20s %16s %16s" % ("Players", player1.get_name(), player2.get_name()))
        logger.debug("%-20s %16d %16d" % ("Match Played", p1_match_played, p2_match_played))
        logger.debug("%-20s %16.3f %16.3f" % ("Points yet", player1.get_cumulative_points(p1_match_played-1, play_type),
                     player2.get_cumulative_points(p2_match_played-1, play_type)))
        logger.debug("%-20s %16d %16d" % ("Ranking", player1.get_ranking(p1_match_played-1, play_type),
                     player2.get_ranking(p2_match_played-1, play_type)))
        logger.debug("-------------------")
        logger.debug("Status for current match index")
        logger.debug("%-20s %16d %16d" % ("Games Won", compute_data['won'][1], compute_data['won'][2]))
        logger.debug("%-20s %16.3f %16.3f" % ("Ranking Factor", compute_data['ranking_factors']['p1_ranking_factor'],
                     compute_data['ranking_factors']['p2_ranking_factor']))
        logger.debug("%-20s %16.3f %16.3f" % ("Diff Ranking Factor",
                     compute_data['ranking_factors']['p1_diff_ranking_factor'],
                     compute_data['ranking_factors']['p2_diff_ranking_factor']))
        logger.debug("%-20s %16.3f %16.3f" % ("Base Points", compute_data['points'][1], compute_data['points'][2]))
        logger.debug("%-20s %16.3f %16.3f" % ("Points Earned", compute_data['earned'][1], compute_data['earned'][2]))

    def _set_ranking_factors(self, prior_match_index: int,
                             player1: PlayingEntity,
                             player2: PlayingEntity,
                             compute_data: dict):
        play_type = compute_data['play_type']

        # Until all players have played at least x games, rankings are not a factor in calculating points.
        # If "ignore ranking factor" is set, same thing.
        if self._ignore_ranking_factors or self._game_breaking_in_flag:
            compute_data['ranking_factors']['p1_ranking_factor'] = 1
            compute_data['ranking_factors']['p2_ranking_factor'] = 1
            compute_data['ranking_factors']['p1_diff_ranking_factor'] = 1
            compute_data['ranking_factors']['p2_diff_ranking_factor'] = 1
            compute_data['ranking_factors']['league_break_in_score_factor'] = self._league_break_in_score_factor
        else:
            p1_average_ppm = player1.get_average_points_per_match(prior_match_index, play_type)
            p2_average_ppm = player2.get_average_points_per_match(prior_match_index, play_type)
            league_average_ppm = self._league.get_league_average_points_per_match(prior_match_index, play_type)

            compute_data['ranking_factors']['avg_divider'] = league_average_ppm

            # League leader is the one with the highest ranking factor and earns more points for same results as another
            # player.
            compute_data['ranking_factors']['p1_ranking_factor'] = \
                p1_average_ppm / compute_data['ranking_factors']['avg_divider'] * self._ranking_factor_constant

            compute_data['ranking_factors']['p2_ranking_factor'] = \
                p2_average_ppm / compute_data['ranking_factors']['avg_divider'] * self._ranking_factor_constant

            # The stronger you are compared to your opponent, the least point you earn per games won.
            compute_data['ranking_factors']['p1_diff_ranking_factor'] = self._ranking_diff_factor_constant / \
                (p1_average_ppm / p2_average_ppm)
            compute_data['ranking_factors']['p2_diff_ranking_factor'] = self._ranking_diff_factor_constant / \
                (p2_average_ppm / p1_average_ppm)
            # Break in inactive, set to 1
            compute_data['ranking_factors']['league_break_in_score_factor'] = 1

    def _set_points_data(self, compute_data, game, player1, player2):
        play_type = compute_data['play_type']
        match_index_1 = compute_data['match_played'][1]
        match_index_2 = compute_data['match_played'][2]

        compute_data['level_score_factor'] = dict()
        compute_data['level_score_factor'][1] = player1.get_play_level_scoring_factor(play_type, match_index_1)
        compute_data['level_score_factor'][2] = player2.get_play_level_scoring_factor(play_type, match_index_2)

        p1_won_games = game.get_games_won(player1.get_name())
        p2_won_games = game.get_games_won(player2.get_name())
        total_games_played = p1_won_games + p2_won_games

        p1_points = p1_won_games/total_games_played*self._points_per_game
        p2_points = p2_won_games/total_games_played*self._points_per_game

        p1_earned_points = p1_points * compute_data['ranking_factors']['p1_ranking_factor'] * \
            compute_data['ranking_factors']['p1_diff_ranking_factor'] * \
            compute_data['ranking_factors']['league_break_in_score_factor'] * \
            compute_data['level_score_factor'][1]

        p2_earned_points = p2_points * compute_data['ranking_factors']['p2_ranking_factor'] * \
            compute_data['ranking_factors']['p2_diff_ranking_factor'] * \
            compute_data['ranking_factors']['league_break_in_score_factor'] * \
            compute_data['level_score_factor'][2]

        compute_data['won'] = dict()
        compute_data['won'][1] = p1_won_games
        compute_data['won'][2] = p2_won_games
        compute_data['total_games'] = total_games_played
        compute_data['points'] = dict()
        compute_data['points'][1] = p1_points
        compute_data['points'][2] = p1_points
        compute_data['earned'] = dict()
        compute_data['earned'][1] = p1_earned_points
        compute_data['earned'][2] = p2_earned_points

    def _set_individual_player_doubles_stats(self, compute_data: dict, teams: list, league_match_index: int):
        for team_index in range(0, 2):
            team_earned_points = compute_data['earned'][team_index+1]
            for player_index in range(1, 3):
                player = teams[team_index].get_player(player_index)
                player_doubles_played = self._league.get_player_matches_played(league_match_index,
                                                                               PlayingEntity.PlayType.DOUBLES,
                                                                               player.get_name())
                player.set_game_points(player_doubles_played, team_earned_points, PlayingEntity.PlayType.DOUBLES)

    def compute(self, last_match_index: int, play_type: PlayingEntity.PlayType):
        if last_match_index == -1:
            last_match_index = self._league.last_match_index(play_type)
        elif last_match_index > self._league.last_match_index(play_type):
            last_match_index = self._league.last_match_index(play_type)

        if last_match_index == 0:
            return

        self._league.reset_points(play_type)

        prior_match_index = 0
        current_match_index = 1

        for game in self._league.iter_games(play_type):
            if current_match_index > last_match_index:
                break

            compute_data = dict()
            compute_data['ranking_factors'] = dict()
            compute_data['play_type'] = play_type

            # Each game modifies the rankings for players who have not played as many games as others,
            # so reset the rankings
            self._league.reset_rankings(play_type)

            playing_entity_1 = self._league.get_playing_entity(game.get_name(1))
            playing_entity_2 = self._league.get_playing_entity(game.get_name(2))

            compute_data['match_played'] = dict()
            for i in range(1, 3):
                compute_data['match_played'][i] = self._league.get_player_matches_played(prior_match_index,
                                                                                         play_type,
                                                                                         game.get_name(i))

            self._game_breaking_in_flag = compute_data['match_played'][1] < self._ranking_factor_break_in_period or \
                compute_data['match_played'][2] < self._ranking_factor_break_in_period

            self._set_ranking_factors(prior_match_index,
                                      playing_entity_1,
                                      playing_entity_2,
                                      compute_data)

            self._set_points_data(compute_data, game, playing_entity_1, playing_entity_2)

            playing_entity_1.set_game_points(compute_data['match_played'][1]+1, compute_data['earned'][1], play_type)
            playing_entity_2.set_game_points(compute_data['match_played'][2]+1, compute_data['earned'][2], play_type)

            if play_type == PlayingEntity.PlayType.DOUBLES:
                self._set_individual_player_doubles_stats(compute_data,
                                                          [playing_entity_1, playing_entity_2],
                                                          current_match_index)

            self._league.fill_in_the_blanks(current_match_index, play_type)
            self._process_ranks(play_type, current_match_index)

            self._print_debug(playing_entity_1, playing_entity_2, current_match_index, play_type, compute_data)

            prior_match_index = current_match_index
            current_match_index += 1


class DoublesScorePerPlayerProcessor(ScoreProcessor):
    """
    Computes the doubles score for each player independent of team as we mix and match doubles' team players
    constantly.
    """

    def __init__(self, *_args, **_kwargs):
        super(DoublesScorePerPlayerProcessor, self).__init__(*_args, **_kwargs)

    def _process_doubles_ranks_for_singles(self,
                                           league_match_index: int):
        """
        Ranking is based on points per match average
        """
        players_points = dict()

        for entity in self._league.iter_playing_entities(PlayingEntity.PlayType.SINGLES):
            player_matches_played = self._league.get_player_matches_played(league_match_index,
                                                                           PlayingEntity.PlayType.DOUBLES,
                                                                           entity.get_name())
            # If player has not played any games, don't set rank
            if player_matches_played == 0:
                continue

            # get total number of points up to match index
            points_per_match = entity.get_cumulative_points(player_matches_played,
                                                            PlayingEntity.PlayType.DOUBLES) / player_matches_played
            if points_per_match not in players_points:
                players_points[points_per_match] = []

            players_points[points_per_match].append(entity)

        rank = 1
        for score in sorted(players_points.keys(), reverse=True):
            # Set the player ranking for current match index
            for entity in players_points[score]:
                player_match_index = self._league.get_player_matches_played(league_match_index,
                                                                            PlayingEntity.PlayType.DOUBLES,
                                                                            entity.get_name())
                entity.set_rank(player_match_index, rank, PlayingEntity.PlayType.DOUBLES)

            rank += 1

    def compute(self, last_match_index: int, play_type: PlayingEntity.PlayType):
        # Compute the points for the doubles playing entities, it already takes into account
        # each player's level scoring factor.
        super(DoublesScorePerPlayerProcessor, self).compute(last_match_index, play_type)
        self._process_doubles_ranks_for_singles(last_match_index)


def init_league(csv_file, tennis_league):
    """
    Required format for the CSV file:
    player entry:   Name,initial_ranking,initial_points
    singles entry:  Name1,GamesWon,Name2,GamesWon
    doubles entry:  Name1,Name2,GamesWon,Name3,Name4,GamesWon

    Level represent a scoring factor applied to points earned, shall be 0 < level <=1
    new singles player level entry: Name,Match_index,New_level
    new doubles player level entry: Name,Name2,Match_index,New_level

    Player entries must be listed first, then singles or doubles games.
    """
    # We must initialize Game.LEAGUE before instantiating games!
    Game.LEAGUE = tennis_league

    new_player_re = re.compile(r"^(\S+?),(\d+|(?:\d+\.\d*)),(\d+),(\d+|(?:\d+\.\d*))$")
    singles_entry_re = re.compile(r"^(\S+?),(\d+),(\S+?),(\d+)$")
    doubles_entry_re = re.compile(r"^(\S+?),(\S+?),(\d+),(\S+?),(\S+?),(\d+)$")
    new_singles_level_re = re.compile(r"^singles-level,(\S+?),(\d+),(\d+|(?:\d+\.\d*))$")
    new_doubles_level_re = re.compile(r"^doubles-level,(\S+?),(\S+?),(\d+),(\d+|(?:\d+\.\d*))$")

    with open(csv_file, 'r') as fd:
        doubles_team_generated = False
        line_nb = 0
        for line in fd:
            line_nb += 1
            line = line.strip()
            line = re.sub(r'\s+', '', line)

            try:
                if REPLACEMENT_PLAYER_PREFIX in line or REPLACEMENT_PLAYER_PREFIX.lower() in line:
                    logger.info("CSV entry '%s' skipped as a replacement played" % line)
                    continue

                new_player = new_player_re.fullmatch(line)
                singles_match = singles_entry_re.fullmatch(line)
                doubles_match = doubles_entry_re.fullmatch(line)
                updated_singles_player_level = new_singles_level_re.fullmatch(line)
                updated_doubles_player_level = new_doubles_level_re.fullmatch(line)

                if new_player:
                    name = new_player.group(1)
                    level_scoring_factor = (float(new_player.group(2)))
                    initial_ranking = int(new_player.group(3))
                    initial_points = float(new_player.group(4))
                    tennis_league.add_playing_entity(Player(name, level_scoring_factor,
                                                            initial_ranking, initial_points))
                elif doubles_match:
                    if not doubles_team_generated:
                        tennis_league.generate_doubles_team_combination()
                        doubles_team_generated = True
                    player1 = doubles_match.group(1)
                    player2 = doubles_match.group(2)
                    games_won_1 = int(doubles_match.group(3))
                    player3 = doubles_match.group(4)
                    player4 = doubles_match.group(5)
                    games_won_2 = int(doubles_match.group(6))
                    team1 = tennis_league.get_doubles_team(player1, player2)
                    team2 = tennis_league.get_doubles_team(player3, player4)
                    tennis_league.add_game(Game(team1.get_name(), games_won_1, team2.get_name(), games_won_2))
                elif singles_match:
                    if not doubles_team_generated:
                        tennis_league.generate_doubles_team_combination()
                        doubles_team_generated = True
                    player1 = singles_match.group(1)
                    games_won_1 = int(singles_match.group(2))
                    player2 = singles_match.group(3)
                    games_won_2 = int(singles_match.group(4))
                    tennis_league.add_game(Game(player1, games_won_1, player2, games_won_2))
                elif updated_doubles_player_level:
                    entity = tennis_league.get_playing_entity(updated_doubles_player_level.group(1))
                    entity2 = tennis_league.get_playing_entity(updated_doubles_player_level.group(2))
                    team = tennis_league.get_doubles_team(entity.get_name(), entity2.get_name())
                    team.update_play_level_scoring_factor(float(updated_doubles_player_level.group(4)),
                                                          PlayingEntity.PlayType.DOUBLES,
                                                          int(updated_doubles_player_level.group(3)))
                elif updated_singles_player_level:
                    entity = tennis_league.get_playing_entity(updated_singles_player_level.group(1))
                    entity.update_play_level_scoring_factor(float(updated_singles_player_level.group(3)),
                                                            PlayingEntity.PlayType.SINGLES,
                                                            int(updated_singles_player_level.group(2)))
                elif line != "":
                    logger.debug("Following line (csv line number:%d) skipped: %s" % (line_nb, line))
            except Exception as e:
                logger.error("ERROR: Line %d in csv. %s" % (line_nb, str(e)))
                raise Exception()


def parse_command_line():
    parser = argparse.ArgumentParser(description='Tennis scoring program proof of concept',
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("csv",
                        type=str,
                        help="CSV file from which to import play results")

    parser.add_argument("--ppp", "--points-per-game",
                        dest="points_per_game",
                        type=int,
                        help="Points earned per game, defaults to %d" %
                             DEFAULT_POINTS_PER_GAME,
                        default=DEFAULT_POINTS_PER_GAME)

    parser.add_argument("--rfc", "--ranking-factor-constant",
                        dest="ranking_factor_constant",
                        type=float,
                        help="Ranking factor constant, higher value favors higher ranked players. Defaults to %2.3f" %
                             RANKING_FACTOR_CONSTANT,
                        default=RANKING_FACTOR_CONSTANT)

    parser.add_argument("--rdfc", "--ranking-diff-factor-constant",
                        dest="ranking_diff_factor_constant",
                        type=float,
                        help="Ranking difference factor constant, higher value favors underdog players. "
                             "Defaults to %2.3f" % RANKING_DIFF_FACTOR_CONSTANT,
                        default=RANKING_DIFF_FACTOR_CONSTANT)

    parser.add_argument("--rfbp", "--ranking-factor-break-in-period",
                        dest="ranking_factor_break_in_period",
                        type=int,
                        help="Number of games before ranking factors have an impact. Defaults to %d games." %
                             RANKING_FACTOR_BREAK_IN_PERIOD,
                        default=RANKING_FACTOR_BREAK_IN_PERIOD)

    parser.add_argument("--lbsf", "--league-break-in-score-factor",
                        dest="league_break_in_score_factor",
                        type=float,
                        help="During league ranking break in period, scores are multiplied by this factor to "
                             "mitigate their impact. Defaults to %2.3f. I suggest a value of 0.1" %
                             LEAGUE_BREAK_IN_SCORE_FACTOR,
                        default=LEAGUE_BREAK_IN_SCORE_FACTOR)

    parser.add_argument("-i", "--ignore-ranking-factors",
                        dest="ignore_ranking_factors",
                        action="store_true",
                        help="Points earned are not affected by ranking factors, no matter the other options."
                             "Defaults to False.",
                        default=False)

    parser.add_argument("-m", "--match-index",
                        dest="match_index",
                        type=int,
                        help="Print results as of specified league match index. If none specified, prints "
                             "latest results.",
                        default=-1)

    parser.add_argument("--doubles",
                        dest="doubles",
                        action="store_true",
                        help="Print results for doubles, default to singles.",
                        default=False)

    parser.add_argument("-v", "--verbose",
                        dest="verbose",
                        action="store_true",
                        help="Print debug chatter.",
                        default=False)

    parser.add_argument("-p", "--player-filter",
                        dest="player_filter",
                        action='append',
                        help="Print information only for selected players, can be used multiple times (needs -v)",
                        default=[])

    parser.epilog = """Demo program for processing scores in a league with players of varied levels. Note
that the data has been pre populated. You can always modify the script to change it. Eventually, if the program
is deemed acceptable, a CSV importer/exporter could be easily added.

ALGORITHM:

- Ranking is based on points per game average.
- Points earned for a given game depends on your average performance compared to that of the league.

The equations used to calculate points are:

    points_per_game     = cumulative_points / number_of_games_played
    points              = games_won/total_games_played * points_per_game

    self_avg            = self_cumulative_points / self_number_played_games
    opponent_avg        = opponent_cumulative_points / opponent_number_played_games

    avg_divider     = league_players_cumulative_points / league_players_number_played_games

    ranking_factor      = self_avg/avg_divider * ranking_factor_constant
    diff_ranking_factor = ranking_diff_factor_constant/(self_avg/opponent_avg)

    if games played by BOTH players >= ranking_factor_break_in_period
        earned_points = points * ranking_factor * diff_ranking_factor
    else
        earned_points = points

Note: points are calculated considering only games played up to that time. This means that the rankings after 'x'
sessions only take into account points for the first 'x-1' sessions, even though more sessions might have been
played.

PARAMETER DETAILS:

"--ppp", "--points-per-game"
    Purely aesthetic option. Does not affect ranking; just makes it more impressive for everybody to see the amount
    of points they have earned.

"--rfc", "--ranking-factor-constant":
    See equations for details on how it impacts ranking. Higher value favors higher ranked players.

"--rdfc", "--ranking-diff-factor-constant":
    See equations for details on how it impacts ranking. Higher value favors lower ranked players.

"--rfbp", "--ranking-factor-break-in-period":
    The ranking mechanism might give biased results for the initial games. Setting this option requires x number
    of matches by played by all involved players in a match before the ranking algorithm kicks in. In the meantime,
    ranking factors are forced to 1, meaning earned points == games_won/total_games_played * points_per_game.
    To reduce the scoring impact of those initial games, points earned are further divided by the league break in
    score factor ("--lbsf", "--league-break-in-score-factor").

"--lbsf", "--league-break-in-score-factor":
    Factor applied to points earned during the break in period. Should be small =~ 0.1. This is to mitigate the impact
    of the initial games where rankings has not broken in yet.

"-i", "--ignore-ranking-factors":
    Whatever the options set, ranking factors are forced to 1, meaning
    earned points == games_won/total_games_played * points_per_game

EXAMPLES

"""

    arguments = parser.parse_args()

    if arguments.league_break_in_score_factor > 0.5:
        logger.error("League break in score factor --lbsf can't be set above 0.5.")

    if arguments.verbose:
        logger.setLevel(logging.DEBUG)

    return arguments


def main(main_args):
    play_type = PlayingEntity.PlayType.SINGLES
    if main_args.doubles:
        play_type = PlayingEntity.PlayType.DOUBLES

    tennis_league = League()

    init_league(main_args.csv, tennis_league)

    processor_type = ScoreProcessor
    if play_type == PlayingEntity.PlayType.DOUBLES:
        processor_type = DoublesScorePerPlayerProcessor

    s = processor_type(league=tennis_league,
                       points_per_game=main_args.points_per_game,
                       ranking_factor_constant=main_args.ranking_factor_constant,
                       ranking_diff_factor_constant=main_args.ranking_diff_factor_constant,
                       league_break_in_score_factor=main_args.league_break_in_score_factor,
                       ranking_factor_break_in_period=main_args.ranking_factor_break_in_period,
                       ignore_ranking_factors=main_args.ignore_ranking_factors)
    s.set_player_filter(main_args.player_filter)
    s.compute(args.match_index, play_type)

    printer = LeagueStatsPrinter(tennis_league, main_args.player_filter)
    printer.print_games(play_type, main_args.match_index)
    printer.print_rankings(play_type, "%s stats" % play_type, main_args.match_index)

    if play_type == PlayingEntity.PlayType.DOUBLES:
        printer = LeagueDoublesStatsPerPlayerPrinter(tennis_league, main_args.player_filter)
        printer.print_rankings(play_type, "DOUBLES stats for each singles player", main_args.match_index)

if __name__ == "__main__":
    import sys

    args = parse_command_line()
    try:
        main(args)
    except Exception as global_e:
        logger.error(str(global_e))

        if args.verbose:
            import traceback
            traceback.print_exc()

        sys.exit(1)

    sys.exit(0)
