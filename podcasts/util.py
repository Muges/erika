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
Utility functions
"""

from itertools import chain
import os.path
import re
import string

from podcasts.config import LIBRARY_DIR, DIRNAME_TEMPLATE, FILENAME_TEMPLATE

EXTENSIONS = {
    "audio/mpeg": ".mp3",
    "audio/x-m4a": ".m4a",
    "video/mp4": ".mp4",
    "video/x-m4v": ".m4v",
    "video/quicktime": ".mov",
    "application/pdf": ".pdf",
    "document/x-epub": ".epub",
}

DELETE_CHARS = (
    ''.join(map(chr, chain(range(0, 32), range(127, 160)))) +
    '?<>|"'
)

TRANSLATION_TABLE = str.maketrans('/\\:*\n\t', '----  ', DELETE_CHARS)

MAX_FILENAME_LENGTH = 255

# List of filenames that are reserved on linux or windows
FORBIDDEN_FILENAMES = [
    ".", "..", "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4",
    "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4",
    "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
]

HYPHEN_PATTERN = r"(\S)(\s+-|-\s+|\s+-\s+)(\S)"
HYPHEN_REPLACE = r"\1 - \3"


def format_duration(seconds):
    """
    Format a duration as "[hours:]minutes:seconds".

    Parameters
    ----------
    seconds : int
        Duration in seconds

    Returns
    -------
    str
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if hours > 0:
        return "{}:{:02d}:{:02d}".format(hours, minutes, seconds)
    else:
        return "{}:{:02d}".format(minutes, seconds)


def format_fulltext_duration(seconds):
    """
    Format a duration as "h hours, m minutes".

    Parameters
    ----------
    seconds : int
        Duration in seconds

    Returns
    -------
    str
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if hours > 2:
        if minutes >= 30:
            hours += 1
        return "{} hours".format(hours)
    elif hours > 0:
        return "{} hours, {} minutes".format(hours, minutes)
    if minutes > 2:
        if seconds >= 30:
            minutes += 1
        return "{} minutes".format(minutes)
    elif minutes > 0:
        return "{} minutes, {} seconds".format(minutes, seconds)
    else:
        return "{} seconds".format(seconds)


def format_size(size):
    """
    Return a human readable size.

    Parameters
    ----------
    size : int
        Size in bytes

    Returns
    -------
    str
    """
    unit = 'bytes'

    for u in ['kB', 'MB', 'GB']:
        if size < 1024:
            break

        unit = u
        size /= 1024
    return "{:.2f} {}".format(size, unit)


def guess_extension(mimetype):
    """
    Guess a file's extension from its mimetype.

    The mimetypes.guess_extension sometimes return uncommon extensions, such as
    ".mp2" instead of ".mp3" for mimetype "audio/mpeg". This function tries
    to return consistent extensions for common podcast formats, and falls back
    to mimetypes.guess_extension for other formats.

    Parameters
    ----------
    mimetype : str
        The mimetype of a file

    Returns
    -------
    str
        The extension of the file, with a trailing '.'
    """
    try:
        return EXTENSIONS[mimetype]
    except KeyError:
        return mimetypes.guess_extension(mimetype) or ''


def sanitize_filename(filename):
    """
    Sanitize a string to make it a valid filename.

    This should hopefully work for windows and linux.
    """
    # Remove or replace forbidden characters
    filename = filename.translate(TRANSLATION_TABLE)

    # Make sure hyphens are surrounded by exactly one space on each side or no
    # spaces at all
    filename = re.sub(HYPHEN_PATTERN, HYPHEN_REPLACE, filename)

    # Truncate filenames
    filename = filename[:MAX_FILENAME_LENGTH]

    if filename in FORBIDDEN_FILENAMES:
        filename += "-podcast"

    return filename


def slugify(name):
    """
    Remove non alphanumeric characters from a string and convert it to
    lowercase.
    """
    name = name.lower()
    return ''.join([
        char for char in name
        if char in string.ascii_lowercase + string.digits
    ])


def episode_filename(episode, extension):
    """
    Return the filename of an episode.

    Parameters
    ----------
    episode : Episode
    extension : str

    Returns
    -------
    str
        The path of the episode.
    """
    dirname = os.path.join(
        LIBRARY_DIR,
        sanitize_filename(DIRNAME_TEMPLATE.format(podcast=episode.podcast))
    )
    filename = os.path.join(
        dirname,
        sanitize_filename(FILENAME_TEMPLATE.format(episode=episode))
    )

    return filename + extension
