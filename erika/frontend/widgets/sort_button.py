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
A button used to represent sorting options
"""

from gi.repository import Gtk


class SortButton(Gtk.Button):
    """A button used to represent sorting options

    The button has two states : ascending or descending.
    """
    def __init__(self, sort_by):
        Gtk.Button.__init__(self)
        self.connect("clicked", SortButton._on_clicked)

        self.sort_by = sort_by
        self.descending = True

        self.ascending_image = Gtk.Image.new_from_icon_name(
            "view-sort-ascending-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        self.descending_image = Gtk.Image.new_from_icon_name(
            "view-sort-descending-symbolic", Gtk.IconSize.SMALL_TOOLBAR)

        self.set_descending(True)

    def set_descending(self, descending):
        """Change the state of the button

        Parameters
        ----------
        descending : bool
            True if the sorting order whould be descending.
        """
        self.descending = descending

        if descending:
            self.set_image(self.descending_image)
            self.set_tooltip_text("Sort by ascending {}".format(self.sort_by))
        else:
            self.set_image(self.ascending_image)
            self.set_tooltip_text("Sort by descending {}".format(self.sort_by))

    def get_descending(self):
        """Return the state of the button

        Returns
        -------
        bool
            True if the sorting order whould be descending.
        """
        return self.descending

    def _on_clicked(self):
        """Called when the button is clicked

        Toggle the state of the button.
        """
        self.set_descending(not self.get_descending())
