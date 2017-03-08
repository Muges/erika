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
An horizontal Gtk.Paned which becomes vertical if there is not enough width
"""

from gi.repository import Gtk


class Paned(Gtk.Paned):
    """An horizontal Gtk.Paned which becomes vertical if there is not enough
    width"""
    def __init__(self):
        super().__init__()

        self.limit_width = 0

        self.connect('size_allocate', Paned._on_size_allocate)

    def set_limit_width(self, width):
        """Set the minimal width of the widget

        If the available width is less than the minimal width, the
        Paned will be reoriented vertically."""
        self.limit_width = width

    def _on_size_allocate(self, allocation):
        if allocation.width < self.limit_width:
            self.set_orientation(Gtk.Orientation.VERTICAL)
        else:
            self.set_orientation(Gtk.Orientation.HORIZONTAL)
