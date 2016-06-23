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
Row object
"""


class Row(object):
    """
    Abstract class for objects representing a row in a database table.

    Class Attributes
    ----------------
    TABLE : str
        Name of the table
    COLUMNS : List[str]
        List of column names of the table.
    """
    def __init__(self, **kwargs):
        # Get the values of each column in the kaywords arguments
        for column in self.__class__.COLUMNS:
            try:
                setattr(self, column, kwargs.pop(column))
            except KeyError:
                raise TypeError((
                    "{}.__init__() missing required argument '{}'"
                ).format(self.__class__.__name__, column))

        # Check that all the arguments corresponded to a column
        try:
            arg = kwargs.popitem()
        except KeyError:
            pass
        else:
            raise TypeError((
                "{}.__init__() got an unexpected keyword argument '{}'"
            ).format(self.__class__.__name__, arg))
