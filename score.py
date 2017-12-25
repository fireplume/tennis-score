#!/usr/bin/env python3.6
import argparse
from ScoreProcessor import *
from StatsPrinter import *
from Player import *
import importer.csv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("score")
logger.setLevel(logging.DEBUG)

DEFAULT_POINTS_PER_GAME = 100
RANKING_FACTOR_CONSTANT = 1.0
RANKING_DIFF_FACTOR_CONSTANT = 1.0
RANKING_FACTOR_BREAK_IN_PERIOD = 3
LEAGUE_BREAK_IN_SCORE_FACTOR = 0.1


def parse_command_line():
    parser = argparse.ArgumentParser(description='Tennis scoring program proof of concept',
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("-v", "--verbose",
                            dest="verbose",
                            action="store_true",
                            help="Print debug chatter.",
                            default=False)

    subparsers = parser.add_subparsers(help='Use one of the following sub commands to perform the desired task.',
                                       dest='cmd')

    csv_parser = subparsers.add_parser('input_csv', help='Import a CSV.')
    csv_parser.add_argument("csv",
                            type=str,
                            help="CSV file from which to import play results")

    csv_parser.add_argument("--ppp", "--points-per-game",
                            dest="points_per_game",
                            type=int,
                            help="Points earned per game, defaults to %d" %
                                 DEFAULT_POINTS_PER_GAME,
                            default=DEFAULT_POINTS_PER_GAME)

    csv_parser.add_argument("--rfc", "--ranking-factor-constant",
                            dest="ranking_factor_constant",
                            type=float,
                            help="Ranking factor constant, higher value favors higher ranked players. Defaults to %2.3f" %
                                 RANKING_FACTOR_CONSTANT,
                            default=RANKING_FACTOR_CONSTANT)

    csv_parser.add_argument("--rdfc", "--ranking-diff-factor-constant",
                            dest="ranking_diff_factor_constant",
                            type=float,
                            help="Ranking difference factor constant, higher value favors underdog players. "
                                 "Defaults to %2.3f" % RANKING_DIFF_FACTOR_CONSTANT,
                            default=RANKING_DIFF_FACTOR_CONSTANT)

    csv_parser.add_argument("--rfbp", "--ranking-factor-break-in-period",
                            dest="ranking_factor_break_in_period",
                            type=int,
                            help="Number of games before ranking factors have an impact. Defaults to %d games." %
                                 RANKING_FACTOR_BREAK_IN_PERIOD,
                            default=RANKING_FACTOR_BREAK_IN_PERIOD)

    csv_parser.add_argument("--lbsf", "--league-break-in-score-factor",
                            dest="league_break_in_score_factor",
                            type=float,
                            help="During league ranking break in period, scores are multiplied by this factor to "
                                 "mitigate their impact. Defaults to %2.3f. I suggest a value of 0.1" %
                                 LEAGUE_BREAK_IN_SCORE_FACTOR,
                            default=LEAGUE_BREAK_IN_SCORE_FACTOR)

    csv_parser.add_argument("-i", "--ignore-ranking-factors",
                            dest="ignore_ranking_factors",
                            action="store_true",
                            help="Points earned are not affected by ranking factors, no matter the other options."
                                 "Defaults to False.",
                            default=False)

    csv_parser.add_argument("-m", "--match-index",
                            dest="match_index",
                            type=int,
                            help="Print results as of specified league match index. If none specified, prints "
                                 "latest results.",
                            default=-1)

    csv_parser.add_argument("--doubles",
                            dest="doubles",
                            action="store_true",
                            help="Print results for doubles, default to singles.",
                            default=False)

    csv_parser.add_argument("-p", "--player-filter",
                            dest="player_filter",
                            action='append',
                            help="Print information only for selected players, can be used multiple times (needs -v)",
                            default=[])

    csv_parser.add_argument("--list-players",
                            dest="list_players",
                            action="store_true",
                            help="List player in CSV format for easy init of their initial ranking and level score factor.",
                            default=False)

    csv_dump_parser = subparsers.add_parser('demo_csv', help='Dump a demo CSV file.')

    csv_dump_parser.add_argument("--seed",
                                 dest="seed",
                                 type=int,
                                 help="Dumped demo CSV is randomized with this integer seed. Defaults to 0.",
                                 default=0)

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

    if arguments.cmd == "input_csv" and arguments.league_break_in_score_factor > 0.5:
        logger.error("League break in score factor --lbsf can't be set above 0.5.")

    return arguments


def list_players_in_csv_format(tennis_league):
    print("Name,Level_Scoring_Factor,Initial_Ranking,Initial_Points")
    for player in tennis_league.iter_playing_entities(PlayingEntity.PlayType.SINGLES):
        for league_match_index, score_factor in player.iter_play_level_scoring_factor():
            print("%s,%2.3f,%d,%2.3f" % (player.get_name(), score_factor,
                                         player.get_ranking(0, PlayingEntity.PlayType.SINGLES), league_match_index))
            break


def compute_and_show_standings(main_args, tennis_league, play_type):
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


def main(main_args):
    if main_args.cmd == "demo_csv":
        importer.csv.dump_sample(main_args.seed)
    else:
        play_type = PlayingEntity.PlayType.SINGLES
        if main_args.doubles:
            play_type = PlayingEntity.PlayType.DOUBLES

        tennis_league = League()
        importer.csv.init_league(main_args.csv, tennis_league)

        if main_args.list_players:
            list_players_in_csv_format(tennis_league)
        else:
            compute_and_show_standings(main_args, tennis_league, play_type)


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
