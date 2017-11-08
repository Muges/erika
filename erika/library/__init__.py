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
The :mod:`erika.library` module implements the podcast library.
"""

import logging
import os

from .models import (database, Config, Episode, EpisodeAction, Podcast,
                     PodcastAction)


def initialize():
    """Create or update the database

    This function should be called once at the beginning of the
    program. If the database file does not exists, it creates it. If
    the database is outdated (e.g. if it was created by an old version
    of the program, and the database format has changed), it should be
    updated.
    """
    logger = logging.getLogger(__name__)
    logger.debug("Initializing the database")

    with database.transaction():
        database.create_tables(
            [Config, Podcast, Episode, EpisodeAction, PodcastAction],
            safe=True)

        # Set default configuration values
        Config.set_defaults()

        # Set all the episodes as non-new
        Episode.update(new=False)


def scan():
    """Scan the library directory to add the local episode files."""
    logger = logging.getLogger(__name__)
    logger.info("Scanning the library")

    with database.transaction():
        # Check that the files that are in the database still exist
        # and update the `paths` list so that it contains all the
        # files that are already the database
        paths = []
        episodes = Episode.select().where(Episode.local_path.is_null(False))
        for episode in episodes:
            if os.path.isfile(episode.local_path):
                paths.append(episode.local_path)
            else:
                episode.local_path = None
                episode.save()

        # Look for new local files
        library_root = Config.get_value("library.root")
        for dirpath, _, filenames in os.walk(library_root):
            for filename in filenames:
                path = os.path.join(dirpath, filename)
                if path in paths:
                    # The file is already in the library
                    continue

                if path.endswith(".part"):
                    # The file is incomplete
                    continue

                episode = Episode.get_matching(path)
                if not episode:
                    # No match was found
                    continue

                # Set the path of the episode in the database
                episode.local_path = path
                episode.save()

                # Add an action indicating that the episode has been
                # downloaded on this device
                action = EpisodeAction(episode=episode, action="download")
                action.save()
