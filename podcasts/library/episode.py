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
Object representing an episode in the library
"""

from podcasts.library.row import Row


class Episode(Row):
    """
    Object representing an episode in the library

    Attributes
    ----------
    podcastid : int
        The id of the podcast in the database
    id : int
        The id of the episode in the database
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
    link : Optional[str]
        Website link
    subtitle : Optional[str]
        The subtitle of the episode
    summary : Optional[str]
        A description of the episode
    mimetype : Optional[str]
        Mimetype of the episode file
    file_size : Optional[int]
        Size of the episode file in bytes
    file_url : Optional[str]
        Url of the episode file
    new : bool
        True if the episode is new
    played : bool
        True if the episode has been played
    progress : int
        Number of seconds of the episode that have been played (used to be able
        to resume the playback after quitting the application)
    """

    TABLE = "episodes"
    PRIMARY_KEY = 'id'
    COLUMNS = [
        "podcast_id", "guid", "pubdate", "title", "duration", "image_url",
        "link", "subtitle", "summary", "mimetype", "file_size", "file_url",
        "new", "played", "progress"
    ]
    ATTRS = []

    def mark_as_played(self):
        """
        Mark the episode as played
        """
        self.played = True
        self.new = False

    def mark_as_unplayed(self):
        """
        Mark the episode as unplayed
        """
        self.played = False
