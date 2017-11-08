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
The :mod:`erika.parsers` module implements parsers for the sources of podcasts.

A parser is a submodule of the :mod:`erika.parsers` module. It should implement
a ``parse`` function, which, given a podcast, parses its source, set its
attributes, and returns a list of its episodes (see the
:mod:`erika.parsers.rss` module for an example).

Each :class:`Podcast` has an attribute ``parser``, which is the name of the
submodule that should be used.

For now the only available is the :mod:`erika.parsers.rss` module, for RSS and
Atom feeds, and support for different parsers has not yet been added to the
GUI.
"""

import importlib


def parse(podcast):
    """Parse a podcast source, edit the podcast's attribute, and return a list
    of the podcast's episode.

    Parameters
    ----------
    podcast : :class:`Podcast`
        The podcast to parse.

    Returns
    -------
    list of :class:`Episode`
        A list of the podcast's episodes.
    """
    if "." in podcast.parser:
        raise ValueError(
            "{} is not a valid parser name.".format(podcast.parser))

    try:
        parser = importlib.import_module(".".join((__name__, podcast.parser)))
    except ModuleNotFoundError:
        raise ValueError(
            "{} is not a valid parser name.".format(podcast.parser))

    episodes = parser.parse(podcast)

    for episode in episodes:
        episode.podcast = podcast

    return sorted(episodes, key=lambda e: e.pubdate)
