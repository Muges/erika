# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Muges
# Copyright (C) 2015 Patrick Griffis <tingping@tingping.se>
# Copyright (C) 2014 Christian Hergert <christian@hergert.me>
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
ScrolledWindow that sets a max size for the child to grow into.
"""

from gi.repository import Gtk
from gi.repository import GObject


class ScrolledWindow(Gtk.ScrolledWindow):
    """
    ScrolledWindow that sets a max size for the child to grow into.

    Source
    ------
    https://gist.github.com/TingPing/e70e09722e0fc37d2386
    """
    __gtype_name__ = "EggScrolledWindow"

    max_content_height = GObject.Property(type=int, default=-1, nick="Max Content Height",
                                          blurb="The maximum height request that can be made")
    max_content_width = GObject.Property(type=int, default=-1, nick="Max Content Width",
                                         blurb="The maximum width request that can be made")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connect_after("notify::max-content-height", lambda obj, param: self.queue_resize())
        self.connect_after("notify::max-content-width", lambda obj, param: self.queue_resize())

    def set_max_content_height(self, value):
        self.max_content_height = value

    def set_max_content_width(self, value):
        self.max_content_width = value

    def get_max_content_height(self):
        return self.max_content_height

    def get_max_content_width(self):
        return self.max_content_width

    def do_get_preferred_height(self):
        min_height, natural_height = Gtk.ScrolledWindow.do_get_preferred_height(self)
        child = self.get_child()

        if natural_height and self.max_content_height > -1 and child:

            style = self.get_style_context()
            border = style.get_border(style.get_state())
            additional = border.top + border.bottom

            child_min_height, child_nat_height = child.get_preferred_height()
            if child_nat_height > natural_height and self.max_content_height > natural_height:
                natural_height = min(self.max_content_height, child_nat_height) + additional;

        return min_height, natural_height

    def do_get_preferred_width(self):
        min_width, natural_width = Gtk.ScrolledWindow.do_get_preferred_width(self)
        child = self.get_child()

        if natural_width and self.max_content_width > -1 and child:

            style = self.get_style_context()
            border = style.get_border(style.get_state())
            additional = border.left + border.right + 1

            child_min_width, child_nat_width = child.get_preferred_width()
            if child_nat_width > natural_width and self.max_content_width > natural_width:
                natural_width = min(self.max_content_width, child_nat_width) + additional;

        return min_width, natural_width
