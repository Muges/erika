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
Formatting functions
"""


def format_duration(seconds):
    """Format a duration as ``[hours:]minutes:seconds``.

    Parameters
    ----------
    seconds : int
        Duration in seconds.

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
    """Format a duration as ``h hours, m minutes``.

    Parameters
    ----------
    seconds : int
        Duration in seconds.

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
    """Convert a size in bytes into a human readable string.

    Example
    -------
    ::

        >>>format_size(2.25*1024)
        '2.25 kB'

    Parameters
    ----------
    size : int
        Size in bytes.

    Returns
    -------
    str
    """
    for unit in ['bytes', 'kB', 'MB']:
        if size < 1024:
            return "{:.2f} {}".format(size, unit)
        size /= 1024

    return "{:.2f} {}".format(size, 'GB')
