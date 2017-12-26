from interfaces import *


class DoublesTeam(PlayingEntity):
    """
    Initial ranking is only meaningful if break in period is 0, see options for details.
    """
    def __init__(self, player1: PlayingEntity,
                 player2: PlayingEntity,
                 initial_points: float,
                 initial_level: float):
        name = DoublesTeam.get_doubles_team_name_from_player_names(player1.get_name(), player2.get_name())
        super(DoublesTeam, self).__init__(name,
                                          PlayingEntity.PlayType.DOUBLES,
                                          initial_level,
                                          initial_points)

        self._players = [player1, player2]
        self._level_override = dict()

    def is_in_team(self, player_name):
        if player_name.lower() == self._players[0].get_name() or \
           player_name.lower() == self._players[1].get_name():
            return True
        return False

    def update_play_level_scoring_factor(self, play_level_scoring_factor: float,
                                         index: LeagueIndex):
        super(DoublesTeam, self).update_play_level_scoring_factor(play_level_scoring_factor,
                                                                  index)

        # Usually, level is computed from the level of both singles players, but if it is set
        # explicitly, respect that.
        self._level_override[index] = play_level_scoring_factor

    def get_play_level_scoring_factor(self, index=LeagueIndex(-1)):
        """
        Override the play level scoring factor to be that of the product of
        the team's players'.
        """

        latest_override_index = LeagueIndex(-1)
        for override_index in self._level_override:
            if latest_override_index < override_index <= index:
                latest_override_index = override_index

        if latest_override_index != -1:
            return self._level_override[latest_override_index]
        elif self.get_initial_level_scoring_factor() != 0.0:
            return self.get_initial_level_scoring_factor()

        # We want the SINGLES playing factor
        try:
            factor1 = self._players[0].get_play_level_scoring_factor(index)
        except NoMatchPlayedYetError:
            factor1 = self._players[0].get_play_level_scoring_factor(PlayerIndex(0))

        try:
            factor2 = self._players[1].get_play_level_scoring_factor(index)
        except NoMatchPlayedYetError:
            factor2 = self._players[1].get_play_level_scoring_factor(PlayerIndex(0))

        return factor1 * factor2

    def get_player(self, index: int):
        if index != 1 and index != 2:
            raise Exception("You can only ask for player 1 or 2 in a doubles team. You requested: %d" % index)
        return self._players[index-1]

    @staticmethod
    def get_doubles_team_name_from_player_names(name1, name2):
        names = sorted([name1.lower(), name2.lower()])
        return PlayingEntity.DOUBLES_NAME_FORMAT.format(*names)
