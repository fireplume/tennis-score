from League import *
from interfaces import *
from utils.exceptions import PlayingEntityDoesNotExistError


class Game(BaseGame):
    """
    Game class to hold game results.
    """
    # LEAGUE must be set to a valid League object before being instantiated!
    LEAGUE = None

    def __init__(self, p1: str, p1_games_won: int, p2: str, p2_games_won: int):
        if Game.LEAGUE is None:
            if League.get_instance() is None:
                raise Exception("You must instantiate a league object before instantiating a Game object!")
            else:
                Game.LEAGUE = League.get_instance()

        self._players_list = set()
        self._play_type = PlayingEntity.PlayType.SINGLES
        self._p1 = p1.lower()
        self._p2 = p2.lower()
        self._p1_games_won = p1_games_won
        self._p2_games_won = p2_games_won

        self._data = dict()
        self._data['name'] = dict()
        self._data['games_won'] = dict()
        self._data['games_lost'] = dict()

        self._init_data()

    def _init_data(self):
        # Extract player's names from the entity's names in case it's a doubles match
        team_1_names = PlayingEntity.DOUBLES_NAME_RE.match(self._p1)
        team_2_names = PlayingEntity.DOUBLES_NAME_RE.match(self._p2)
        if team_1_names and not team_2_names or not team_2_names and team_1_names:
            raise Exception("Playing entity caters to different match type '%s' vs '%s'" % (self._p1, self._p2))

        # Add doubles players names to the player list
        if team_1_names:
            self._play_type = PlayingEntity.PlayType.DOUBLES
            self._players_list.add(team_1_names.group(1).lower())
            self._players_list.add(team_1_names.group(2).lower())
            self._players_list.add(team_2_names.group(1).lower())
            self._players_list.add(team_2_names.group(2).lower())

        # Add singles players' names or doubles' team names to the list too
        self._players_list.add(self._p1.lower())
        self._players_list.add(self._p2.lower())

        exception_string = []
        if not Game.LEAGUE.playing_entity_name_exists(self._p1):
            exception_string.append("Playing entity '%s' is not registered with the league!" % self._p1)
        if not Game.LEAGUE.playing_entity_name_exists(self._p2):
            exception_string.append("Playing entity '%s' is not registered with the league!" % self._p2)
        if exception_string:
            raise PlayingEntityDoesNotExistError("\n".join(exception_string))

        self._data['name'][1] = self._p1.lower()
        self._data['games_won'][self._p1.lower()] = self._p1_games_won
        self._data['games_lost'][self._p1.lower()] = self._p2_games_won
        self._data['name'][2] = self._p2.lower()
        self._data['games_won'][self._p2.lower()] = self._p2_games_won
        self._data['games_lost'][self._p2.lower()] = self._p1_games_won

        if self._play_type == PlayingEntity.PlayType.DOUBLES:
            # Allow doubles players to ask for their score by their individual name
            # instead of the team's name.
            self._data['games_won'][team_1_names.group(1).lower()] = self._p1_games_won
            self._data['games_won'][team_1_names.group(2).lower()] = self._p1_games_won
            self._data['games_lost'][team_1_names.group(1).lower()] = self._p2_games_won
            self._data['games_lost'][team_1_names.group(2).lower()] = self._p2_games_won

            self._data['games_won'][team_2_names.group(1).lower()] = self._p2_games_won
            self._data['games_won'][team_2_names.group(2).lower()] = self._p2_games_won
            self._data['games_lost'][team_2_names.group(1).lower()] = self._p1_games_won
            self._data['games_lost'][team_2_names.group(2).lower()] = self._p1_games_won

    def get_name(self, entity: int):
        if entity != 1 and entity != 2:
            raise Exception("Game.get_name: entity must be either 1 or 2, value given: %d" % entity)
        return self._data['name'][entity]

    def get_games_won(self, entity_name: str):
        if not self.has_played(entity_name):
            raise Exception("Game.get_games_won: player %s didn't play in this game" % entity_name)
        return self._data['games_won'][entity_name]

    def get_games_lost(self, entity_name: str):
        if not self.has_played(entity_name):
            raise Exception("Game.get_games_won: player %s didn't play in this game" % entity_name)
        return self._data['games_lost'][entity_name]

    def has_played(self, entity_name: str, entity_name2=""):
        if entity_name.lower() in self._players_list:
            if entity_name2 != "" and entity_name2.lower() not in self._players_list:
                return False
            else:
                return True
        return False

    def get_players_list(self):
        return self._players_list

    @property
    def play_type(self):
        return self._play_type

    def __str__(self):
        name1 = self._data['name'][1]
        name2 = self._data['name'][2]
        return "{:<12s} vs {:<12s}: {:d}-{:d}".format(self._data['name'][1], self._data['name'][2],
                                                      self._data['games_won'][name1], self._data['games_won'][name2])
