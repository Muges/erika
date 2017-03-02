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
A parser creating a podcast from an Atom/RSS feed
"""

import logging
from time import mktime
from datetime import datetime
import feedparser

from podcasts.library import Episode


def parse_feed(feed, podcast):
    """Parse the feed element"""
    try:
        image = feed.image.href
    except AttributeError:
        image = None

    podcast.title = feed.get("title", None)
    podcast.author = feed.get("author", None)
    podcast.image_url = image
    podcast.language = feed.get("language", None)
    podcast.subtitle = feed.get("subtitle", None)
    podcast.summary = feed.get("summary", None)
    podcast.link = feed.get("link", None)


def parse_links(links):
    """Parse an entry's links to find the audio file

    Returns
    -------
    Optional[str]
        The url of the audio file
    Optional[int]
        The size of the audio file
    Optional[str]
        The mimetype of the audio file
    """
    logger = logging.getLogger(__name__)

    for link in links:
        # Check that the link is an enclosure
        if "rel" not in link or link.rel != "enclosure":
            continue

        # Check that the link is valid
        if "href" not in link:
            logger.warning("Skipping enclosure with no href attribute.")
            continue

        return link.href, link.get("length", None), link.type

    logger.warning("No enclosure found.")
    return None, None, None


def parse_duration(string):
    """Parse a duration of the form [hours:]minutes:seconds"""
    duration = string.split(":")[:3]

    try:
        duration = [int(i) for i in duration]
    except ValueError:
        logger = logging.getLogger(__name__)
        logger.warning("Invalid duration : \"%s\".", string)
        return None

    hours, minutes, seconds = [0] * (3 - len(duration)) + duration

    return hours * 3600 + minutes * 60 + seconds


def parse_entry(entry):
    """Parse an entry

    Returns
    -------
    Episode
    """
    if "published_parsed" in entry:
        timestamp = mktime(entry.published_parsed)
        pubdate = datetime.fromtimestamp(timestamp)
    else:
        pubdate = None

    default_guid = "{} - {}".format(pubdate, entry.get("title", ""))

    try:
        image = entry.image.href
    except AttributeError:
        image = None

    file_url, file_size, mimetype = parse_links(entry.links)

    return Episode(
        guid=entry.get("id", default_guid),
        pubdate=pubdate,
        title=entry.get("title", None),
        duration=parse_duration(entry.get("itunes_duration", "")),
        image_url=image,
        subtitle=entry.get("subtitle", None),
        summary=entry.get("summary", None),
        link=entry.get("link", None),

        file_url=file_url,
        file_size=file_size,
        mimetype=mimetype
    )


def parse(podcast):
    """Parse a podcast from an Atom/RSS feed

    Parameters
    ----------
    podcast : podcasts.library.Podcast
        The podcast to parse

    Returns
    -------
    List[podcasts.library.Episode]
        The list of the podcast's episodes
    """
    logger = logging.getLogger(__name__)
    logger.debug("Parsing %s.", podcast.url)

    document = feedparser.parse(podcast.url)

    parse_feed(document.feed, podcast)
    episodes = [parse_entry(entry) for entry in document.entries]

    return episodes
