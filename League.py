import sys

from DoublesTeam import *
from exceptions import PlayingEntityAlreadyExistsError, PlayingEntityDoesNotExistError, UnforseenError
from utils import LoggerHandler

logger = LoggerHandler.get_instance().get_logger("League")


class League:
    _SINGLETON = None

    @staticmethod
    def get_instance():
        return League._SINGLETON

    def __init__(self):
        if League.get_instance() is not None:
            logger.error("Can only instantiate one league")
            sys.exit(1)

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

        League._SINGLETON = self

    def last_match_index(self, play_type: PlayingEntity.PlayType):
        if len(self._games[play_type].keys()) == 0:
            return 0
        return max(self._games[play_type].keys())

    def playing_entity_name_exists(self, playing_entity_name: str):
        if playing_entity_name.lower() in self._name_to_entity:
            return True
        return False

    def add_playing_entity(self, playing_entity: PlayingEntity):
        if playing_entity.get_name() in self._name_to_entity:
            raise PlayingEntityAlreadyExistsError("Player already exist")

        self._playing_entity[playing_entity.get_type()][playing_entity.get_name()] = playing_entity
        self._name_to_entity[playing_entity.get_name()] = playing_entity

        self._players_matches_played[playing_entity.get_type()][playing_entity.get_name()] = dict()
        self._players_matches_played[playing_entity.get_type()][playing_entity.get_name()][0] = 0

        # If playing entity is SINGLES, also add place holder for doubles information
        if playing_entity.get_type() == PlayingEntity.PlayType.SINGLES:
            self._players_matches_played[PlayingEntity.PlayType.DOUBLES][playing_entity.get_name()] = dict()
            self._players_matches_played[PlayingEntity.PlayType.DOUBLES][playing_entity.get_name()][0] = 0

    def add_game(self, game: BaseGame):
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

        if player not in self._players_matches_played[play_type]:
            raise PlayingEntityDoesNotExistError("Player %s not registered for %s" % (player, play_type))

        if league_match_index not in self._players_matches_played[play_type][player]:
            if len(self._players_matches_played[play_type][player]) != 0:
                raise UnforseenError("League match index should have been found.")
            return 0

        return self._players_matches_played[play_type][player][league_match_index]

    def fill_in_the_blanks(self, match_index, play_type):
        for playing_entity_name in self._playing_entity[play_type]:
            entity = self._name_to_entity[playing_entity_name]
            player_match_index = self.get_player_matches_played(match_index, play_type, entity.get_name())
            entity.fill_in_the_blanks(player_match_index, play_type)

    def get_playing_entity(self, name):
        if name not in self._name_to_entity:
            raise PlayingEntityDoesNotExistError("Playing entity %s does not exist!" % name)
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
