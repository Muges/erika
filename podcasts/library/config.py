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
Table containing the configuration.
"""

import logging
import json
from peewee import TextField

from podcasts.library.database import BaseModel
from podcasts.config import CONFIG_DEFAULTS


class JSONField(TextField):
    """A field used to store values of (almost) any type in JSON"""
    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        if value is not None:
            return json.loads(value)


class Config(BaseModel):
    """Model for the configuration of the application"""
    key = TextField(primary_key=True)
    value = JSONField(null=True)

    @classmethod
    def get_value(cls, key):
        """Return the value associated to a key"""
        return cls.get(Config.key == key).value

    @classmethod
    def set_value(cls, key, value):
        """Set the value associated to a key"""
        (cls
         .insert(key=key, value=value)
         .upsert()
         .execute())

    @classmethod
    def set_defaults(cls):
        """Set the default values"""
        logger = logging.getLogger(".".join((__name__, cls.__name__)))
        logger.debug("Setting default configuration.")

        (cls
         .insert_many({"key": key, "value":  value}
                      for key, value in CONFIG_DEFAULTS.items())
         .on_conflict('IGNORE')
         .execute())
