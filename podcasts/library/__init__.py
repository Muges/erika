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

from podcasts.library.database import database
from podcasts.library.config import Config
from podcasts.library.episode import Episode
from podcasts.library.episode_action import EpisodeAction
from podcasts.library.podcast import Podcast
from podcasts.library.removed_podcast import RemovedPodcast


def initialize():
    """Create or update the database

    This function should be called once at the beginning of the
    program. If the database file does not exists, it creates it. If
    the database is outdated (e.g. if it was created by an old version
    of the program, and the database format has changed), it should be
    updated.
    """
    logger = logging.getLogger(__name__)
    logger.debug("Database initialization.")

    with database.transaction():
        database.create_tables([Config, Podcast, Episode, EpisodeAction,
                                RemovedPodcast],
                               safe=True)

        Config.set_defaults()
