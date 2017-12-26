from StatsPrinter import *
from Player import *
from League import *


class StatsPrinter:
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

        if not self._player_filter:
            return True

        if isinstance(entity, str) or isinstance(entity, Player):
            if _in_list(entity):
                return True
            return False
        else:
            for i in range(1, 3):
                player = entity.get_player(i)
                if _in_list(player):
                    return True
            return False

    def print_rankings(self,
                       play_type: PlayingEntity.PlayType,
                       title: str,
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

            index += 1

            if not in_filter:
                continue

            print(game)

            if index >= match_index:
                break
        print()


class LeagueDoublesStatsPerPlayerPrinter(StatsPrinter):
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
