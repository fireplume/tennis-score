from utils.SmartIndex import *
from utils.utils import LoggerHandler

logger = LoggerHandler.get_instance().get_logger("Stats")


class StatsData(dict):
    PLAYER_INDEX_0 = PlayerIndex(0)
    PLAYER_INDEX_0.lock()

    def __init__(self, tag: str, data_type, extendable=False):
        super(StatsData, self).__init__()

        self._tag = tag
        if data_type != int and data_type != float:
            raise TypeError("StatsData only supports 'int' and 'float'")
        self._data_type = data_type

        # Extendability means that if the index for which the data is requested doesn't exist,
        # we are allowed to take the latest available one, otherwise, raise an exception.
        self._extendable = extendable

    @property
    def tag(self):
        return self._tag

    @property
    def data_type(self):
        return self._data_type

    def reset(self):
        # clear all data except if one exist at player index 0
        if StatsData.PLAYER_INDEX_0 in self:
            data = dict.__getitem__(self, StatsData.PLAYER_INDEX_0)
            self.clear()
            self[StatsData.PLAYER_INDEX_0] = data
        else:
            self.clear()

    def __getitem__(self, key: PlayerIndex):
        if not key.exists:
            if not self._extendable:  # and key.index_type == IndexType.PLAYER:
                raise SmartIndexError("Data is not set for %s at player index %d" % (self._tag, int(key)))

        try:
            return dict.__getitem__(self, key)
        except KeyError:
            # get latest index less than or equal to key
            latest = PlayerIndex(0)
            for index in sorted(self.keys()):
                if latest < index <= key:
                    latest = index

            return dict.__getitem__(self, latest)

    def __setitem__(self, key: PlayerIndex, value):
        if not key.exists:
            # get latest index less than or equal to key
            latest = PlayerIndex(0)
            for index in sorted(self.keys()):
                if latest < index <= key:
                    latest = index
            key = latest

        dict.__setitem__(self, key, value)

    def __str__(self):
        return "%s: extendable: %s" % (self._tag, self._extendable)


class Stats:
    """
    Stats are set based on the league match index, not to be confused with the player's
    match index.

    Stats are accessed using SmartIndex. SmartIndex cannot have a negative value, except
    for -1, nor a 0 value. '-1' means 'latest index'.

    There is a direct relationship between the number of match played
    and the corresponding PlayerIndex and LeagueIndex.
    """

    @Accepts.accepts(object, float, float, initial_points=float, initial_level=float)
    def __init__(self, initial_points, initial_level):
        self._stats_data = dict()

        # Default stats
        games_won = StatsData('games_won', int, extendable=False)
        games_lost = StatsData('games_lost', int, extendable=False)
        points = StatsData('match_points', float, extendable=False)
        rank = StatsData('ranking', int, extendable=True)
        level_scoring_factor = StatsData('level_scoring_factor', float, extendable=True)

        self._stats_data[games_won.tag] = games_won
        self._stats_data[games_lost.tag] = games_lost
        self._stats_data[points.tag] = points
        self._stats_data[rank.tag] = rank
        self._stats_data[level_scoring_factor.tag] = level_scoring_factor

        self._stats_data[games_won.tag][PlayerIndex(0)] = 0
        self._stats_data[games_lost.tag][PlayerIndex(0)] = 0
        self._stats_data[points.tag][PlayerIndex(0)] = initial_points
        self._stats_data[rank.tag][PlayerIndex(0)] = 0
        self._stats_data[level_scoring_factor.tag][PlayerIndex(0)] = initial_level

        self._player_match_index = PlayerIndex(1)

        self._index_cache = SmartIndexCache()

    def _get_index_cache(self):
        """
        Necessary for player_index_selector decorator
        """
        return self._index_cache

    def reset_data(self, tag: str):
        if tag != 'match_points' and tag != 'ranking':
            raise Exception("You can't reset data other than for 'match_points' and 'ranking'")
        self._stats_data[tag].reset()

    @Accepts.accepts(object, int, int, LeagueIndex, games_won=int, games_lost=int, league_match_index=LeagueIndex)
    def set_match_results(self,
                          games_won: int,
                          games_lost: int,
                          league_match_index: LeagueIndex):
        if self._index_cache.exists(league_match_index):
            raise OverwriteError("Trying to overwrite match results for %s" % str(league_match_index))

        if self._index_cache.number_of_indexes(IndexType.LEAGUE) != 0:
            latest_index = self._index_cache.max_index(IndexType.LEAGUE)
            if league_match_index < latest_index:
                raise BackToTheFutureError("Can't rewrite past, trying to set results for a game index"
                                           "lower than the latest.")

        p_index = self._player_match_index.get_locked_copy()
        l_index = league_match_index.get_locked_copy()

        self._stats_data['games_won'][p_index] = games_won
        self._stats_data['games_lost'][p_index] = games_lost

        self._index_cache.add_index(l_index, p_index)

        self._player_match_index += 1

    def index_exists(self, index: SmartIndex):
        return self._index_cache.exists(index)

    @Accepts.accepts(object, str, object, LeagueIndex, tag=str, data=object, league_index=LeagueIndex)
    def set_data(self, tag: str, data, league_index: LeagueIndex):
        # data has to be internally set with player index:
        player_index = self._index_cache.get_index_for_type(league_index, IndexType.PLAYER)

        if self._stats_data[tag].data_type != type(data):
            raise TypeError("%s stats data is expecting %s, you provided %s" %
                            (tag, self._stats_data[tag].data_type.__name__, type(data).__name__))

        if player_index in self._stats_data[tag]:
            raise OverwriteError("Data already exist for %s at player index %d (league index: %d)" %
                                 (tag, int(player_index), int(league_index)))

        self._stats_data[tag][player_index.get_locked_copy()] = data

    ##########################################################
    # Getter functions
    # Note: player_index_selector decorated function must be called
    # with keyword parameter 'index=value'
    ##########################################################
    @Accepts.accepts(object, SmartIndex, IndexType, index=SmartIndex, index_type=IndexType)
    def get_index_for_type(self, index: SmartIndex, index_type: IndexType):
        return self._index_cache.get_index_for_type(index, index_type)

    def get_initial_data(self, tag: str):
        return self._stats_data[tag][PlayerIndex(0)]

    @Accepts.accepts(object, dict, PlayerIndex, data=dict, last_player_index=PlayerIndex)
    def _get_sum(self,
                 data: StatsData,
                 last_player_index: PlayerIndex):
        if data.data_type == int:
            value = 0
        else:
            value = 0.0

        for index in sorted(data.keys()):
            if index > last_player_index:
                break
            else:
                value += data[index]

        return value

    @player_index_selector
    def get_number_of_match_played_by_league_index_time(self, **kwargs):
        """
        Return the number of match played as of the league index provided.
        """
        index = kwargs['index']

        if not index.exists:
            index = self._fix_non_exists(index)

        return int(index)

    @player_index_selector
    def get_data_for_index(self, tag: str, **kwargs):
        player_index = kwargs['index']
        return self._stats_data[tag][player_index]

    @Accepts.accepts(object, SmartIndex, index=SmartIndex)
    def _fix_non_exists(self, index: SmartIndex):
        latest_valid_league_index = self._index_cache.get_latest_valid_index(index)
        return self._index_cache.get_index_for_type(latest_valid_league_index, IndexType.PLAYER)

    @player_index_selector
    def get_cumulative_data_sum_for_index(self, tag: str, **kwargs):
        player_index = kwargs['index']

        # If index is invalid, try to get the latest valid one
        # Oh, and it's actually a LeagueIndex when it doesn't exist, so conver to PlayerIndex afterwards.
        if not player_index.exists:
            player_index = self._fix_non_exists(player_index)

        total = self._get_sum(self._stats_data[tag],
                              player_index)

        return total

    @player_index_selector
    def get_average_points_per_match(self, **kwargs):
        player_index = kwargs['index']

        # If index is invalid, try to get the latest valid one
        # Oh, and it's actually a LeagueIndex when it doesn't exist, so conver to PlayerIndex afterwards.
        if not player_index.exists:
            player_index = self._fix_non_exists(player_index)

        points = self.get_cumulative_data_sum_for_index('match_points', index=player_index)
        match_played = int(player_index)

        if match_played == 0:
            return 0

        return points/match_played
