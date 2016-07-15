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

# TODO : track number

import imghdr
from mutagen.id3 import (
    TPE1, TALB, TIT2, TSOT, TDRC, ID3TimeStamp, COMM, WOAF, WFED, WORS, TXXX,
    UrlFrame, APIC
)


def set_tags(audio, episode):
    """
    Set the tags of the mp3 audio file of an episode.

    Parameters
    ----------
    filename : str
        The audio file
    episode : Episode
        The corresponding episode
    """
    # Author and titles
    if episode.podcast.author:
        audio.tags["TPE1"] = TPE1(3, episode.podcast.author)
    if episode.podcast.title:
        audio.tags["TALB"] = TALB(3, episode.podcast.title)
    if "TIT2" not in audio.tags and episode.title:
        audio.tags["TIT2"] = TIT2(3, episode.title)
        audio.tags["TSOT"] = TSOT(3, episode.title)

    # Publication date
    if episode.pubdate:
        timestamp = ID3TimeStamp(episode.pubdate.isoformat())
        audio.tags["TDRC"] = TDRC(3, [timestamp])

    # Description
    if "COMM" not in audio.tags and episode.summary:
        audio.tags["COMM"] = COMM(3, text=episode.summary)

    # Links
    if episode.link:
        audio.tags["WOAF"] = WOAF(episode.link)
    if episode.podcast.url:
        audio.tags["WFED"] = WFED(episode.podcast.url)
    if episode.podcast.link:
        audio.tags["WORS"] = WORS(episode.podcast.link)
    if episode.guid:
        audio.tags["TXXX"] = TXXX(3, episode.guid)

    # Image
    if "APIC" not in audio.tags:
        data = episode.get_image()

        if data:
            if imghdr.what(None, h=data) == 'png':
                mimetype = 'image/png'
            else:
                mimetype = 'image/jpeg'

            audio.tags["APIC"] = APIC(3, mime=mimetype, type=3, data=data)

    audio.tags.save()
