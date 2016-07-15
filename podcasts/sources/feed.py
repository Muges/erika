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
A source creating a podcast from an Atom/RSS feed.
"""

from time import mktime
from datetime import datetime
import logging
import feedparser

from .source import Source, Podcast, Episode


class Feed(Source):
    """
    A source creating a podcast from an RSS/Atom feed.
    """

    name = "feed"
    description = "RSS/Atom feed"

    def __init__(self, url):
        self.logger = logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__))

        self.url = url
        self.podcast = None
        self.episodes = []

    def _parse_duration(self, string):
        duration = string.split(":")[:3]

        try:
            duration = [int(i) for i in duration]
        except ValueError:
            self.logger.warning("Invalid duration : \"%s\".", string)
            return None

        hours, minutes, seconds = [0] * (3 - len(duration)) + duration

        return hours * 3600 + minutes * 60 + seconds

    def _parse_links(self, links):
        for link in links:
            # Check that the link is an enclosure
            if "rel" not in link or link.rel != "enclosure":
                continue

            # Check that the link is valid
            if "href" not in link:
                self.logger.warning(
                    "Skipping enclosure with no href attribute.")
                continue

            return link.type, link.get("length", None), link.href

        self.logger.warning("No enclosure found.")
        return None, None, None

    def _parse_entry(self, entry):
        if "published_parsed" in entry:
            timestamp = mktime(entry.published_parsed)
            pubdate = datetime.fromtimestamp(timestamp)
        else:
            pubdate = None

        default_guid = "{} - {}".format(pubdate, entry.get("title", ""))

        try:
            image = entry.image.href
        except AttributeError:
            image = self.podcast.image

        mimetype, file_size, file_url = self._parse_links(entry.links)

        self.episodes.append(Episode(
            guid=entry.get("id", default_guid),
            pubdate=pubdate,
            title=entry.get("title", None),

            duration=self._parse_duration(entry.get("itunes_duration", "")),
            image=image,
            link=entry.get("link", None),
            subtitle=entry.get("subtitle", None),
            summary=entry.get("summary", None),

            mimetype=mimetype,
            file_size=file_size,
            file_url=file_url
        ))

    def _parse_feed(self, feed):
        try:
            image = feed.image.href
        except AttributeError:
            image = None

        self.podcast = Podcast(
            title=feed.get("title", None),
            author=feed.get("author", None),

            image=image,
            language=feed.get("language", None),
            subtitle=feed.get("subtitle", None),
            summary=feed.get("summary", None),

            link=feed.get("link", None)
        )

    def parse(self):
        self.logger.info("Parsing %s.", self.url)

        document = feedparser.parse(self.url)

        self._parse_feed(document.feed)

        for entry in document.entries:
            self._parse_entry(entry)

    def get_podcast(self):
        return self.podcast

    def get_episodes(self):
        return sorted(self.episodes, key=lambda e: e.pubdate)
