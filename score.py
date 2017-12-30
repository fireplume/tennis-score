#!/usr/bin/env python3
import argparse
import logging
import sys

from ScoreProcessor import *
from StatsPrinter import *
from Player import *
import importer.csv
from utils.utils import LoggerHandler, Accepts

logging.basicConfig(level=logging.INFO)
LoggerHandler.set_default_level(level=logging.INFO)
logger = LoggerHandler.get_instance().get_logger("score")

DEFAULT_POINTS_PER_MATCH = 100
RANKING_FACTOR_CONSTANT = 1.0
RANKING_DIFF_FACTOR_CONSTANT = 1.0
RANKING_FACTOR_BREAK_IN_PERIOD = 3
LEAGUE_BREAK_IN_SCORE_FACTOR = 0.1


def parse_command_line(command_line_args=sys.argv[1:]):
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

    csv_parser.add_argument("--ppm", "--points-per-match",
                            dest="points_per_match",
                            type=int,
                            help="Maximum points which can be earned per game, defaults to %d" %
                                 DEFAULT_POINTS_PER_MATCH,
                            default=DEFAULT_POINTS_PER_MATCH)

    csv_parser.add_argument("--rfc", "--ranking-factor-constant",
                            dest="ranking_factor_constant",
                            type=float,
                            help="Ranking factor constant, higher value favors higher ranked players. "
                                 "Defaults to %2.3f" % RANKING_FACTOR_CONSTANT,
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
                            help="Points earned are not affected by ranking factors, no matter the other options. "
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
                            help="List player in CSV format for easy init of their initial ranking and level "
                                 "score factor.",
                            default=False)

    csv_parser.add_argument("--pms", "--print-match-scores",
                            dest="print_match_scores",
                            action="store_true",
                            help="By default, only final stats are printed, use this option to also print match scores.",
                            default=False)

    csv_parser.add_argument("--csv",
                            dest="csv_output",
                            action="store_true",
                            help="Output stats in CSV format to standard output.",
                            default=False)

    csv_dump_parser = subparsers.add_parser('demo_csv', help='Dump a demo CSV file.')

    csv_dump_parser.add_argument("--seed",
                                 dest="seed",
                                 type=int,
                                 help="Dumped demo CSV is randomized with this integer seed. Defaults to 0.",
                                 default=0)

    parser.epilog = """Demo program for processing scores in a league with players of varied levels. You can generate
demo data by running 'score.py demo_csv --seed 0 > test.csv' and then running 'score.py input_csv test.csv'.

This program makes a clear distinction between a match and a game, so pay attention to the wording.

ALGORITHM:

- Ranking is based on points per match average and player level (level_scoring_factor).
- The level scoring factor is to be set in the imported file. If not set, defaults to 1.
- Points earned for a given match depends on your average performance compared to that of the league at the time
of the match and your level (level_scoring_factor, see a CSV file for details).

The player level scoring factor can be modified during the course of the season.

Note that all matches are indexed in this program based on league matches. When referring to a match index
in the CSV file, it must refer to the league match index, not the player's. I could be playing my first match, but
it could very well be the league's fifth match. You don't usually have to bother about that unless you start to
modify a player's level scoring factor, which should correspond to how strong the player is.

The equations used to calculate points for a given match are:

    points_per_match    = cumulative_points / number_of_matches_played
    points              = games_won/total_games_played * points_per_match

    self_avg            = self_cumulative_points / self_number_played_matches
    opponent_avg        = opponent_cumulative_points / opponent_number_played_matches

    avg_divider         = league_players_cumulative_points / league_players_number_matches_played

    ranking_factor      = self_avg/avg_divider * ranking_factor_constant
    diff_ranking_factor = ranking_diff_factor_constant / (self_avg/opponent_avg)

    if player has completed ranking break in period:
        earned_points = points * ranking_factor * diff_ranking_factor * level_scoring_factor
    else
        earned_points = points * league_break_in_score_factor * level_scoring_factor

The 'league_break_in_score_factor' is used to mitigate the impact of the first few games on ranking. You should
set it to a small value (=~ 0.1).

Note how the diff_ranking_factor favors the underdog player in a match. If your average is small compared to your
opponent, '(self_avg/opponent_avg)' is going to be small and  ranking_diff_factor_constant divided by a small number
is going to give an interestingly bigger number than for your opponent. This can be tuned by adjusting 
the 'ranking_diff_factor_constant' on the command line ("--rdfc", "--ranking-factor-break-in-period")

Points are calculated considering only games played up to that moment in time. This means that the rankings after 'x'
league matches only take into account points for the first 'x-1' league matches for all players at that moment.

This also means that until all players have played the same number of games, the rankings may change as some players
get to have played as many games as others. At the end of the season, if not all players have played the same number
of games, it doesn't matter all that much as the average points per match is considered for rankings.

PARAMETER DETAILS:

"--ppm", "--points-per-match"
    Purely aesthetic option. Does not affect ranking; just makes it more impressive for everybody to see the amount
    of points they have earned.

"--rfc", "--ranking-factor-constant":
    See equations for details on how it impacts ranking. Higher value favors higher ranked players.

"--rdfc", "--ranking-diff-factor-constant":
    See equations for details on how it impacts ranking. Higher value favors underdog players during matches.

"--rfbp", "--ranking-factor-break-in-period":
    The ranking mechanism might give biased results for the initial games. Setting this option requires x number
    of matches be played by players in a match before the ranking algorithm kicks in. In the meantime, earned
    points are reduced significantly, see equations for details.

"--lbsf", "--league-break-in-score-factor":
    Factor applied to points earned during the break in period. Should be small =~ 0.1. This is to mitigate the impact
    of the initial games where rankings has not broken in yet.

"-i", "--ignore-ranking-factors":
    Whatever the options set, ranking factors are forced to 1. It doesn't impact the ranking break in period though.
    To disable the latter, use '--rfbp=0' 

EXAMPLES

Print help message

    score.py -h

Print help for 'input_csv' sub command:

    score.py input_csv -h

Print help for 'demo_csv' sub command:

    score.py demo_csv -h

Output to screen demo CSV content (to inspect format accepted by this tool for example).
Set a different seed to generate different results.

    score.py demo_csv --seed 0

Same, but save to a file:
    score.py demo_csv --seed 0 > demo.csv

Default stats output for singles

    score.py input_csv demo.csv

Same, but also print match scores

    score.py input_csv --print-match-scores demo.csv

Default stats output for doubles

    score.py input_csv --doubles demo.csv

Print lots of debugging information; note that position of '-v' parameter is important!!!
The '-v' parameter must come before the sub command ('input_csv' or 'demo_csv')

    score.py -v input_csv demo.csv

Emulate current point system based on games won vs games lost without consideration for performance on player level.

    score.py input_csv --ignore-ranking-factors --ranking-factor-break-in-period=0 demo.csv
"""

    arguments = parser.parse_args(command_line_args)

    error = False

    if arguments.cmd is None:
        parser.print_help()
        sys.exit(0)

    if arguments.verbose:
        LoggerHandler.get_instance().reset_all_level(logging.DEBUG)
        LoggerHandler.set_default_level(logging.DEBUG)

        # When verbose is set, enable type checking decorator.
        Accepts.enable()

    if arguments.cmd == "input_csv":
        if arguments.league_break_in_score_factor > 0.5:
            logger.error("League break in score factor --lbsf can't be set above 0.5.")
            error = True

        if arguments.match_index < 1 and arguments.match_index != -1:
            logger.error("Can't set a match index inferior to 1")
            error = True

    if error:
        sys.exit(1)

    return arguments


def list_players_in_csv_format(tennis_league):
    print()
    print("New player level, Name, league match index to take effect, new level(scoring factor)")
    for player in tennis_league.iter_playing_entities(PlayingEntity.PlayType.SINGLES):
        score_factor = player.get_play_level_scoring_factor(LeagueIndex(0))
        print(importer.csv.SINGLES_NEW_LEVEL_ENTRY_FORMAT.format(name=player.get_name(),
                                                                 new_level=score_factor,
                                                                 league_match_index=1))


def compute_and_show_standings(main_args, tennis_league, play_type):
    processor_type = ScoreProcessor

    s = processor_type(league=tennis_league,
                       points_per_match=main_args.points_per_match,
                       ranking_factor_constant=main_args.ranking_factor_constant,
                       ranking_diff_factor_constant=main_args.ranking_diff_factor_constant,
                       league_break_in_score_factor=main_args.league_break_in_score_factor,
                       ranking_factor_break_in_period=main_args.ranking_factor_break_in_period,
                       ignore_ranking_factors=main_args.ignore_ranking_factors)
    s.set_player_filter(main_args.player_filter)
    s.compute(LeagueIndex(main_args.match_index), play_type)

    if main_args.csv_output:
        printer = CsvStatsPrinter(tennis_league, main_args.player_filter)
    else:
        printer = StatsPrinter(tennis_league, main_args.player_filter)

    if main_args.print_match_scores:
        printer.print_games(play_type, LeagueIndex(main_args.match_index))
    printer.print_rankings(play_type, "%s stats" % play_type, LeagueIndex(main_args.match_index))


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

        # For testing:
        return tennis_league


if __name__ == "__main__":
    _args = parse_command_line()
    try:
        main(_args)
    except Exception as global_e:
        logger.error(str(global_e))
        if _args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    sys.exit(0)
