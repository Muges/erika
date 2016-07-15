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
Module defining the base classes used by podcast sources
"""

# TODO : Error handling

from collections import namedtuple

"""
Namedtuple describing an episode

Attributes
----------
guid : Optional[str]
    A unique identifier for the episode
pubdate : Optional[datetime]
    The date of publication of the episode
title : Optional[str]
    The title of the episode
duration : Optional[int]
    The duration of the episode in seconds
image : Optional[str]
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
"""
Episode = namedtuple('Episode', [
    "guid",
    "pubdate",
    "title",

    "duration",
    "image",
    "link",
    "subtitle",
    "summary",

    "mimetype",
    "file_size",
    "file_url"
])


"""
Namedtuple describing a podcast

Attributes
----------
title : Optional[str]
    The title of the podcast
author : Optional[str]
    The author of the podcast
image : Optional[str]
    A link to the image of the podcast
language : Optional[str]
    The language of the podcast
subtitle : Optional[str]
    The subtitle of the podcast
summary : Optional[str]
    A description of the podcast
link : Optional[str]
    Website link
"""
Podcast = namedtuple('Podcast', [
    "title",
    "author",

    "image",
    "language",
    "subtitle",
    "summary",
    "link"
])


class Source(object):
    """
    Base class for podcast sources.

    A podcast source could be an RSS feed, a youtube channel...

    Class Attributes
    ----------------
    name : str
        A unique identifier for the source type (e.g. "feed")
    description : str
        A short description of the source type (e.g "RSS/Atom feed")
    """
    def parse(self):
        """
        Parse the source (all time-consuming operations should be done in this
        method)
        """
        raise NotImplementedError()

    def get_podcast(self):
        """
        Returns
        -------
        Podcast
        """
        raise NotImplementedError()

    def get_episodes(self):
        """
        Returns
        -------
        List[Episode]
            A list of episodes sorted by ascending publication date.
        """
        raise NotImplementedError()
