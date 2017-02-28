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
Table containing the podcasts
"""

from peewee import BooleanField, BlobField, TextField

from podcasts.library.database import BaseModel
from podcasts.library.episode import DeferredPodcast
from podcasts.image import Image


class Podcast(BaseModel):
    """Object representing a podcast in the library

    Attributes
    ----------
    parser : str
        The name of the parser
    url : str
        The url of the podcast
    title : Optional[str]
        The title of the podcast
    author : Optional[str]
        The author of the podcast
    image_url : Optional[str]
        A link to the image of the podcast
    image_data : Optional[bytes]
        The content of the image file
    language : Optional[str]
        The language of the podcast
    subtitle : Optional[str]
        The subtitle of the podcast
    summary : Optional[str]
        A description of the podcast
    link : Optional[str]
        Website link
    new : bool
        True if the podcast has been synced with gpodder.net
    removed : bool
        True if the podcast has been removed

    new_count : int
        Number of new episodes
    played_count : int
        Number of played episodes
    episodes_count : int
        Number of episodes
    """
    parser = TextField()
    url = TextField()

    title = TextField(null=True)
    author = TextField(null=True)
    image_url = TextField(null=True)
    image_data = BlobField(null=True)
    language = TextField(null=True)
    subtitle = TextField(null=True)
    summary = TextField(null=True)
    link = TextField(null=True)

    new = BooleanField(default=True)
    removed = BooleanField(default=False)

    class Meta:  # pylint: disable=too-few-public-methods, missing-docstring
        indexes = (
            (('parser', 'url'), True),
        )

    @property
    def image(self):
        """Return the podcast's image as an Image object"""
        return Image(self.image_data)

    @property
    def display_subtitle(self):
        """Return the podcast's subtitle or its summary"""
        return self.subtitle or self.summary or ""

    @property
    def display_summary(self):
        """Return the podcast's summary or its subtitle"""
        return self.summary or self.subtitle or ""

    @property
    def display_title(self):
        """Return the podcast's title or its url"""
        return self.title or self.url or ""

    @property
    def unplayed_count(self):
        """Return the number of episodes that have not been played"""
        return self.episodes_count - self.played_count


DeferredPodcast.set_model(Podcast)
