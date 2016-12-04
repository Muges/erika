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

import requests

from podcasts.library.row import Row


class Episode(Row):
    """
    Object representing an episode in the library

    Attributes
    ----------
    podcast_id : int
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
    local_path : Optional[str]
        Path of the downloaded file
    new : bool
        True if the episode is new
    played : bool
        True if the episode has been played
    progress : int
        Number of seconds of the episode that have been played (used to be able
        to resume the playback after quitting the application)
    track_number : int
        The track_number of the episode. As long as the publication dates are
        consistent with the publication order this should be accurate.
    podcast : Podcast
        The podcast
    """

    TABLE = "episodes"
    PRIMARY_KEY = 'id'
    COLUMNS = [
        "podcast_id", "guid", "pubdate", "title", "duration", "image_url",
        "link", "subtitle", "summary", "mimetype", "file_size", "file_url",
        "local_path", "new", "played", "progress", "track_number"
    ]
    ATTRS = [
        "podcast"
    ]

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

    def get_image(self):
        """
        Get the episode's image.

        This method downloads the episode's image if image_url is not None, and
        falls back to the podcast's image if it is None or in case of error.

        Returns
        -------
        bytes
            The image's data.
        """
        if self.image_url:
            # Download image
            try:
                response = requests.get(self.image_url)
                response.raise_for_status()
            except requests.exceptions.RequestException:
                self.logger.exception("Unable to download image.")
            else:
                return response.content

        # Fallback to podcast image
        return self.podcast.image_data
