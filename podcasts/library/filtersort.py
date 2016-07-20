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
Module handling the filtering of a database query.
"""

from collections import OrderedDict


class FilterSort(object):
    """
    Object handling the filtering of a database query.

    When displaying the episodes of a podcast, the database query should return
    all the episodes, including those which are currently not visible if there
    is a filter activated, so that the filters can be changed dynamically.
    However, since the loading of the episodes is done asynchronously, the
    episodes that are visible should be returned first to be displayed as soon
    as possible.

    The FilterSort objects store the current filtering state, and can be used
    to obtain the "ORDER BY ..." part of the query that achieves this.
    """
    def __init__(self):
        self.exprs = {}
        self.fields = {}
        self.sort_by = "pubdate"
        self.sort_descending = True

    def set_expr(self, field, expr):
        """
        Add a new field that will be evaluated to a certain expression in the
        SQL queries (e.g. the downloaded field of the EpisodeFilterSort
        object).
        """
        self.exprs[field] = expr

    def filter(self, field, value):
        """
        Add a new filter on an existing field (i.e. a database field or field
        created with the set_expr method).

        Parameters
        ----------
        field : str
            The name of the field.
        value : bool
            The value that the field should have, or None not to filter on this
            field.
        """
        if value is None:
            if field in self.fields:
                del self.fields[field]
        else:
            self.fields[field] = value

    def get_filter(self, field):
        """
        Get the current filter on this field.

        Parameters
        ----------
        field : str
            The name of the field.
        """
        return self.fields.get(field, None)

    def _filter_query(self, field):
        expr = self.exprs.get(field, field)
        descending = self.fields[field]
        return self._sort_order(expr, descending)

    def _sort_order(self, expr, descending):
        if descending:
            return "{} DESC".format(expr)
        else:
            return "{} ASC".format(expr)

    def query(self):
        """
        Get the sorting part of the SQL query (starting with " ORDER BY").
        """
        ordering_terms = [
            self._filter_query(field) for field in self.fields
        ] + [self._sort_order(self.sort_by, self.sort_descending)]

        return " ORDER BY " + ", ".join(ordering_terms)


class EpisodeFilterSort(FilterSort):
    """
    Object handling the filtering of the database table.
    """
    def __init__(self):
        FilterSort.__init__(self)
        self.set_expr("downloaded", "(local_path IS NOT NULL)")
