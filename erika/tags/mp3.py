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
The :mod:`erika.tags.mp3` module provides functions to set and get tags of mp3
files.
"""

from datetime import datetime
import imghdr
from mutagen.id3 import (  # pylint: disable=no-name-in-module
    TPE1, TALB, TIT2, TSOT, TDRC, ID3TimeStamp, COMM, WOAF, WFED, WORS, TXXX,
    APIC, TRCK, TCON, Encoding, PictureType
)

ENCODING = Encoding.UTF8


def set_tags(audio, episode):  # pylint: disable=too-many-branches
    """Set the tags of the mp3 audio file of an episode.

    Parameters
    ----------
    filename : str
        The audio file.
    episode : :class:`Episode`
        The corresponding episode.
    """
    if not audio.tags:
        audio.add_tags()

    # Author and titles
    if episode.podcast.author:
        audio.tags["TPE1"] = TPE1(ENCODING, episode.podcast.author)
    if episode.podcast.title:
        audio.tags["TALB"] = TALB(ENCODING, episode.podcast.title)
    if episode.title:
        audio.tags["TIT2"] = TIT2(ENCODING, episode.title)
        audio.tags["TSOT"] = TSOT(ENCODING, episode.title)

    # Publication date
    if episode.pubdate:
        timestamp = ID3TimeStamp(episode.pubdate.isoformat(' '))
        audio.tags["TDRC"] = TDRC(ENCODING, [timestamp])

    # Description
    if "COMM" not in audio.tags and episode.summary:
        audio.tags["COMM"] = COMM(ENCODING, desc="", text=episode.summary)

    # Links
    if episode.link:
        audio.tags["WOAF"] = WOAF(episode.link)
    if episode.podcast.url:
        audio.tags["WFED"] = WFED(episode.podcast.url)
    if episode.podcast.link:
        audio.tags["WORS"] = WORS(episode.podcast.link)
    if episode.guid:
        audio.tags["TXXX"] = TXXX(ENCODING, desc="", text=episode.guid)

    # Track number
    audio.tags["TRCK"] = TRCK(ENCODING, str(episode.track_number))

    # Image
    if "APIC:" not in audio.tags:
        data = episode.get_image()

        if data:
            if imghdr.what(None, h=data) == 'png':
                mimetype = 'image/png'
            else:
                mimetype = 'image/jpeg'

            audio.tags["APIC"] = APIC(ENCODING, desc="", mime=mimetype,
                                      type=PictureType.COVER_FRONT, data=data)

    # Genre
    audio.tags["TCON"] = TCON(ENCODING, text="Podcast")

    audio.save()


def get_tag(audio, tag):
    """Get an audio tag, or return None if it is not available."""
    try:
        return audio.tags[tag].text[0]
    except (KeyError, IndexError, TypeError):
        return None


def get_tags(audio):
    """Return the tags of an audio file."""
    date = get_tag(audio, "TDRC")
    try:
        date = datetime.strptime(date.text, "%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        date = None

    try:
        image = audio.tags["APIC:"].data
    except KeyError:
        image = None

    return {
        "podcast": get_tag(audio, "TALB"),
        "title": get_tag(audio, "TIT2"),
        "guid": get_tag(audio, "TXXX"),
        "pubdate": date,
        "image": image
    }
