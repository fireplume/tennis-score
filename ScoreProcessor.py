from League import *
import logging
from utils import LoggerHandler

logger = LoggerHandler.get_instance().get_logger("ScoreProcessor")


class ScoreProcessor:
    def __init__(self,
                 league: League,
                 points_per_match: int,
                 ranking_factor_constant: float,
                 ranking_diff_factor_constant: float,
                 league_break_in_score_factor: float,
                 ranking_factor_break_in_period: int,
                 ignore_ranking_factors: bool):
        self._league = league
        self._points_per_match = points_per_match
        self._ranking_factor_constant = ranking_factor_constant
        self._ranking_diff_factor_constant = ranking_diff_factor_constant
        self._ranking_factor_break_in_period = ranking_factor_break_in_period
        self._ignore_ranking_factors = ignore_ranking_factors
        self._league_break_in_score_factor = league_break_in_score_factor

        self._player_filter = []

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

        p1_match_played = compute_data['match_played'][1]
        p2_match_played = compute_data['match_played'][2]

        logger.debug("######################################################")
        logger.debug("Stats for game prior to current one")
        logger.debug("League match index: %d" % league_match_index)
        logger.debug("Player 1 match index: %d" % p1_match_played)
        logger.debug("Player 2 match index: %d" % p2_match_played)
        logger.debug("Player 1 ranking break in period: %s" %
                     compute_data['ranking_factors']['league_break_in_score_factor'][1] == 1.0)
        logger.debug("Player 2 ranking break in period: %s" %
                     compute_data['ranking_factors']['league_break_in_score_factor'][2] == 1.0)
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

        compute_data['ranking_factors']['league_break_in_score_factor'] = dict()
        compute_data['ranking_factors']['league_break_in_score_factor'][1] = 1
        compute_data['ranking_factors']['league_break_in_score_factor'][2] = 1

        # If "ignore ranking factor", ranking factors are not a considered in calculating points.
        if self._ignore_ranking_factors or prior_match_index == 0:
            compute_data['ranking_factors']['p1_ranking_factor'] = 1
            compute_data['ranking_factors']['p2_ranking_factor'] = 1
            compute_data['ranking_factors']['p1_diff_ranking_factor'] = 1
            compute_data['ranking_factors']['p2_diff_ranking_factor'] = 1
            if compute_data['ranking_breaking_in'][1]:
                compute_data['ranking_factors']['league_break_in_score_factor'][1] = self._league_break_in_score_factor
            if compute_data['ranking_breaking_in'][2]:
                compute_data['ranking_factors']['league_break_in_score_factor'][2] = self._league_break_in_score_factor
        else:
            p1_average_ppm = player1.get_average_points_per_match(prior_match_index, play_type)
            p2_average_ppm = player2.get_average_points_per_match(prior_match_index, play_type)

            league_average_ppm = self._league.get_league_average_points_per_match(prior_match_index, play_type)
            compute_data['ranking_factors']['avg_divider'] = league_average_ppm

            compute_data['ranking_factors']['p1_ranking_factor'] = \
                p1_average_ppm / compute_data['ranking_factors']['avg_divider'] * self._ranking_factor_constant

            compute_data['ranking_factors']['p2_ranking_factor'] = \
                p2_average_ppm / compute_data['ranking_factors']['avg_divider'] * self._ranking_factor_constant

            # The stronger you are compared to your opponent, the least point you earn per games won.
            try:
                compute_data['ranking_factors']['p1_diff_ranking_factor'] = self._ranking_diff_factor_constant / \
                    (p1_average_ppm / p2_average_ppm)
            except ZeroDivisionError:
                compute_data['ranking_factors']['p1_diff_ranking_factor'] = 1

            try:
                compute_data['ranking_factors']['p2_diff_ranking_factor'] = self._ranking_diff_factor_constant / \
                    (p2_average_ppm / p1_average_ppm)
            except ZeroDivisionError:
                compute_data['ranking_factors']['p2_diff_ranking_factor'] = 1

            # override depending on breaking in flag
            if compute_data['ranking_breaking_in'][1]:
                compute_data['ranking_factors']['p1_ranking_factor'] = 1
                compute_data['ranking_factors']['p1_diff_ranking_factor'] = 1
                compute_data['ranking_factors']['league_break_in_score_factor'][1] = self._league_break_in_score_factor
            if compute_data['ranking_breaking_in'][2]:
                compute_data['ranking_factors']['p2_ranking_factor'] = 1
                compute_data['ranking_factors']['p2_diff_ranking_factor'] = 1
                compute_data['ranking_factors']['league_break_in_score_factor'][2] = self._league_break_in_score_factor

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

        if total_games_played == 0:
            p1_points = 0
            p2_points = 0
        else:
            p1_points = p1_won_games/total_games_played*self._points_per_match
            p2_points = p2_won_games/total_games_played*self._points_per_match

        p1_earned_points = p1_points * compute_data['ranking_factors']['p1_ranking_factor'] * \
            compute_data['ranking_factors']['p1_diff_ranking_factor'] * \
            compute_data['ranking_factors']['league_break_in_score_factor'][1] * \
            compute_data['level_score_factor'][1]

        p2_earned_points = p2_points * compute_data['ranking_factors']['p2_ranking_factor'] * \
            compute_data['ranking_factors']['p2_diff_ranking_factor'] * \
            compute_data['ranking_factors']['league_break_in_score_factor'][2] * \
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

            # Are players in their breaking in mode?
            compute_data['ranking_breaking_in'] = dict()
            compute_data['ranking_breaking_in'][1] = \
                compute_data['match_played'][1] <= self._ranking_factor_break_in_period
            compute_data['ranking_breaking_in'][2] = \
                compute_data['match_played'][2] <= self._ranking_factor_break_in_period

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
