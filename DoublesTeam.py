from interfaces import *


class DoublesTeam(PlayingEntity):
    """
    Initial ranking is only meaningful if break in period is 0, see options for details.
    """
    def __init__(self, player1: PlayingEntity, player2: PlayingEntity,
                 play_level_scoring_factor: float,
                 initial_ranking: int,
                 initial_points: float):
        super(DoublesTeam, self).__init__(player1.get_name(),
                                          PlayingEntity.PlayType.DOUBLES,
                                          play_level_scoring_factor,
                                          0, 0,
                                          player2.get_name(),
                                          initial_ranking,
                                          initial_points)

        self._players = [player1, player2]
        self._level_override = dict()

    def is_in_team(self, player_name):
        if player_name.lower() == self._players[0].get_name() or \
                        player_name.lower() == self._players[1].get_name():
            return True
        return False

    def update_play_level_scoring_factor(self, play_level_scoring_factor: float,
                                         play_type: PlayingEntity.PlayType,
                                         match_index: int):
        if play_type != PlayingEntity.PlayType.DOUBLES:
            raise Exception("Trying to set play level for singles player on team object!")

        super(DoublesTeam, self).update_play_level_scoring_factor(play_level_scoring_factor,
                                                                  play_type,
                                                                  match_index)

        # Usually, level is computed from the level of both singles players, but if it is set
        # explicitly, respect that.
        self._level_override[match_index] = play_level_scoring_factor

    def get_play_level_scoring_factor(self, play_type: PlayingEntity.PlayType, match_index=-1):
        """
        Override the play level scoring factor to be that of the product of
        the team's players'.
        """

        if play_type != PlayingEntity.PlayType.DOUBLES:
            raise Exception("Asking for singles play level score factor for a doubles team!")

        latest_override_index = -1
        for index in self._level_override:
            if match_index <= index and index > latest_override_index:
                latest_override_index = index

        if latest_override_index != -1:
            return self._level_override[latest_override_index]

        # We want the SINGLES playing factor
        factor1 = self._players[0].get_play_level_scoring_factor(PlayingEntity.PlayType.SINGLES, match_index)
        factor2 = self._players[1].get_play_level_scoring_factor(PlayingEntity.PlayType.SINGLES, match_index)

        return factor1 * factor2

    def get_player(self, index: int):
        if index != 1 and index != 2:
            raise Exception("You can only ask for player 1 or 2 in a doubles team. You requested: %d" % index)
        return self._players[index-1]
