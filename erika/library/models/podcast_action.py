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
Table containing the episode actions
"""

from peewee import TextField

from .database import BaseModel


class PodcastAction(BaseModel):
    """A model used to store podcast actions in the library.

    The podcast actions are used for the gpodder synchronization.

    Attributes
    ----------
    podcast_url : str
        The url of the podcast.
    action : str
        The type of the action (add or remove).
    """
    podcast_url = TextField(primary_key=True)
    action = TextField()

    @staticmethod
    def new(**kwargs):
        """Create a new podcast action (or overwrite an existing one)."""
        (PodcastAction
         .insert(**kwargs)
         .upsert()
         .execute())
