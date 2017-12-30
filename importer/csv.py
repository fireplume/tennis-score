from Match import *
import League
from Player import *

logger = LoggerHandler.get_instance().get_logger("CSV")

REPLACEMENT_PLAYER_PREFIX_TOKENS = ['*', 'RPL']

# CSV FILE FORMAT REQUIREMENTS, run score.py --demo-csv for a sample.
PLAYER_ENTRY_FORMAT = "NEW_PLAYER,{name:s},{level_scoring_factor:.3f},{initial_points:.3f}"
SINGLES_GAME_ENTRY_FORMAT = "SINGLES_GAME,{player1:s},{games_won_1:d},{player2:s},{games_won_2:d}"
DOUBLES_GAME_ENTRY_FORMAT = "DOUBLES_GAME,{player1:s},{player2:s},{games_won_a:d},{player3:s},{player4:s}," + \
                            "{games_won_b:d}"
SINGLES_NEW_LEVEL_ENTRY_FORMAT = "NEW_PLAYER_LEVEL,{name:s},{league_match_index:d},{new_level:.3f}"
DOUBLES_TEAM_NEW_LEVEL_ENTRY_FORMAT = "NEW_TEAM_LEVEL,{name1:s},{name2:s},{league_match_index:d},{new_level:.3f}"
# TODO: Add support for interweaving match results with player level adjustments so as to not have to specify
# TODO: league match index. Don't forget to adjust regex in csv parsing.


def add_player(tennis_league: League, player: str, level=1.0, initial_points=0.0):
    player = Player(player, level, initial_points)
    try:
        tennis_league.add_playing_entity(player)
    except PlayingEntityAlreadyExistsError:
        pass
    return player


def add_doubles_team(tennis_league: League, name1: str, name2: str, level=1.0, initial_points=0.0):
    p1 = add_player(tennis_league, name1)
    p2 = add_player(tennis_league, name2)
    team = DoublesTeam(p1, p2, level, initial_points)
    try:
        tennis_league.add_playing_entity(team)
    except PlayingEntityAlreadyExistsError:
        pass
    return team


def cleanup_name(name):
    new_name = name.replace('*', '')
    return new_name


# TODO, use python's csv reader
def init_league(csv_file, tennis_league):
    """
    Required format for the CSV file:
    See top of file definitions.
    Player entries must be listed first, then singles or doubles matches.
    """

    new_player_re = re.compile(r"^NEW_PLAYER,(\S+?),(\d+|(?:\d+\.\d*)),(\d+|(?:\d+\.\d*))$")
    singles_entry_re = re.compile(r"^SINGLES_GAME,(\S+?),(\d+),(\S+?),(\d+)$")
    doubles_entry_re = re.compile(r"^DOUBLES_GAME,(\S+?),(\S+?),(\d+),(\S+?),(\S+?),(\d+)$")
    new_singles_level_re = re.compile(r"^NEW_PLAYER_LEVEL,(\S+?),(\d+),(\d+|(?:\d+\.\d*))$")
    new_team_level_re = re.compile(r"^NEW_TEAM_LEVEL,(\S+?),(\S+?),(\d+),(\d+|(?:\d+\.\d*))$")

    with open(csv_file, 'r') as fd:
        doubles_team_generated = False
        line_nb = 0
        for line in fd:
            line_nb += 1
            line = line.strip()
            line = re.sub(r'\s+', '', line)

            if line.startswith("#"):
                continue

            try:
                next_line = False
                for token in REPLACEMENT_PLAYER_PREFIX_TOKENS:
                    if token in line.lower():
                        logger.info("Entry '%s' skipped as a replacement played" % line)
                        next_line = True
                        break
                if next_line:
                    continue

                new_player = new_player_re.fullmatch(line)
                singles_match = singles_entry_re.fullmatch(line)
                doubles_match = doubles_entry_re.fullmatch(line)
                updated_singles_player_level = new_singles_level_re.fullmatch(line)
                updated_doubles_team_level = new_team_level_re.fullmatch(line)

                if new_player:
                    name = cleanup_name(new_player.group(1))
                    level_scoring_factor = (float(new_player.group(2)))
                    initial_points = float(new_player.group(3))
                    add_player(tennis_league, name, level_scoring_factor, initial_points)
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
                        team1 = add_doubles_team(tennis_league, player1, player2)
                        team2 = add_doubles_team(tennis_league, player3, player4)

                    tennis_league.add_match(Match(team1.get_name(), games_won_1, team2.get_name(), games_won_2))

                elif singles_match:
                    player1 = cleanup_name(singles_match.group(1))
                    games_won_1 = int(singles_match.group(2))
                    player2 = cleanup_name(singles_match.group(3))
                    games_won_2 = int(singles_match.group(4))

                    try:
                        tennis_league.add_match(Match(player1, games_won_1, player2, games_won_2))
                    except PlayingEntityDoesNotExistError:
                        add_player(tennis_league, player1)
                        add_player(tennis_league, player2)
                        tennis_league.add_match(Match(player1, games_won_1, player2, games_won_2))
                elif updated_doubles_team_level:
                    entity = tennis_league.get_playing_entity(cleanup_name(updated_doubles_team_level.group(1)))
                    entity2 = tennis_league.get_playing_entity(cleanup_name(updated_doubles_team_level.group(2)))
                    team = tennis_league.get_doubles_team(entity.get_name(), entity2.get_name())
                    team.update_play_level_scoring_factor(float(updated_doubles_team_level.group(4)),
                                                          LeagueIndex(int(updated_doubles_team_level.group(3))))
                elif updated_singles_player_level:
                    entity = tennis_league.get_playing_entity(cleanup_name(updated_singles_player_level.group(1)))
                    entity.update_play_level_scoring_factor(float(updated_singles_player_level.group(3)),
                                                            LeagueIndex(int(updated_singles_player_level.group(2))))
                elif line != "":
                    logger.debug("Following line (csv line number:%d) skipped: %s" % (line_nb, line))
            except Exception as e:
                error_msg = "\n\tERROR: Line %d in csv. %s.\n\t" % (line_nb, str(e)) + \
                            "ERROR: You may want to remove the line if you don't need it."
                raise Exception(error_msg)


def dump_sample(seed: int):
    import random
    import copy
    max_match_index = 50

    def generate_player(player):
        data = dict()
        data['name'] = player
        data['level_scoring_factor'] = random.uniform(0.7, 0.9)
        data['initial_points'] = random.random()*10 + 5.0
        return data

    def generate_singles_match(a_players_list: list):
        match = dict()
        players_list = copy.deepcopy(a_players_list)
        match['player1'] = players_list[random.randint(0, len(players_list)-1)]
        players_list.remove(match['player1'])
        match['player2'] = players_list[random.randint(0, len(players_list)-1)]
        match['games_won_1'] = random.randint(0, 8)
        match['games_won_2'] = random.randint(0, 8)
        return match

    def generate_doubles_match(a_players_list: list):
        match = dict()
        players_list = copy.deepcopy(a_players_list)
        match['player1'] = players_list[random.randint(0, len(players_list)-1)]
        players_list.remove(match['player1'])
        match['player2'] = players_list[random.randint(0, len(players_list)-1)]
        players_list.remove(match['player2'])
        match['player3'] = players_list[random.randint(0, len(players_list)-1)]
        players_list.remove(match['player3'])
        match['player4'] = players_list[random.randint(0, len(players_list)-1)]
        match['games_won_a'] = random.randint(0, 8)
        match['games_won_b'] = random.randint(0, 8)
        return match

    def generate_singles_level_change(a_players_list: list):
        new_level = dict()
        new_level['name'] = a_players_list[random.randint(0, len(a_players_list)-1)]
        new_level['league_match_index'] = random.randint(1, 5)
        new_level['new_level'] = random.uniform(0.4, 1.0)
        return new_level

    def generate_doubles_level_change(a_players_list: list):
        new_level = dict()
        players_list = copy.deepcopy(a_players_list)
        new_level['name1'] = players_list[random.randint(0, len(players_list)-1)]
        players_list.remove(new_level['name1'])
        new_level['name2'] = players_list[random.randint(0, len(players_list)-1)]
        new_level['league_match_index'] = random.randint(1, 3)
        new_level['new_level'] = random.uniform(0.4, 1.0)
        return new_level

    random.seed(seed)

    players = ["math", "andrew", "ben", "jessica", "anika", "carolina"]
    players_sub_list = ["math", "andrew", "jessica", "carolina"]

    # Players
    print("# New Player, Name, Level Scoring Factor, Initial Points")
    for p in sorted(players_sub_list):
        print(PLAYER_ENTRY_FORMAT.format(**generate_player(p)))

    # Singles Matches
    print("# Singles Matches, Player 1, Games Won, Player 2, Games Won")
    for i in range(0, max_match_index):
        print(SINGLES_GAME_ENTRY_FORMAT.format(**generate_singles_match(players)))

    # Doubles Matches
    print("# Doubles Matches, Player 1, Player 2, Games Won, Player 3, Player 4, Games Won")
    for i in range(0, max_match_index):
        print(DOUBLES_GAME_ENTRY_FORMAT.format(**generate_doubles_match(players)))

    # Singles Level Adjustment
    print("# New Player Level, Name, League Match Index To Take Effect, New Level(Scoring Factor)")
    for i in range(0, 4):
        print(SINGLES_NEW_LEVEL_ENTRY_FORMAT.format(**generate_singles_level_change(players)))

    # Doubles Team Level Adjustment
    print("# New Team Level, Name, League Match Index To Take Effect, New Level(Scoring Factor)")
    for i in range(0, 4):
        print(DOUBLES_TEAM_NEW_LEVEL_ENTRY_FORMAT.format(**generate_doubles_level_change(players)))

    # Generate some originally unlisted player doubles matches
    print(DOUBLES_GAME_ENTRY_FORMAT.format(player1="math", player2="julie", games_won_a=4, player3="anika",
                                           player4="rick", games_won_b=4))
    print(DOUBLES_GAME_ENTRY_FORMAT.format(player1="RPL1", player2="julie", games_won_a=4, player3="anika",
                                           player4="rick", games_won_b=4))
