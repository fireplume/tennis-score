import sys

from DoublesTeam import *
from utils.exceptions import PlayingEntityAlreadyExistsError, PlayingEntityDoesNotExistError
from utils.utils import LoggerHandler

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
        self._playing_entity[PlayingEntity.PlayType.SINGLES] = set()
        self._playing_entity[PlayingEntity.PlayType.DOUBLES] = set()

        self._matches = dict()
        self._matches[PlayingEntity.PlayType.SINGLES] = dict()
        self._matches[PlayingEntity.PlayType.DOUBLES] = dict()

        self._name_to_entity = dict()

        self._league_match_index = dict()
        self._league_match_index[PlayingEntity.PlayType.SINGLES] = LeagueIndex(0)
        self._league_match_index[PlayingEntity.PlayType.DOUBLES] = LeagueIndex(0)

        League._SINGLETON = self

    # Populating league and matches

    def add_playing_entity(self, playing_entity: PlayingEntity):
        if playing_entity.get_name() in self._name_to_entity:
            raise PlayingEntityAlreadyExistsError("Trying to add a player who already exists: %s" %
                                                  playing_entity.get_name())

        self._playing_entity[playing_entity.play_type].add(playing_entity)
        self._name_to_entity[playing_entity.get_name()] = playing_entity

    def add_match(self, match: BaseMatch):
        p1_entity = self._name_to_entity[match.get_name(1)]
        p2_entity = self._name_to_entity[match.get_name(2)]

        # if p1_entity.play_type != p2_entity.play_type:
        #     raise AussieException("%s%s" %
        #                           ("You can't mix singles and doubles in a Match object!",
        #                            "P1: %s P2: %s" % (p1_entity.get_name(), p2_entity.get_name())))

        play_type = p1_entity.play_type
        self._league_match_index[play_type] += 1

        if self._league_match_index[play_type] in self._matches[play_type].keys():
            raise Exception("Internal error: match overwrite attempt at match index %d" %
                            self._league_match_index[play_type])
        self._matches[play_type][self._league_match_index[play_type].get_locked_copy()] = match

        # Add match to player objects for stats update
        p1_entity.add_match(match, self._league_match_index[play_type])
        p2_entity.add_match(match, self._league_match_index[play_type])

    # Information

    def last_match_index(self, play_type: PlayingEntity.PlayType):
        if len(self._matches[play_type].keys()) == 0:
            return LeagueIndex(-1)
        return max(self._matches[play_type].keys())

    def playing_entity_name_exists(self, playing_entity_name: str):
        if playing_entity_name.lower() in self._name_to_entity:
            return True
        return False

    def get_player_matches_played(self, league_match_index: LeagueIndex,
                                  entity_name: str):
        """
        Returns the number of matches a player has played at the time the league has hit 'league_match_index'
        """
        return self._name_to_entity[entity_name].get_nb_match_played(league_match_index)

    def get_playing_entity(self, name):
        if name not in self._name_to_entity:
            raise PlayingEntityDoesNotExistError("Playing entity %s does not exist!" % name)
        return self._name_to_entity[name]

    def get_league_average_points_per_match(self,
                                            index: LeagueIndex,
                                            play_type: PlayingEntity.PlayType,
                                            data=None):
        """
        This function returns the weighted league average of the player's average points per match.
        """
        league_points = 0
        league_match_played = 0
        games_won = 0
        games_lost = 0

        for player in self.iter_playing_entities(play_type):
            player_matches_played = self.get_player_matches_played(index, player.get_name())
            if player_matches_played == 0:
                continue

            player_points = player.get_cumulative_points(index)
            league_points += player_points

            league_match_played += player_matches_played

            games_won += player.get_cumulative_games_won(index)
            games_lost += player.get_cumulative_games_lost(index)

        if data is not None:
            data['league_points'] = league_points
            # league matches are counted twice, once for each player, so divide by two here
            data['league_matches'] = int(league_match_played/2)
            data['games_won'] = games_won
            data['games_lost'] = games_lost
            data['total_games'] = games_won + games_lost
            try:
                data['games_percent'] = games_won/data['total_games']
            except ZeroDivisionError:
                data['games_percent'] = 0

        try:
            # for the purpose of league average player average points per match, we take the full league match count
            avg = league_points/league_match_played
        except ZeroDivisionError:
            avg = 0

        return avg

    # Resets

    def reset_rankings(self, play_type: PlayingEntity.PlayType):
        for entity in self._playing_entity[play_type]:
            entity.reset_rankings()

    def reset_points(self, play_type: PlayingEntity.PlayType):
        for entity in self._playing_entity[play_type]:
            entity.reset_points()

    # Doubles services

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
                play_level_scoring_factor = singles_players[i].get_play_level_scoring_factor(index=LeagueIndex(0)) * \
                                            singles_players[j].get_play_level_scoring_factor(index=LeagueIndex(0))

                team = DoublesTeam(singles_players[i],
                                   singles_players[j],
                                   initial_points=0.0,
                                   initial_level=play_level_scoring_factor)

                if team.get_name() not in self._playing_entity[PlayingEntity.PlayType.DOUBLES]:
                    self.add_playing_entity(team)

    def get_doubles_team(self, player_name_1, player_name_2):
        team_name = DoublesTeam.get_doubles_team_name_from_player_names(player_name_1, player_name_2)
        if team_name in self._name_to_entity:
            return self._name_to_entity[team_name]
        raise PlayingEntityDoesNotExistError("Team composed of %s and %s does not exist!" % (player_name_1,
                                                                                             player_name_2))

    # Iterators

    def iter_matches(self, play_type: PlayingEntity.PlayType):
        """
        Cycles over the matches from oldest to newest for given play type
        """
        for match_index in sorted(self._matches[play_type].keys()):
            yield self._matches[play_type][match_index]

    def iter_playing_entities(self, play_type: PlayingEntity.PlayType):
        for entity in sorted(self._playing_entity[play_type]):
            yield entity
