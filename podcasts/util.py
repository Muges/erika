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

EXTENSIONS = {
    "audio/mpeg": ".mp3",
    "audio/x-m4a": ".m4a",
    "video/mp4": ".mp4",
    "video/x-m4v": ".m4v",
    "video/quicktime": ".mov",
    "application/pdf": ".pdf",
    "document/x-epub": ".epub",
}


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
