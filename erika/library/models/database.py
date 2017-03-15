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
Module defining the database
"""

import string
from playhouse.sqlite_ext import SqliteExtDatabase
from peewee import Model

from erika.config import DATABASE_PATH

database = SqliteExtDatabase(DATABASE_PATH)  # pylint: disable=invalid-name


class BaseModel(Model):
    """
    Base model defining which database to use.
    """
    class Meta:  # pylint: disable=too-few-public-methods, missing-docstring
        database = database


@database.func()
def slugify(name):
    """Remove non alphanumeric characters from a string and convert it to
    lowercase"""
    return ''.join(
        char for char in name.lower()
        if char in string.ascii_lowercase + string.digits
    )
