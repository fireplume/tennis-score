# tennis-score
Python script to process tennis league player scores for singles and doubles

```score.py -h
usage: score.py [-h] [-v] {input_csv,demo_csv} ...

Tennis scoring program proof of concept

positional arguments:
  {input_csv,demo_csv}  Use one of the following sub commands to perform the
                        desired task.
    input_csv           Import a CSV.
    demo_csv            Dump a demo CSV file.

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Print debug chatter.

Demo program for processing scores in a league with players of varied levels. You can generate
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

Point system based on games won vs games lost without consideration for performance or player level.

    score.py input_csv --ignore-ranking-factors --ranking-factor-break-in-period=0 demo.csv
```
