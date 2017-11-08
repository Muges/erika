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
A Model storing the configuration of the application as ``(key, value)`` pairs.
"""

from collections import namedtuple
import logging
from peewee import TextField

from erika.config import CONFIG_DEFAULTS
from erika.library.fields import JSONField
from .database import BaseModel


class Config(BaseModel):
    """A model storing the configuration of the application as ``(key, value)``
    pairs.

    The keys can be of the form ``group.key``, making it possible to
    get all the values of a certain group at once with the :func:`~get_group`
    method.

    The values can be of any type that is serializable by the ``json`` python
    module."""
    key = TextField(primary_key=True)
    value = JSONField(null=True)

    @classmethod
    def get_value(cls, key):
        """Return the value associated to a key."""
        return cls.get(Config.key == key).value

    @classmethod
    def set_value(cls, key, value):
        """Set the value associated to a key."""
        (cls
         .insert(key=key, value=value)
         .upsert()
         .execute())

    @classmethod
    def set_defaults(cls):
        """Set the default configuration values (ignoring the values that are
        already defined).

        The default values are stored in the
        :py:obj:`erika.config.CONFIG_DEFAULTS` dictionnary."""
        logger = logging.getLogger(".".join((__name__, cls.__name__)))
        logger.debug("Setting default configuration.")

        (cls
         .insert_many({"key": key, "value": value}
                      for key, value in CONFIG_DEFAULTS.items())
         .on_conflict('IGNORE')
         .execute())

    @staticmethod
    def get_group(group):
        """Return the configurations pairs belonging to a group (i.e. whose
        keys are of the form ``group.*``).

        Example
        -------
        Assuming the config table contains the following data:

        +---------------------+------------------+
        | key                 | value            |
        +=====================+==================+
        | downloads.workers   | 2                |
        +---------------------+------------------+
        | gpodder.synchronize | False            |
        +---------------------+------------------+
        | gpodder.hostname    | 'gpodder.net'    |
        +---------------------+------------------+

        .. code-block:: python

            >>>Config.get_group("downloads")
            configuration(workers=2)
            >>>Config.get_group("gpodder")
            configuration(synchronize=False, hostname='gpodder.net')
            >>>Config.get_group("nothing")
            configuration()

        Parameters
        ----------
        group : str
           The name of the group.

        Returns
        -------
        namedtuple
            A namedtuple containing the ``(key, value)`` pairs.
        """
        prefix = group + "."
        lprefix = len(prefix)
        values = {}

        configs = Config.select().where(Config.key.startswith(prefix))
        for config in configs:
            values[config.key[lprefix:]] = config.value

        type_ = namedtuple("configuration", values.keys())
        return type_(**values)
