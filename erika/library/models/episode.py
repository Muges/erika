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
A model used to store episodes in the library.
"""

import logging
import os.path
import requests
from peewee import (BooleanField, DateTimeField, IntegerField, ForeignKeyField,
                    TextField, Proxy, DoesNotExist)
from playhouse.hybrid import hybrid_property

from erika import tags
from erika.library.fields import Image
from erika.util import format_duration, sanitize_filename
from .database import BaseModel
from .config import Config

Podcast = Proxy()  # pylint: disable=invalid-name


class Episode(BaseModel):
    """
    A model used to store episodes in the library.

    Attributes
    ----------
    podcast : Podcast
        The podcast the episode belongs to.
    guid : str, optional
        A unique identifier for the episode.
    pubdate : datetime, optional
        The date of publication of the episode.
    title : str, optional
        The title of the episode.
    duration : int, optional
        The duration of the episode in seconds.
    image_url : str, optional
        A link to the image of the episode.
    subtitle : str, optional
        The subtitle of the episode in plaintext.
    summary : str, optional
        A description of the episode in html.
    link : str, optional
        Website link.
    track_number : int
        The track number of the episode. As long as the publication dates are
        consistent with the publication order this should be accurate.
    file_url : str, optional
        Url of the episode file.
    file_size : int, optional
        Size of the episode file in bytes.
    mimetype : str, optional
        Mimetype of the episode file.
    local_path : str, optional
        Path of the downloaded file.
    new : bool
        True if the episode is new.
    played : bool
        True if the episode has been played.
    progress : int
        Number of seconds of the episode that have been played (used to be able
        to resume the playback after quitting the application).
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

    file_url = TextField(null=True, index=True)
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

        self._image = None
        self._tried_image_tags = False

    @property
    def display_duration(self):
        """str: the episode's duration as a formatted string."""
        if not self.duration:
            return ""

        return format_duration(self.duration)

    @property
    def image(self):
        """:class:`~erika.library.fields.Image`: the episode's image."""
        if self._image:
            return self._image

        # Try to get the image from the audio file
        if self.local_path and not self._tried_image_tags:
            self._tried_image_tags = True

            audio_tags = tags.get_tags(self.local_path)
            if audio_tags["image"]:
                self._image = Image(audio_tags["image"])
                return self._image

        return self.podcast.image

    @property
    def image_downloaded(self):
        """bool: true if the episode's image has been downloaded."""
        return self._image

    @hybrid_property
    def downloaded(self):
        """bool: true if the episode has been downloaded."""
        return self.local_path is not None

    @downloaded.expression
    def downloaded(self):
        """bool: true if the episode has been downloaded."""
        return self.local_path.is_null(False)

    @classmethod
    def get_matching(cls, path):
        """Get the episode matching a file and move the file to the right
        location.

        Parameters
        ----------
        path : str
            The path of the file.

        Returns
        -------
        :class:`Episode`, optional
            The episode, or None if there was no match.
        """
        logger = logging.getLogger(".".join((__name__, cls.__name__)))
        logger.debug("Searching for an episode matching the file '%s'", path)

        # Read the file's audio metadata
        audiotags = tags.get_tags(path)
        if not audiotags:
            return None

        podcast_title = audiotags['podcast']

        # Try to find the podcast
        try:
            podcast = Podcast.get(Podcast.title == podcast_title)
        except DoesNotExist:
            logger.warning("No podcast with title %s.", podcast_title)
            return None

        # Find the episode matching the metadata stricty
        episode = podcast.get_episode_from_tags_strict(audiotags)
        if episode:
            return episode

        # Try to find an episode matching the metadata loosely
        filename = os.path.splitext(os.path.basename(path))[0]
        episode = podcast.get_episode_from_tags_loose(audiotags, filename)
        if episode:
            episode.import_file(path)
            return episode

        logger.warning("No match found.")

    @staticmethod
    def get_counts():
        """Return a tuple containing some statistics about all the episodes.

        Returns
        -------
        int
            The number of new episodes.
        int
            The number of played episodes.
        int
            The total number of episodes.
        """
        # pylint: disable=singleton-comparison
        new = Episode.select().where(Episode.new == True).count()
        played = Episode.select().where(Episode.played == True).count()
        total = Episode.select().count()
        return new, played, total

    def import_file(self, path):
        """Import the episode's audio file in the library.

        Moves the file and sets its tag."""
        extension = os.path.splitext(path)[1]
        new_path = self.get_default_filename(extension)

        os.rename(path, new_path)
        tags.set_tags(new_path, self)

        return new_path

    def get_default_filename(self, extension):
        """Return the default filename for the audio file of an episode given
        its extension.

        Parameters
        ----------
        extension : str

        Returns
        -------
        str
            The default filename for the episode.
        """
        dirname = self.podcast.get_directory()
        template = Config.get_value("library.episode_file_template")
        filename = os.path.join(
            dirname,
            sanitize_filename(template.format(episode=self))
        )
        return filename + extension

    def mark_as_played(self):
        """Mark the episode as played."""
        self.played = True
        self.new = False

    def mark_as_unplayed(self):
        """Mark the episode as unplayed."""
        self.played = False

    def get_image(self):
        """Get the episode's image.

        This method downloads the episode's image if ``image_url`` is not None
        (and it has not been dowloaded yet), and falls back to the podcast's
        image if it is None or if an error occured.

        Returns
        -------
        :class:`~erika.library.fields.Image`
            The image.
        """
        # Return the episode's image if it has already been downloaded
        if self._image:
            return self._image

        if self.image_url:
            # Download image
            try:
                response = requests.get(self.image_url)
                response.raise_for_status()
            except requests.exceptions.RequestException:
                self.logger.exception("Unable to download image.")
            else:
                self._image = Image(response.content)
                return self._image

        # Fallback to the podcast's image
        return self.podcast.image
