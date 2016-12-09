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

from collections import namedtuple
from datetime import datetime
import logging
import os.path
import sqlite3
import requests

from mygpoclient.util import datetime_to_iso8601, iso8601_to_datetime

from podcasts.config import CONFIG_DIR, CONFIG_DEFAULTS, CONFIG_TYPES
from podcasts import sources, tags
from podcasts.library.episode import Episode
from podcasts.library.episode_action import EpisodeAction
from podcasts.library.podcast import Podcast
from podcasts.library.row import Row
from podcasts.util import slugify, sanitize_filename

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

        # Create the boolean type
        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter("boolean", lambda v: bool(int(v)))

        if not os.path.isfile(DATABASE_PATH):
            library = Library()
            library.create()
        else:
            library = Library()
            library.reset_new()

    def __init__(self):
        self.logger = logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__))

        self.connection = sqlite3.connect(DATABASE_PATH,
                                          detect_types=sqlite3.PARSE_DECLTYPES)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    def create(self):
        """
        Create the database file
        """
        self.logger.info("Creating database file.")

        # Create tables
        self.connection.execute("""
            CREATE TABLE config (
                key text PRIMARY KEY,
                value text
            )
        """)

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
                link text,

                synced INTEGER DEFAULT 0,

                UNIQUE (source, url)
            )
        """)

        self.connection.execute("""
            CREATE TABLE episodes (
                podcast_id integer REFERENCES podcasts(id) ON DELETE CASCADE,
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
                local_path text,

                track_number integer,

                new boolean DEFAULT 1,
                played boolean DEFAULT 0,
                progress integer DEFAULT 0,

                UNIQUE (podcast_id, guid),
                UNIQUE (podcast_id, title, pubdate)
            )
        """)

        self.connection.execute("""
            CREATE TABLE removed_podcasts (
                url text UNIQUE
            )
        """)

        self.connection.execute("""
            CREATE TABLE episode_actions (
                podcast_id integer REFERENCES podcasts(id) ON DELETE CASCADE,
                episode_id integer REFERENCES episodes(id) ON DELETE CASCADE,

                action text,
                timestamp text,

                started integer,
                position integer,
                total integer
            )
        """)

        self.connection.commit()

    def has_podcast(self, source_name, url):
        cursor = self.connection.cursor()

        cursor.execute(
            """
                SELECT id FROM podcasts
                WHERE source = ? AND URL = ?
            """, (
                source_name, url
            )
        )

        row = cursor.fetchone()
        return row is not None

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
            response = requests.get(podcast.image)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            self.logger.exception("Unable to download image.")
            image_data = None
        else:
            image_data = response.content

        cursor = self.connection.cursor()

        cursor.execute(
            """
                INSERT OR IGNORE INTO podcasts
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

        self.connection.commit()

        return cursor.lastrowid

    def _add_episode(self, podcast_id, episode, next_track_number):
        """
        Add an episode to the library (or update it if it already exists).

        This methods does not commit the changes to the database.

        Parameters
        ----------
        podcast_id : int
            The id of the podcast
        episode : Episode
            The namedtuple describing the episode
        next_track_number : int
            The track number of the next episode
        """
        cursor = self.connection.cursor()

        # Try to update the episode
        cursor.execute(
            """
                UPDATE episodes
                SET
                    guid=?, pubdate=?, title=?, duration=?,
                    image_url=?, link=?, subtitle=?, summary=?,
                    mimetype=?, file_size=?, file_url=?
                WHERE
                    podcast_id=? AND
                    ((pubdate=? AND title=?) OR
                    (guid IS NOT NULL AND guid=?))
            """, (
                # SET
                episode.guid, episode.pubdate, episode.title, episode.duration,
                episode.image, episode.link, episode.subtitle, episode.summary,
                episode.mimetype, episode.file_size, episode.file_url,
                # WHERE
                podcast_id,
                episode.pubdate, episode.title,
                episode.guid
            )
        )

        if cursor.rowcount == 0:
            # No row has been changed : the episode is new
            cursor.execute(
                """
                    INSERT INTO episodes
                    (podcast_id, guid, pubdate, title,
                    duration, image_url, link,
                    subtitle, summary, mimetype,
                    file_size, file_url, track_number)
                    VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    podcast_id, episode.guid, episode.pubdate, episode.title,
                    episode.duration, episode.image, episode.link,
                    episode.subtitle, episode.summary, episode.mimetype,
                    episode.file_size, episode.file_url, next_track_number
                )
            )
            next_track_number += 1

        return next_track_number

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
        if self.has_podcast(source_name, url):
            return

        source = sources.get(source_name, url)
        source.parse()

        podcast = source.get_podcast()
        podcast_id = self._add_podcast(source_name, url, podcast)
        next_track_number = 1

        for episode in source.get_episodes():
            next_track_number = self._add_episode(podcast_id, episode,
                                                  next_track_number)

        self.connection.commit()

    def _update_podcast(self, oldpodcast, newpodcast):
        """
        Update a podcast.

        Parameters
        ----------
        oldpodcast : podcasts.library.Podcasts
            The old version of the podcast.
        newpodcast : podcasts.sources.Podcast
            The new version of the podcast.
        """
        image_data = oldpodcast.image_data
        if oldpodcast.image_url != newpodcast.image:
            # Get the image file
            self.logger.debug("Downloading image for %s.", oldpodcast.url)
            try:
                response = requests.get(newpodcast.image)
                response.raise_for_status()
            except requests.exceptions.RequestException:
                self.logger.exception("Unable to download image.")
                image_data = None
            else:
                image_data = response.content

        cursor = self.connection.cursor()
        cursor.execute(
            """
                UPDATE podcasts
                SET
                    title=?, author=?, image_url=?,
                    image_data=?, language=?, subtitle=?,
                    summary=?, link=?
                WHERE
                    id=?
            """, (
                # SET
                newpodcast.title, newpodcast.author, newpodcast.image,
                image_data, newpodcast.language, newpodcast.subtitle,
                newpodcast.summary, newpodcast.link,
                # WHERE
                oldpodcast.id
            )
        )

    def update_podcasts(self):
        """
        Update the podcasts
        """
        self.logger.info("Updating podcasts.")

        for podcast in self.get_podcasts(fast=True):
            source = sources.get(podcast.source, podcast.url)
            source.parse()

            self._update_podcast(podcast, source.get_podcast())
            next_track_number = self.get_next_episode_track_number(podcast)

            for episode in source.get_episodes():
                next_track_number = self._add_episode(podcast.id, episode,
                                                      next_track_number)

            self.connection.commit()

    def get_podcasts(self, fast=False):
        """
        Return a list of podcasts.

        Parameters
        ----------
        fast : bool
            True not to compute the episodes counts of the podcasts.

        Yields
        ------
        Podcast
        """
        cursor = self.connection.cursor()
        if fast:
            cursor.execute("""
                SELECT
                    podcasts.*,
                    NULL AS new_count,
                    NULL AS played_count,
                    NULL AS episodes_count
                FROM podcasts
            """)
        else:
            cursor.execute("""
                SELECT
                    podcasts.*,
                    IFNULL(SUM(episodes.new), 0) AS new_count,
                    IFNULL(SUM(episodes.played), 0) AS played_count,
                    COUNT(*) AS episodes_count
                FROM podcasts
                LEFT OUTER JOIN episodes ON (episodes.podcast_id = podcasts.id)
                GROUP BY episodes.podcast_id
            """)

        return (Podcast(**row) for row in cursor.fetchall())

    def get_episodes(self, podcast, sort=None):
        """
        Return a list of podcasts.

        Parameters
        ----------
        podcast : podcasts.library.Podcast
            The podcasts whose episodes will be returned
        sort : Union[FilterSort, None]
            A FilterSort indicating which episodes should be returned first, or
            None not to sort the results.

        Yields
        ------
        Episode
        """
        if sort:
            order_query = sort.query()
        else:
            order_query = ""

        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT
                *
            FROM episodes
            WHERE
                podcast_id=?
        """ + order_query, (podcast.id,))

        return (Episode(**row, podcast=podcast) for row in cursor.fetchall())

    def get_counts(self):
        """
        Get the episodes counts

        Returns
        -------
        int, int, int
            The number of new episodes, the number of played episodes, and the
            total number of episodes
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT
                IFNULL(SUM(new), 0) AS new_count,
                IFNULL(SUM(played), 0) AS played_count,
                COUNT(*) AS episodes_count
            FROM episodes
        """)

        row = cursor.fetchone()
        return row["new_count"], row["played_count"], row["episodes_count"]

    def commit(self, rows):
        """
        Commit the changes made to Row objects to the database.

        Parameters
        ----------
        rows : List[Row]
            List of rows
        """
        cursor = self.connection.cursor()

        for row in rows:
            if row.get_primary_key() is not None:
                cursor.execute(row.UPDATE_QUERY, row.get_update_attrs())
            else:
                cursor.execute(row.INSERT_QUERY, row.get_insert_attrs())

        self.connection.commit()

    def remove(self, row):
        """
        Remove a Row from the database.

        Parameters
        ----------
        row : Row
        """
        cursor = self.connection.cursor()

        cursor.execute(row.DELETE_QUERY, row.get_delete_attrs())

        if isinstance(row, Podcast) and row.source == "rss":
            cursor.execute(
                """
                    INSERT INTO removed_podcasts (url)
                    VALUES (?)
                """, (row.url,))

        self.connection.commit()

    def update_counts(self, podcast):
        """
        Update the episodes counts of a podcast

        Parameters
        ----------
        podcast : Podcast
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT
                IFNULL(SUM(new), 0) AS new_count,
                IFNULL(SUM(played), 0) AS played_count,
                COUNT(*) AS episodes_count
            FROM episodes
            WHERE podcast_id = ?
        """, (podcast.id,))

        result = cursor.fetchone()
        podcast.new_count = result["new_count"]
        podcast.played_count = result["played_count"]
        podcast.episodes_count = result["episodes_count"]

    def reset_new(self):
        """
        Mark all podcasts as non-new.
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE episodes
            SET new=0
        """)

        self.connection.commit()

    def get_next_episode_track_number(self, podcast):
        """
        Return the track_number of a podcast's next episode.

        Parameters
        ----------
        podcast : Podcast
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT
                IFNULL(MAX(track_number), 0) AS previous_track_number
            FROM episodes
            WHERE podcast_id = ?
        """, (podcast.id,))

        result = cursor.fetchone()
        return result["previous_track_number"] + 1

    def get_podcast_with_title(self, title):
        """
        Get the podcast from its title.

        Parameters
        ----------
        title : str
            The podcast's title.

        Returns
        -------
        Union[Podcast, None]
            None if there is no podcast with this title.
        """
        cursor = self.connection.cursor()

        cursor.execute(
            """
                SELECT
                    *,
                    NULL AS new_count,
                    NULL AS played_count,
                    NULL AS episodes_count
                FROM podcasts
                WHERE title = ?
            """, (title,)
        )
        row = cursor.fetchone()

        if row:
            return Podcast(**row)
        else:
            return None

    def get_matching_episode(self, path):
        """
        Get the episode matching a file.

        Parameters
        ----------
        path : str
            The path of the file.

        Returns
        -------
        Union[Episode, None], bool
            The episode, or None if there was no match;
            and True if it is a strict match (i.e. if the tags of the file are
            correct)
        """
        # Get the file's audio tags
        audiotags = tags.get_tags(path)
        if not audiotags:
            return None, False

        # Get podcast
        podcast = self.get_podcast_with_title(audiotags["podcast"])
        if not podcast:
            self.logger.warning(
                "The file '{}' belongs to an unknown podcast '{}'.".format(
                    path, audiotags["podcast"]))
            return None, False

        # Get the podcast's episodes with no local file
        episodes = [
            episode for episode in self.get_episodes(podcast)
            if episode.local_path is None
        ]

        # Try to get the episode with the same GUID
        filtered_episodes = [
            episode for episode in episodes
            if episode.guid == audiotags["guid"]
        ]
        if filtered_episodes:
            return filtered_episodes[0], True

        # Try to get the episode with the same publication date and title
        filtered_episodes = [
            episode for episode in episodes
            if episode.pubdate == audiotags["pubdate"] and
            episode.title == audiotags["title"]
        ]
        if filtered_episodes:
            if len(filtered_episodes) > 1:
                self.logger.warning(
                    "Too many episodes with matching date and title for file "
                    "'{}'.".format(path))
                return None, False
            else:
                return filtered_episodes[0], True

        # Try to get the episode with the same title
        filtered_episodes = [
            episode for episode in episodes
            if episode.title == audiotags["title"]
        ]
        if filtered_episodes:
            if len(filtered_episodes) > 1:
                self.logger.warning(
                    "Too many episodes with matching title for file "
                    "'{}'.".format(path))
                return None, False
            else:
                return filtered_episodes[0], False

        # Try to get the episode with a filename similar to the title
        filename = slugify(os.path.splitext(os.path.basename(path))[0])
        title = slugify(audiotags["title"] or "")

        filtered_episodes = [
            episode for episode in episodes
            if slugify(episode.title) in [title, filename]
        ]
        if filtered_episodes:
            if len(filtered_episodes) > 1:
                self.logger.warning(
                    "Too many episodes with matching filename for file "
                    "'{}'.".format(path))
                return None, False
            else:
                return filtered_episodes[0], False

        # No match was found
        self.logger.warning(
            "The file '{}' is an unknown episode.".format(path))
        return None, False

    def get_episodes_with_local_file(self):
        """
        Get the episodes that have a local file.

        Yields
        ------
        int, str
            The episode's id and the path of the file.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
                SELECT id, local_path
                FROM episodes
                WHERE local_path IS NOT NULL
            """
        )

        return ((row["id"], row["local_path"]) for row in cursor.fetchall())

    def remove_local_file(self, episode_id):
        """
        Remove the local_path column of an episode if the file does not exist.

        Parameters
        ----------
        episode_id : int
            The id of the episode.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
                UPDATE episodes
                SET
                    local_path = NULL
                WHERE
                    id = ?
            """, (episode_id,)
        )

    def scan(self):
        """
        Scan the library directory to add the local episode files.
        """
        paths = []
        # Check that the files that are in the database still exist
        for episode_id, path in self.get_episodes_with_local_file():
            if os.path.isfile(path):
                paths.append(path)
            else:
                self.remove_local_file(episode_id)
        self.connection.commit()

        # Look for new local files
        library_root = self.get_config("library.root")
        modifications = []
        for dirpath, dirnames, filenames in os.walk(library_root):
            for filename in filenames:
                path = os.path.join(dirpath, filename)
                if path in paths:
                    # The file is already in the library
                    continue

                if path.endswith(".part"):
                    # The file is incomplete
                    continue

                episode, strict = self.get_matching_episode(path)
                if not episode:
                    # No match was found
                    continue

                if not strict:
                    path = self.import_episode_file(episode, path)

                episode.local_path = path
                modifications.append(episode)
                modifications.append(EpisodeAction.new(episode, "download"))
        self.commit(modifications)

    def get_config(self, key, default=""):
        """
        Get a value from the config table.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
                SELECT value
                FROM config
                WHERE key = ?
            """, (key,)
        )

        row = cursor.fetchone()
        if row:
            return CONFIG_TYPES[key].read(row["value"])

        return CONFIG_DEFAULTS[key]

    def get_all_config(self):
        cursor = self.connection.cursor()
        cursor.execute(
            """
                SELECT key, value
                FROM config
            """
        )

        config = CONFIG_DEFAULTS.copy()

        rows = cursor.fetchall()
        for row in rows:
            config[row['key']] = CONFIG_TYPES[row['key']].read(row['value'])

        del config['gpodder.password']

        return config

    def set_config(self, key, value, commit=False):
        """
        Set a value in the config table.
        """
        cursor = self.connection.cursor()

        value = CONFIG_TYPES[key].write(value)

        # Try to update the value
        cursor.execute(
            """
                UPDATE config
                SET value = ?
                WHERE key = ?
            """, (value, key)
        )

        if cursor.rowcount == 0:
            # No row has been changed : the value is new
            cursor.execute(
                """
                    INSERT INTO config
                    (key, value)
                    VALUES
                    (?, ?)
                """, (
                    key, value
                )
            )

        self.connection.commit()

    def save_config(self, config):
        for key, value in config.items():
            self.set_config(key, value, commit=False)

        self.connection.commit()

    def get_added_podcasts(self):
        """
        Return a list of podcast url that were added since the last
        synchronization.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
                SELECT
                    url
                FROM podcasts
                WHERE
                    source = 'rss' AND
                    synced = 0
            """)
        return [row["url"] for row in cursor.fetchall()]

    def get_removed_podcasts(self):
        """
        Return a list of podcast url that were removed since the last
        synchronization.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
                SELECT
                    url
                FROM removed_podcasts
            """)
        return [row["url"] for row in cursor.fetchall()]

    def update_urls(self, update_urls):
        """
        Update the podcasts urls after the synchronization.
        """
        cursor = self.connection.cursor()

        for old_url, new_url in update_urls:
            if new_url:
                self.logger.debug("Updating url '%s' to '%s'.", old_url, new_url)
                cursor.execute(
                    """
                        UPDATE podcasts
                        SET url = ?
                        WHERE url = ?
                    """,
                    (new_url, old_url))

        self.connection.commit()

    def reset_podcast_synchronization(self):
        cursor = self.connection.cursor()

        cursor.execute(
            """
               UPDATE podcasts
               SET synced = 1
            """)
        cursor.execute(
            """
               DELETE FROM removed_podcasts
            """)

    def remove_podcast_with_url(self, url):
        """
        Remove a podcast from its url.

        Parameters
        ----------
        url : str
            The podcast's url.
        """
        cursor = self.connection.cursor()

        cursor.execute(
            """
                DELETE FROM podcasts
                WHERE url = ?
            """, (url,)
        )

        self.connection.commit()

    def get_episode_actions(self):
        cursor = self.connection.cursor()
        cursor.execute(
            """
                SELECT
                    podcasts.url AS podcast,
                    episodes.file_url AS episode,
                    config.value AS device,
                    episode_actions.rowid, episode_actions.*
                FROM episode_actions
                JOIN episodes ON episode_actions.episode_id = episodes.id
                JOIN podcasts ON episode_actions.podcast_id = podcasts.id
		JOIN config ON config.key = 'gpodder.deviceid'
            """)
        return [EpisodeAction(**row) for row in cursor.fetchall()]

    def handle_episode_actions(self, actions):
        actions.sort(key=lambda a: iso8601_to_datetime(a.timestamp))
        cursor = self.connection.cursor()

        smart_mark_seconds = self.get_config("player.smart_mark_seconds")

        for action in actions:
            if action.action == "play":
                if action.position + smart_mark_seconds >= action.total:
                    cursor.execute(
                        """
                            UPDATE episodes
                            SET
                                played = 1,
                                progress = 0
                            WHERE
                                file_url = ?
                        """, (action.episode,))
                else:
                    cursor.execute(
                        """
                            UPDATE episodes
                            SET
                                progress = ?
                            WHERE
                                file_url = ?
                        """, (action.position, action.episode))
            elif action.action == "new":
                cursor.execute(
                    """
                        UPDATE episodes
                        SET
                            played = 0
                        WHERE
                            file_url = ?
                    """, (action.episode,))

        self.connection.commit()

    def remove_episode_actions(self):
        cursor = self.connection.cursor()

        cursor.execute("""
            DELETE FROM episode_actions
        """)

        self.connection.commit()

    def import_episode_file(self, episode, path):
        # Rename and retag the episode
        ext = os.path.splitext(path)[1]
        newpath = self.get_episode_filename(episode, ext)
        os.rename(path, newpath)
        tags.set_tags(newpath, episode)
        return newpath

    def get_podcast_directory(self, podcast):
        """
        Return the path of the directory containing a podcast.

        Parameters
        ----------
            podcast : Podcast

        Returns
        -------
        str
            The path of the directory.
        """
        template = self.get_config("library.podcast_directory_template")
        return os.path.join(
            self.get_config("library.root"),
            sanitize_filename(template.format(podcast=podcast))
        )

    def get_episode_filename(self, episode, extension):
        """
        Return the filename of an episode.

        Parameters
        ----------
        episode : Episode
        extension : str

        Returns
        -------
        str
            The path of the episode.
        """
        dirname = self.get_podcast_directory(episode.podcast)
        template = self.get_config("library.episode_file_template")
        filename = os.path.join(
            dirname,
            sanitize_filename(template.format(episode=episode))
        )

        return filename + extension
