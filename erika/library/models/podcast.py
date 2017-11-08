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
A model used to store podcasts in the library.
"""

import logging
import os.path
import requests
from peewee import BooleanField, TextField, DoesNotExist, IntegrityError, fn

from erika import parsers
from erika.library.fields import Image, ImageField
from erika.util import sanitize_filename
from .database import BaseModel, database, slugify
from .config import Config
from .episode import Episode
from .episode import Podcast as PodcastProxy
from .podcast_action import PodcastAction


class Podcast(BaseModel):
    """A model used to store podcasts in the library.

    Attributes
    ----------
    parser : str
        The name of the parser (see :mod:`erika.parsers`).
    url : str
        The url of the podcast.
    title : str, optional
        The title of the podcast.
    author : str, optional
        The author of the podcast.
    image_url : str, optional
        A link to the image of the podcast
    image : :class:`~erika.library.fields.Image`, optional
        The image of the podcast.
    language : str, optional
        The language of the podcast.
    subtitle : str, optional
        The subtitle of the podcast.
    summary : str, optional
        A description of the podcast.
    link : str, optional
        Website link.
    update_failed : bool
        True if the last update of the podcast failed.
    """
    parser = TextField()
    url = TextField()

    title = TextField(null=True)
    author = TextField(null=True)
    image_url = TextField(null=True)
    image = ImageField(null=True)
    language = TextField(null=True)
    subtitle = TextField(null=True)
    summary = TextField(null=True)
    link = TextField(null=True)

    update_failed = BooleanField(default=False)

    class Meta:  # pylint: disable=too-few-public-methods, missing-docstring
        indexes = (
            (('parser', 'url'), True),
        )

    @property
    def display_subtitle(self):
        """str: The subtitle of the podcast, or its summary if it has no
        subtitle."""
        return self.subtitle or self.summary or ""

    @property
    def display_summary(self):
        """str: The summary of the podcast, or its subtitle if it has no
        summary."""
        return self.summary or self.subtitle or ""

    @property
    def display_title(self):
        """str: The title of the podcast, or its url if it has no title."""
        return self.title or self.url or ""

    @property
    def episodes_count(self):
        """int: the number of episodes of the podcast."""
        return self.episodes.count()

    @property
    def played_count(self):
        """int: the number of episodes that have already been played."""
        # pylint: disable=singleton-comparison
        return self.episodes.where(Episode.played == True).count()

    @property
    def new_count(self):
        """int: the number of episodes that have been added since the previous
        launch."""
        # pylint: disable=singleton-comparison
        return self.episodes.where(Episode.new == True).count()

    @property
    def unplayed_count(self):
        """int: the number of episodes that have not been played."""
        return self.episodes_count - self.played_count

    @classmethod
    def new(cls, parser, url):
        """Create a new podcast, and add it to the database

        Parameters
        ----------
        parser_name : str
            The name of a parser (see :mod:`erika.parsers`).
        url : str
            The url of the podcast.
        """
        logger = logging.getLogger(".".join((__name__, cls.__name__)))
        logger.info("Adding the %s podcast %s.", parser, url)
        try:
            podcast = Podcast.get(parser=parser, url=url)
        except DoesNotExist:
            podcast = Podcast(parser=parser, url=url)
            podcast.save()

            if podcast.parser == 'rss':
                PodcastAction.new(podcast_url=podcast.url, action="add")
        else:
            logger.warning("The %s podcast %s is already in the database.",
                           parser, url)

        return podcast

    def delete_instance(self, *args, **kwargs):
        # pylint: disable=arguments-differ
        PodcastAction.new(podcast_url=self.url, action="remove")
        super().delete_instance(*args, **kwargs)

    def update_podcast(self):
        """Update the podcast."""
        logger = logging.getLogger(
            ".".join((__name__, self.__class__.__name__)))
        logger.info("Updating the podcast %s.", self.display_title)

        try:
            # Parse the podcast
            episodes = parsers.parse(self)

            # Download the podcast's image if its url changed
            dirty_fields = [field.name for field in self.dirty_fields]
            if 'image_url' in dirty_fields:
                self.download_image()

            # Get the track number that should be used for the next new episode
            next_track_number = self.get_next_track_number()

            # Save the podcast and the episodes in the database
            with database.transaction():
                self.update_failed = False
                self.save()

                for episode in episodes:
                    episode.track_number = next_track_number
                    try:
                        episode.save()
                    except IntegrityError:
                        # The episode is already in the database, don't
                        # increment the track number.
                        continue
                    next_track_number += 1
        except Exception:  # pylint: disable=broad-except
            logger.exception("Unable to update the podcast.")

            self.update_failed = True
            self.save()

    def download_image(self):
        """Download the podcast's image"""
        logger = logging.getLogger(
            ".".join((__name__, self.__class__.__name__)))
        logger.debug("Downloading image for the podcast %s.", self.title)
        try:
            response = requests.get(self.image_url)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            logger.exception("Unable to download the image.")
            return

        self.image = Image(response.content)

    def get_next_track_number(self):
        """Get the track number of the next episode."""
        previous = self.episodes.select(fn.Max(Episode.track_number)).get()
        previous_number = previous.track_number or 0
        return previous_number + 1

    def get_directory(self):
        """Return the directory containing a podcast's audio files.

        Returns
        -------
        str
            The path of the directory.
        """
        template = Config.get_value("library.podcast_directory_template")
        return os.path.join(
            Config.get_value("library.root"),
            sanitize_filename(template.format(podcast=self))
        )

    def get_episode_from_tags_strict(self, audiotags):
        """Get the podcast's episode matching a file strictly.

        Returns the episode having the same guid, or the same title
        and publication date if there is one (meaning it was probably
        tagged by erika).

        Parameters
        ----------
        audiotags : dict
            Dictionnary containing the audio file's metadata.

        Returns
        -------
        :class:`Episode`, optional
            The episode, or None if there was no match.
        """
        logger = logging.getLogger(
            ".".join((__name__, self.__class__.__name__)))

        guid = audiotags['guid']
        pubdate = audiotags['pubdate']
        title = audiotags['title']

        try:
            episode = self.episodes.where(
                Episode.local_path.is_null(),
                (Episode.guid == guid) |
                ((Episode.pubdate == pubdate) & (Episode.title == title))
            ).first()
        except DoesNotExist:
            logger.debug("No strict match.")
            return None

        return episode

    def get_episode_from_tags_loose(self, audiotags, filename):
        """Get the podcast's episode matching a file loosely.

        Returns the episode having a title similar to the title or
        filename of the audio file. If there is more than one such
        match, None is returned as there is no way to find which
        episode is the right one.

        Parameters
        ----------
        audiotags : dict
            Dictionnary containing the audio file's metadata.
        filename : str
            The name of the audio file (without extensions or directory).

        Returns
        -------
        :class:`Episode`, optional
            The episode, or None if there was no match.
        """
        logger = logging.getLogger(
            ".".join((__name__, self.__class__.__name__)))

        title = audiotags['title']

        # Try to find a single episode with the same title
        episodes = self.episodes.where(
            Episode.local_path.is_null(),
            Episode.title == title).first(2)
        if episodes is not None:
            if len(episodes) > 1:
                logger.warning("Too many episodes with title %s.", title)
                return None

            return episodes[0]

        # Try to find a single episode with a title or filename similar to the
        # title
        filename = slugify(filename)
        title = slugify(title or "")

        episodes = self.episodes.where(
            Episode.local_path.is_null(),
            fn.slugify(Episode.title) << [title, filename]).first(2)
        if episodes is not None:
            if len(episodes) > 1:
                logger.warning("Too many episodes with title similar to '%s' "
                               "or '%s'.", title, filename)
                return None

            return episodes[0]


PodcastProxy.initialize(Podcast)
