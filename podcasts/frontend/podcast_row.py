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
Row in the list of podcasts
"""

# TODO : Test with invalid images.
# TODO : Check summary format (plaintext or html?) for tooltip.

from gi.repository import Gtk
from gi.repository import GdkPixbuf
from gi.repository import Pango

IMAGE_SIZE = 48


class PodcastRow(Gtk.ListBoxRow):
    """
    Row in the list of podcasts
    """
    def __init__(self, podcast):
        Gtk.ListBoxRow.__init__(self)

        self.podcast = podcast

        grid = Gtk.Grid()
        grid.set_column_spacing(5)
        grid.set_tooltip_markup((
            "<b>{title}</b>\n"
            "{total} episodes\n\n"

            "{summary}"
        ).format(
            title=self.podcast["title"],
            total=self.podcast["total"],
            summary=self.podcast["summary"]
        ))
        self.add(grid)

        # Podcast Image
        if self.podcast["image_data"]:
            image = Gtk.Image.new_from_pixbuf(self.get_pixbuf())
            grid.attach(image, 0, 0, 1, 2)

        # Title label
        label = Gtk.Label()
        label.set_hexpand(True)
        label.set_alignment(xalign=0, yalign=0.5)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_markup("<b>{}</b>".format(self.podcast["title"]))
        grid.attach(label, 1, 0, 1, 1)

        # Unplayed and new counts label
        unplayed = self.podcast["total"] - self.podcast["played"]
        label = Gtk.Label()
        label.set_alignment(xalign=1, yalign=0.5)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_markup(str(self.podcast["new"]))
        label.set_markup("{} ({})".format(unplayed, self.podcast["new"]))
        grid.attach(label, 2, 0, 1, 1)

        # Subtitle label
        label = Gtk.Label()
        label.set_alignment(xalign=0, yalign=0.5)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_markup(self.podcast["subtitle"])
        grid.attach(label, 1, 1, 2, 1)

    def get_pixbuf(self):
        """
        Return the image of the podcast as a scaled pixbuf
        """
        loader = GdkPixbuf.PixbufLoader.new()
        loader.write(self.podcast["image_data"])
        pixbuf = loader.get_pixbuf()
        loader.close()

        return pixbuf.scale_simple(IMAGE_SIZE, IMAGE_SIZE,
                                   GdkPixbuf.InterpType.BILINEAR)
