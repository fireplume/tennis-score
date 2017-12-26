from interfaces import *


class Player(PlayingEntity):
    """
    Initial ranking is only meaningful if break in period is 0, see options for details.
    """
    def __init__(self, name: str, play_level_scoring_factor: float, initial_points=0.0):
        super(Player, self).__init__(name,
                                     PlayingEntity.PlayType.SINGLES,
                                     play_level_scoring_factor,
                                     initial_points)
