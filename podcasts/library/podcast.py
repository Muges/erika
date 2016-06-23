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
Object representing a podcast in the library
"""

from podcasts.library.row import Row


class Podcast(Row):
    """
    Object representing a podcast in the library

    Attributes
    ----------
    id : int
        The id of the podcast in the database
    source : str
        The name of the source type
    url : str
        The url of the source
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
    new_count : int
        Number of new episodes
    played_count : int
        Number of played episodes
    episodes_count : int
        Number of episodes
    """

    TABLE = "podcasts"
    PRIMARY_KEY = 'id'
    COLUMNS = [
        "source", "url", "title", "author", "image_url", "image_data",
        "language", "subtitle", "summary", "link"
    ]
    ATTRS = [
        "new_count", "played_count", "episodes_count"
    ]
