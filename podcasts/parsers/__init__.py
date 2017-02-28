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
Module used to parse podcasts.
"""

import importlib


def parse(parser_name, url):
    """Parse a podcast

    Returns
    -------
    podcasts.library.Podcast
        The podcast
    List[podcasts.library.Episode]
        The list of the podcast's episodes
    """
    if "." in parser_name:
        raise ValueError("{} is not a valid parser name.".format(parser_name))

    try:
        parser = importlib.import_module("."+parser_name, __name__)
    except ModuleNotFoundError:
        raise ValueError("{} is not a valid parser name.".format(parser_name))

    podcast, episodes = parser.parse(url)

    podcast.parser = parser_name
    podcast.url = url

    for episode in episodes:
        episode.podcast = podcast

    return podcast, episodes
