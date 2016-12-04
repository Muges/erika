# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Muges
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Object representing an episode action in the library
"""

from datetime import datetime

from mygpoclient.api import EpisodeAction as GpoEpisodeAction
from mygpoclient.util import datetime_to_iso8601

from podcasts.library.row import Row


class EpisodeAction(Row):
    """
    Object representing an episode in the library

    Attributes
    ----------
    podcast_id : int
        The id of the podcast in the database
    episode_id : int
        The id of the episode in the database
    action : str
        The type of the action (download, delete, play or new)
    timestamp : str
        A UTC timestamp of when the action took place, in ISO 8601 format
    started : Optional[int]
        The position at which the playback started (only valid if action is
        'play')
    position : Optional[int]
        The position at which the playback was stopped (only valid if action is
        'play')
    total : Optional[int]
        The duration of the episode in seconds (only valid if action is 'play')
    podcast : str
        The url of the podcast feed
    episode : str
        The url of the episode file
    """

    TABLE = "episode_actions"
    PRIMARY_KEY = 'rowid'
    COLUMNS = [
        "podcast_id", "episode_id", "action", "timestamp", "started", "position",
        "total"
    ]
    ATTRS = [
        "podcast", "episode", "device"
    ]

    @staticmethod
    def new(episode, action, started=None, position=None, total=None):
        timestamp = datetime_to_iso8601(datetime.utcnow())

        return EpisodeAction(podcast_id=episode.podcast.id, episode_id=episode.id,
                             action=action, timestamp=timestamp, started=started,
                             position=position, total=total, podcast=episode.podcast,
                             episode=episode, device=None, rowid=None)
    
    def for_gpodder(self):
        """
        Returns
        -------
        mygpoclient.api.EpisodeAction
        """
        if self.action == "play":
            return GpoEpisodeAction(self.podcast, self.episode, self.action,
                                    self.device, self.timestamp, self.started,
                                    self.position, self.total)
        else:
            return GpoEpisodeAction(self.podcast, self.episode, self.action,
                                    self.device, self.timestamp)
