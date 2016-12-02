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

import logging


class RowType(type):
    """
    Metaclass used to add the ALL_ATTRS and UPDATE_QUERY to the Row subclasses.
    """
    def __new__(cls, name, bases, attrs):
        if "TABLE" in attrs and "COLUMNS" in attrs:
            attrs['ALL_ATTRS'] = (
                attrs['COLUMNS'] + attrs['ATTRS'] + [attrs['PRIMARY_KEY']]
            )

            attrs["UPDATE_QUERY"] = """
                UPDATE {}
                SET {}
                WHERE {}=?
            """.format(
                attrs['TABLE'],
                ", ".join("{}=?".format(col) for col in attrs['COLUMNS']),
                attrs['PRIMARY_KEY']
            )

            attrs["DELETE_QUERY"] = """
                DELETE FROM {}
                WHERE {}=?
            """.format(
                attrs['TABLE'],
                attrs['PRIMARY_KEY']
            )

        return super(RowType, cls).__new__(cls, name, bases, attrs)


class Row(object, metaclass=RowType):
    """
    Abstract class for objects representing a row in a database table.

    The following class attributes should be defined by the subclasses :

    TABLE : str
        Name of the table
    PRIMARY_KEY : str
        Name of the primary key column
    COLUMNS : List[str]
        List of column names of the table
    ATTRS : List[str]
        List of attributes that are not saved in the database

    And the following ones will be automatically computed :

    ALL_ATTRS : List[str]
        List of all the attributes of the objects of the class
    UPDATE_QUERY : str
        SQL query updating all the attributes of a row
    """

    def __init__(self, **kwargs):
        self.logger = logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__))

        # Get the values of each column in the kaywords arguments
        for column in self.__class__.ALL_ATTRS:
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

    def get_update_attrs(self):
        """
        Return a list of values to save in the database

        Returns
        -------
        List[Any]
            List of columns values to save in the database
        """
        return (
            [getattr(self, column) for column in self.__class__.COLUMNS] +
            [getattr(self, self.__class__.PRIMARY_KEY)]
        )

    def get_delete_attrs(self):
        """
        Return a list containing the primary key of the row

        Returns
        -------
        List[Any]
            List containing the primary key of the row
        """
        return (
            [getattr(self, self.__class__.PRIMARY_KEY)]
        )
        
    
    def __eq__(self, other):
        """
        Check if two rows are the same.
        """
        return (
            self.__class__ == other.__class__ and
            getattr(self, self.__class__.PRIMARY_KEY) ==
            getattr(other, self.__class__.PRIMARY_KEY)
        )
