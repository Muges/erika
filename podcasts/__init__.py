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

import logging

from . import sources


FILENAMES = [
    "tests/data/itunes.xml",
    "http://www.bbc.co.uk/programmes/p02nrvd3/episodes/downloads.rss",
    "http://aliceisntdead.libsyn.com/rss",
    "http://feeds.feedburner.com/WelcomeToNightVale"
]


def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # File output
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(levelname)-8s (%(name)s) : %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    for filename in FILENAMES:
        source = sources.get(filename)
        source.parse()
        podcast = source.get_podcast()
        episodes = source.get_episodes()

        print(podcast.title)
        for episode in episodes:
            print("   ", episode.pubdate, "-", episode.title)
        print()
