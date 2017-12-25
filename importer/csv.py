from Game import *
from exceptions import PlayingEntityDoesNotExistError, PlayingEntityAlreadyExistsError
import League
from Player import *

REPLACEMENT_PLAYER_PREFIX = 'RPL'

# CSV FILE FORMAT REQUIREMENTS, run score.py --demo-csv for a sample.
PLAYER_ENTRY_FORMAT = "NEW_PLAYER,{name:s},{level_scoring_factor:f},{initial_ranking:d},{initial_points:f}"
SINGLES_GAME_ENTRY_FORMAT = "SINGLES_GAME,{player1:s},{games_won_1:d},{player2:s},{games_won_2:d}"
DOUBLES_GAME_ENTRY_FORMAT = "DOUBLES_GAME,{player1:s},{player2:s},{games_won_a:d},{player3:s},{player4:s}," + \
                            "{games_won_b:d}"
SINGLES_NEW_LEVEL_ENTRY_FORMAT = "NEW_PLAYER_LEVEL,{name:s},{league_match_index:d},{new_level:f}"
DOUBLES_TEAM_NEW_LEVEL_ENTRY_FORMAT = "NEW_TEAM_LEVEL,{name1:s},{name2:s},{league_match_index:d},{new_level:f}"
# TODO: Add support for interweaving game results with player level adjustments so as to not have to specify
# TODO: league match index. Don't forget to adjust regex in csv parsing.


def add_player(tennis_league: League, player: str, level=1.0, initial_ranking=1, initial_points=0.0):
    player = Player(player, level, initial_ranking, initial_points)
    try:
        tennis_league.add_playing_entity(player)
    except PlayingEntityAlreadyExistsError:
        pass
    return player


def cleanup_name(name):
    new_name = name.replace('*', '')
    return new_name


# TODO, use python's csv reader
def init_league(csv_file, tennis_league):
    """
    Required format for the CSV file:
    See top of file definitions.
    Player entries must be listed first, then singles or doubles games.
    """

    new_player_re = re.compile(r"^NEW_PLAYER,(\S+?),(\d+|(?:\d+\.\d*)),(\d+),(\d+|(?:\d+\.\d*))$")
    singles_entry_re = re.compile(r"^SINGLES_GAME,(\S+?),(\d+),(\S+?),(\d+)$")
    doubles_entry_re = re.compile(r"^DOUBLES_GAME,(\S+?),(\S+?),(\d+),(\S+?),(\S+?),(\d+)$")
    new_singles_level_re = re.compile(r"^NEW_SINGLES_LEVEL,(\S+?),(\d+),(\d+|(?:\d+\.\d*))$")
    new_team_level_re = re.compile(r"^NEW_TEAM_LEVEL,(\S+?),(\S+?),(\d+),(\d+|(?:\d+\.\d*))$")

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
                updated_doubles_team_level = new_team_level_re.fullmatch(line)

                if new_player:
                    name = cleanup_name(new_player.group(1))
                    level_scoring_factor = (float(new_player.group(2)))
                    initial_ranking = int(new_player.group(3))
                    initial_points = float(new_player.group(4))
                    add_player(tennis_league, name, level_scoring_factor,
                               initial_ranking, initial_points)
                elif doubles_match:
                    if not doubles_team_generated:
                        tennis_league.generate_doubles_team_combination()
                        doubles_team_generated = True
                    player1 = cleanup_name(doubles_match.group(1))
                    player2 = cleanup_name(doubles_match.group(2))
                    games_won_1 = int(doubles_match.group(3))
                    player3 = cleanup_name(doubles_match.group(4))
                    player4 = cleanup_name(doubles_match.group(5))
                    games_won_2 = int(doubles_match.group(6))
                    try:
                        team1 = tennis_league.get_doubles_team(player1, player2)
                        team2 = tennis_league.get_doubles_team(player3, player4)
                    except PlayingEntityDoesNotExistError:
                        add_player(tennis_league, player1)
                        add_player(tennis_league, player2)
                        add_player(tennis_league, player3)
                        add_player(tennis_league, player4)
                        team1 = tennis_league.get_doubles_team(player1, player2)
                        team2 = tennis_league.get_doubles_team(player3, player4)

                    tennis_league.add_game(Game(team1.get_name(), games_won_1, team2.get_name(), games_won_2))

                elif singles_match:
                    player1 = cleanup_name(singles_match.group(1))
                    games_won_1 = int(singles_match.group(2))
                    player2 = cleanup_name(singles_match.group(3))
                    games_won_2 = int(singles_match.group(4))

                    try:
                        tennis_league.add_game(Game(player1, games_won_1, player2, games_won_2))
                    except PlayingEntityDoesNotExistError:
                        add_player(tennis_league, player1)
                        add_player(tennis_league, player2)
                        tennis_league.add_game(Game(player1, games_won_1, player2, games_won_2))
                elif updated_doubles_team_level:
                    entity = tennis_league.get_playing_entity(cleanup_name(updated_doubles_team_level.group(1)))
                    entity2 = tennis_league.get_playing_entity(cleanup_name(updated_doubles_team_level.group(2)))
                    team = tennis_league.get_doubles_team(entity.get_name(), entity2.get_name())
                    team.update_play_level_scoring_factor(float(updated_doubles_team_level.group(4)),
                                                          PlayingEntity.PlayType.DOUBLES,
                                                          int(updated_doubles_team_level.group(3)))
                elif updated_singles_player_level:
                    entity = tennis_league.get_playing_entity(cleanup_name(updated_singles_player_level.group(1)))
                    entity.update_play_level_scoring_factor(float(updated_singles_player_level.group(3)),
                                                            PlayingEntity.PlayType.SINGLES,
                                                            int(updated_singles_player_level.group(2)))
                elif line != "":
                    logger.debug("Following line (csv line number:%d) skipped: %s" % (line_nb, line))
            except Exception as e:
                logger.error("ERROR: Line %d in csv. %s" % (line_nb, str(e)))
                raise Exception()


def dump_sample(seed: int):
    import random
    import copy
    MAX_MATCH_INDEX = 50

    def generate_player(player, rank_max):
        data = dict()
        data['name'] = player
        data['level_scoring_factor'] = random.uniform(0.7, 0.9)
        data['initial_ranking'] = random.randint(1, rank_max)
        data['initial_points'] = random.random()*10 + 5.0
        return data

    def generate_singles_game(players: list):
        game = dict()
        players_list = copy.deepcopy(players)
        game['player1'] = players_list[random.randint(0, len(players_list)-1)]
        players_list.remove(game['player1'])
        game['player2'] = players_list[random.randint(0, len(players_list)-1)]
        game['games_won_1'] = random.randint(0, 8)
        game['games_won_2'] = random.randint(0, 8)
        return game

    def generate_doubles_game(players: list):
        game = dict()
        players_list = copy.deepcopy(players)
        game['player1'] = players_list[random.randint(0, len(players_list)-1)]
        players_list.remove(game['player1'])
        game['player2'] = players_list[random.randint(0, len(players_list)-1)]
        players_list.remove(game['player2'])
        game['player3'] = players_list[random.randint(0, len(players_list)-1)]
        players_list.remove(game['player3'])
        game['player4'] = players_list[random.randint(0, len(players_list)-1)]
        game['games_won_a'] = random.randint(0, 8)
        game['games_won_b'] = random.randint(0, 8)
        return game

    def generate_singles_level_change(players):
        new_level = dict()
        new_level['name'] = players[random.randint(0, len(players)-1)]
        new_level['league_match_index'] = random.randint(1, 5)
        new_level['new_level'] = random.uniform(0.4, 1.0)
        return new_level

    def generate_doubles_level_change(players):
        new_level = dict()
        players_list = copy.deepcopy(players)
        new_level['name1'] = players_list[random.randint(0, len(players_list)-1)]
        players_list.remove(new_level['name1'])
        new_level['name2'] = players_list[random.randint(0, len(players_list)-1)]
        new_level['league_match_index'] = random.randint(1, 3)
        new_level['new_level'] = random.uniform(0.4, 1.0)
        return new_level

    random.seed(seed)

    players = ["math", "andrew", "ben", "jessica", "anika", "carolina"]

    # Players
    print("New Player, name, level scoring factor, initial ranking, initial points")
    for p in players:
        print(PLAYER_ENTRY_FORMAT.format(**generate_player(p, len(players))))
    # Singles Games
    print("Singles games, player 1, games won, player 2, games won")
    for i in range(0, MAX_MATCH_INDEX):
        print(SINGLES_GAME_ENTRY_FORMAT.format(**generate_singles_game(players)))

    # Doubles Games
    print("Doubles games, player 1, player 2, games won, player 3, player 4, games won")
    for i in range(0, MAX_MATCH_INDEX):
        print(DOUBLES_GAME_ENTRY_FORMAT.format(**generate_doubles_game(players)))

    # Singles Level Adjustment
    print("New player level, Name, league match index to take effect, new level(scoring factor)")
    for i in range(0,4):
        print(SINGLES_NEW_LEVEL_ENTRY_FORMAT.format(**generate_singles_level_change(players)))

    # Doubles Team Level Adjustment
    print("New team level, Name, league match index to take effect, new level(scoring factor)")
    for i in range(0,4):
        print(DOUBLES_TEAM_NEW_LEVEL_ENTRY_FORMAT.format(**generate_doubles_level_change(players)))
