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


def format_position(position, duration):
    """
    Format a position as "[hours:]minutes:seconds", in the same format as
    a duration would be rendered by format_duration.

    Example
    -------

        >>> position = 10
        >>> duration = 3600
        >>> format_duration(position)
        ... '0:10'
        >>> format_duration(duration)
        ... '1:00:00'
        >>> format_position(position, duration)
        ... '0:00:10'

    Parameters
    ----------
    position : int
        Position in seconds
    duration : int
        Duration in seconds
    """
    minutes, seconds = divmod(position, 60)
    hours, minutes = divmod(minutes, 60)

    duration_minutes, duration_seconds = divmod(duration, 60)
    duration_hours, duration_minutes = divmod(duration_minutes, 60)

    if duration_hours > 0:
        return "{}:{:02d}:{:02d}".format(hours, minutes, seconds)
    elif duration_minutes >= 10:
        return "{:02d}:{:02d}".format(hours, minutes, seconds)
    else:
        return "{}:{:02d}".format(minutes, seconds)
