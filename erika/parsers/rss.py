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
The :mod:`erika.parsers.rss` module implements a parser for RSS and Atom feeds.
"""

import logging
from time import mktime
from datetime import datetime
import feedparser
import requests

from erika.library import Episode
from erika.util import plaintext_to_html, html_to_plaintext

MIN_SUBTITLE_LENGTH = 25


def parse_feed(feed, podcast):
    """Parse the feed element."""
    try:
        image = feed.image.href
    except AttributeError:
        image = None

    if image != podcast.image_url:
        # Only update the podcast image if it changed, to avoid
        # setting the field as dirty
        podcast.image_url = image

    podcast.title = feed.get("title", None)
    podcast.author = feed.get("author", None)
    podcast.language = feed.get("language", None)
    podcast.subtitle = feed.get("subtitle", None)
    podcast.summary = feed.get("summary", None)
    podcast.link = feed.get("link", None)


def parse_links(links):
    """Parse an entry's links to find the audio file.

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
    """Parse a duration of the form ``[hours:]minutes:seconds``."""
    if string == "":
        return None

    duration = string.split(":")[:3]

    try:
        duration = [int(i) for i in duration]
    except ValueError:
        logger = logging.getLogger(__name__)
        logger.warning("Invalid duration : \"%s\".", string)
        return None

    hours, minutes, seconds = [0] * (3 - len(duration)) + duration

    return hours * 3600 + minutes * 60 + seconds


def summary_to_subtitle(summary):
    """Convert a summary (in html) to a subtitle (in plaintext)."""
    summary_lines = [
        line.strip()
        for line in html_to_plaintext(summary).split("\n")
        if line.strip()
    ]

    # Get the first lines, until the total length is bigger than
    # MIN_SUBTITLE_LENGTH
    length = -1
    end = 0
    for line in summary_lines:
        length += 1 + len(line)
        end += 1
        if length > MIN_SUBTITLE_LENGTH:
            break

    return " ".join(summary_lines[:end])


def parse_entry(entry):
    """Parse an rss entry."""
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

    # Get summary
    try:
        if entry.summary_detail['type'] == "text/plain":
            summary = plaintext_to_html(entry["summary"])
        else:
            summary = entry["summary"]
    except AttributeError:
        summary = None

    # Create subtitle from summary (this usually gives better subtitles than
    # the ones in the rss feed)
    subtitle = summary_to_subtitle(summary)

    # Subtitle fallback
    if not subtitle:
        subtitle = entry.get("subtitle", None)

    # Summary fallback
    if not summary:
        summary = plaintext_to_html(subtitle)

    return Episode(
        guid=entry.get("id", default_guid),
        pubdate=pubdate,
        title=entry.get("title", None),
        duration=parse_duration(entry.get("itunes_duration", "")),
        image_url=image,
        subtitle=subtitle,
        summary=summary,
        link=entry.get("link", None),

        file_url=file_url,
        file_size=file_size,
        mimetype=mimetype
    )


def parse(podcast):
    """Parse an RSS or Atom feed.

    Parameters
    ----------
    podcast : :class:`Podcast`
        The podcast to parse.

    Returns
    -------
    list of :class:`Episode`
        A list of the podcast's episodes.
    """
    logger = logging.getLogger(__name__)
    logger.debug("Parsing %s.", podcast.url)

    response = requests.get(podcast.url, timeout=10)
    document = feedparser.parse(response.content)

    parse_feed(document.feed, podcast)
    episodes = [parse_entry(entry) for entry in document.entries]

    return episodes
