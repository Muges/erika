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
Table containing the episode actions
"""

from datetime import datetime
from peewee import DateTimeField, IntegerField, ForeignKeyField, TextField

from mygpoclient.api import EpisodeAction as GpoEpisodeAction
from mygpoclient.util import datetime_to_iso8601

from .database import BaseModel
from .episode import Episode
from .config import Config


class EpisodeAction(BaseModel):
    """Object representing an episode action in the library

    Attributes
    ----------
    episode : Episode
        The episode
    action : str
        The type of the action (download, delete, play or new)
    time : Optional[datetime]
        The UTC time when the action took place as a datetime
    started : Optional[int]
        The position at which the playback started (only valid if action is
        'play')
    position : Optional[int]
        The position at which the playback was stopped (only valid if action is
        'play')
    total : Optional[int]
        The duration of the episode in seconds (only valid if action is 'play')
    """
    episode = ForeignKeyField(Episode, on_delete='CASCADE')
    action = TextField()
    time = DateTimeField(default=datetime.utcnow)

    started = IntegerField(null=True)
    position = IntegerField(null=True)
    total = IntegerField(null=True)

    def for_gpodder(self):
        """
        Returns
        -------
        mygpoclient.api.EpisodeAction
        """
        device = Config.get_value("gpodder.deviceid")

        if self.action == "play":
            return GpoEpisodeAction(self.podcast_url, self.episode_url,
                                    self.action, device, self.timestamp,
                                    self.started, self.position, self.total)
        else:
            return GpoEpisodeAction(self.podcast_url, self.episode_url,
                                    self.action, device, self.timestamp)

    @property
    def podcast_url(self):
        """The url of the episode's podcast"""
        return self.episode.podcast.url

    @property
    def episode_url(self):
        """The url of the episode"""
        return self.episode.file_url

    @property
    def timestamp(self):
        """The UTC time when the action took place as an ISO8601 timestamp"""
        return datetime_to_iso8601(self.time)
