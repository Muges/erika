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
Podcast library
"""

import logging
import os.path
import sqlite3
import urllib.request

from .config import CONFIG_DIR
from . import sources

DATABASE_PATH = os.path.join(CONFIG_DIR, "library")


class Library(object):
    """
    Object handling the podcast library.

    The podcast library is stored in an sqlite database. The Library object
    provides methods to access this database easily. Multiple Library objects
    can be used concurrently.
    """

    @classmethod
    def init(cls):
        """
        Create or update the database

        This function should be called once at the beginning of the program. If
        the database file does not exists, it creates it. If the database is
        outdated (e.g. if it was created by an old version of the program, and
        the database format has changed), it should be updated.
        """
        logger = logging.getLogger(
            "{}.{}".format(__name__, cls.__name__))
        logger.debug("Database initialization.")

        if not os.path.isfile(DATABASE_PATH):
            library = Library()
            library.create()

    def __init__(self):
        self.logger = logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__))

        self.connection = sqlite3.connect(DATABASE_PATH,
                                          detect_types=sqlite3.PARSE_DECLTYPES)

    def create(self):
        """
        Create the database file
        """
        self.logger.info("Creating database file.")

        # Create tables
        self.connection.execute("""
            CREATE TABLE podcasts (
                id INTEGER PRIMARY KEY,

                source text,
                url text,

                title text,
                author text,

                image_url text,
                image_data blob,
                language text,
                subtitle text,
                summary text,
                link text
            )
        """)

        self.connection.execute("""
            CREATE TABLE episodes (
                podcast_id integer REFERENCES podcasts(id),
                id integer PRIMARY KEY,

                guid text,
                pubdate timestamp,
                title text,

                duration integer,
                image_url text,
                link text,
                subtitle text,
                summary text,

                mimetype text,
                file_size text,
                file_url text,

                new integer DEFAULT 1,
                progress integer DEFAULT 0,

                UNIQUE (podcast_id, guid),
                UNIQUE (podcast_id, title, pubdate)
            )
        """)

        self.connection.commit()

    def _add_podcast(self, source_name, url, podcast):
        """
        Add a new podcast to the library

        This methods does not commit the changes to the database.

        Parameters
        ----------
        source_name : str
            Name of the source class to be used (e.g. "feed")
        url : str
            URL of the podcast
        podcast : Podcast
            The namedtuple describing the podcast

        Returns
        -------
        int
            The id of the podcast
        """
        # Get the image file
        self.logger.debug("Downloading image for %s.", url)
        try:
            response = urllib.request.urlopen(podcast.image)
            image_data = response.read()
        except urllib.request.URLError:
            self.logger.exception("Unable to download image.")
            image_data = None

        cursor = self.connection.cursor()
        cursor.execute(
            """
                INSERT INTO podcasts
                (source, url, title, author, image_url,
                image_data, language, subtitle,
                summary, link)
                VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source_name, url, podcast.title, podcast.author, podcast.image,
                image_data, podcast.language, podcast.subtitle,
                podcast.summary, podcast.link
            )
        )

        return cursor.lastrowid

    def _add_episode(self, podcast_id, episode):
        """
        Add a new episode to the library

        This methods does not commit the changes to the database.

        Parameters
        ----------
        podcast_id : int
            The id of the podcast
        episode : Episode
            The namedtuple describing the episode
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
                INSERT INTO episodes
                (podcast_id, guid, pubdate, title,
                duration, image_url, link,
                subtitle, summary, mimetype,
                file_size, file_url)
                VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                podcast_id, episode.guid, episode.pubdate, episode.title,
                episode.duration, episode.image, episode.link,
                episode.subtitle, episode.summary, episode.mimetype,
                episode.file_size, episode.file_url
            )
        )

        return cursor.lastrowid

    def add_source(self, source_name, url):
        """
        Add a new podcast source and its episodes to the library.

        Parameters
        ----------
        source_name : str
            Name of the source class to be used (e.g. "feed")
        url : str
            URL of the podcast
        """
        source = sources.get(source_name, url)
        source.parse()

        podcast = source.get_podcast()
        podcast_id = self._add_podcast(source_name, url, podcast)

        for episode in source.get_episodes():
            self._add_episode(podcast_id, episode)

        self.connection.commit()
