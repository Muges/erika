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
Table containing the episodes
"""

import requests
from peewee import (BooleanField, DateTimeField, IntegerField, ForeignKeyField,
                    TextField, Proxy)

from podcasts.library.database import BaseModel
from podcasts.image import Image
from podcasts.util import format_duration

Podcast = Proxy()  # pylint: disable=invalid-name


class Episode(BaseModel):
    """
    Object representing an episode in the library

    Attributes
    ----------
    podcast : Podcast
        The podcast
    guid : Optional[str]
        A unique identifier for the episode
    pubdate : Optional[datetime]
        The date of publication of the episode
    title : Optional[str]
        The title of the episode
    duration : Optional[int]
        The duration of the episode in seconds
    image_url : Optional[str]
        A link to the image of the episode
    subtitle : Optional[str]
        The subtitle of the episode
    summary : Optional[str]
        A description of the episode
    link : Optional[str]
        Website link
    track_number : int
        The track_number of the episode. As long as the publication dates are
        consistent with the publication order this should be accurate.
    file_url : Optional[str]
        Url of the episode file
    file_size : Optional[int]
        Size of the episode file in bytes
    mimetype : Optional[str]
        Mimetype of the episode file
    local_path : Optional[str]
        Path of the downloaded file
    new : bool
        True if the episode is new
    played : bool
        True if the episode has been played
    progress : int
        Number of seconds of the episode that have been played (used to be able
        to resume the playback after quitting the application)
    """

    podcast = ForeignKeyField(Podcast, related_name='episodes',
                              on_delete='CASCADE')

    guid = TextField(null=True)
    pubdate = DateTimeField(null=True)
    title = TextField(null=True)
    duration = IntegerField(null=True)
    image_url = TextField(null=True)
    subtitle = TextField(null=True)
    summary = TextField(null=True)
    link = TextField(null=True)

    track_number = IntegerField()

    file_url = TextField(null=True)
    file_size = IntegerField(null=True)
    mimetype = TextField(null=True)
    local_path = TextField(null=True)

    new = BooleanField(default=True)
    played = BooleanField(default=False)
    progress = IntegerField(default=0)

    class Meta:  # pylint: disable=too-few-public-methods, missing-docstring
        indexes = (
            (('podcast', 'guid'), True),
            (('podcast', 'title', 'pubdate'), True),
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.image_data = None

    @property
    def display_duration(self):
        """The episode's duration as a formatted string"""
        if not self.duration:
            return ""

        return format_duration(self.duration)

    @property
    def image(self):
        """The episode's image as an Image object"""
        if self.image_data is None:
            return self.podcast.image

        return Image(self.image_data)

    def mark_as_played(self):
        """Mark the episode as played"""
        self.played = True
        self.new = False

    def mark_as_unplayed(self):
        """Mark the episode as unplayed"""
        self.played = False

    def get_image(self):
        """Get the episode's image

        This method downloads the episode's image if image_url is not None, and
        falls back to the podcast's image if it is None or in case of error.

        Returns
        -------
        bytes
            The image's data.
        """
        try:
            return self.image_data
        except AttributeError:
            pass

        if self.image_url:
            # Download image
            try:
                response = requests.get(self.image_url)
                response.raise_for_status()
            except requests.exceptions.RequestException:
                self.logger.exception("Unable to download image.")
            else:
                self.image_data = response.content
                return self.image_data

        # Fallback to the podcast's image
        return self.podcast.image_data
