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
The :mod:`erika.tags` module provides functions to set and get tags for various
audio format.

For now, the only supported format is MP3.
"""

import logging
import mutagen

from . import mp3


def set_tags(filename, episode):
    """Set the tags of the audio file of an episode.

    Parameters
    ----------
    filename : str
        The audio file.
    episode : :class:`Episode`
        The corresponding episode.
    """
    logger = logging.getLogger(__name__)

    try:
        audio = mutagen.File(filename)
    except Exception:  # pylint: disable=broad-except
        logger.exception("Unable to set tags for '%s'.", filename)
        return None

    if isinstance(audio, mutagen.mp3.MP3):
        mp3.set_tags(audio, episode)
    else:
        logger.warning("Unable to set tags (unsupported file format) for "
                       "'%s'.", filename)


def get_tags(filename):
    """Get the tags of an audio file.

    Parameters
    ----------
    filename : str
        The audio file.
    """
    logger = logging.getLogger(__name__)

    try:
        audio = mutagen.File(filename)
    except Exception:  # pylint: disable=broad-except
        logger.exception("Unable to get tags for '%s'.", filename)
        return None

    if isinstance(audio, mutagen.mp3.MP3):
        return mp3.get_tags(audio)
    else:
        logger.warning("Unable to get tags (unsupported file format) for "
                       "'%s'.", filename)
        return None
