#!/usr/bin/env python3.6
import argparse
from Game import *
from ScoreProcessor import *
from StatsPrinter import *
from Player import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("score")
logger.setLevel(logging.DEBUG)

DEFAULT_POINTS_PER_GAME = 100
RANKING_FACTOR_CONSTANT = 1.0
RANKING_DIFF_FACTOR_CONSTANT = 1.0
RANKING_FACTOR_BREAK_IN_PERIOD = 3
LEAGUE_BREAK_IN_SCORE_FACTOR = 0.1
REPLACEMENT_PLAYER_PREFIX = 'RPL'


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

    if arguments.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if arguments.league_break_in_score_factor > 0.5:
        logger.error("League break in score factor --lbsf can't be set above 0.5.")

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

    printer = StatsPrinter(tennis_league, main_args.player_filter)
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
