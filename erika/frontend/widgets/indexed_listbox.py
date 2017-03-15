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
A ListBox whose rows are indexed
"""

import logging

from .listbox import ListBox


class IndexedListBox(ListBox):
    """A ListBox whose rows are indexed"""
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__))

        self.rows = {}

    def get_ids(self):
        """Return the ids of all the rows

        Returns
        -------
        set
        """
        return set(self.rows.keys())

    def get_row(self, row_id):
        """Return a row given its id

        Parameters
        ----------
        row_id
            The id of the row

        Returns
        -------
        Gtk.ListBoxRow

        Raises
        ------
        ValueError if there is no row with this id
        """
        if row_id not in self.rows:
            raise ValueError(
                "The ListBox has no row with id '{}'.".format(row_id))

        return self.rows[row_id]

    def add_with_id(self, row, row_id):
        """Add a row with a certain id

        Parameters
        ----------
        row : Gtk.ListBoxRow
            The row
        row_id
            The id of the row

        Raises
        ------
        ValueError if there is already a row with this id
        """
        if row_id in self.rows:
            raise ValueError(
                "The ListBox already has a row with id '{}'.".format(row_id))

        self.rows[row_id] = row
        self.add(row)

    def remove_id(self, row_id):
        """Remove a row given its id

        Parameters
        ----------
        row_id
            The id of the row to remove

        Raises
        ------
        ValueError if there is no row with this id
        """
        try:
            row = self.rows.pop(row_id)
        except KeyError:
            raise ValueError(
                "The ListBox has no row with id '{}'.".format(row_id))

        self.remove(row)

    def clear(self):
        """Remove all the rows"""
        for child in self.get_children():
            child.destroy()

        self.rows = {}
