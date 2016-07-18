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
List of podcasts
"""

# TODO : Test with invalid images.
# TODO : Test with non square images.
# TODO : Check summary format (plaintext or html?) for tooltip.
# TODO : Add placeholder image
# TODO : Add "All podcasts" row
# TODO : Escape markup

from gi.repository import Gtk
from gi.repository import GdkPixbuf
from gi.repository import GObject

from podcasts.library import Library
from podcasts.frontend.widgets import Label, IndexedListBox
from podcasts.frontend import htmltopango

IMAGE_SIZE = 64
SUBTITLE_LINES = 2


class PodcastList(IndexedListBox):
    """
    List of podcasts

    Signals
    -------
    podcast-selected(podcasts.library.Podcast)
        Emitted when a podcast is selected
    """

    __gsignals__ = {
        'podcast-selected':
            (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
    }

    def __init__(self):
        super().__init__()
        self.set_selection_mode(Gtk.SelectionMode.BROWSE)
        self.set_sort_func(self.sort_func)
        self.connect("row-selected", PodcastList._on_row_selected)

    def update(self):
        """
        Update the list of podcasts
        """
        # Set of ids that should be removed
        remove_ids = self.get_ids()

        library = Library()
        for podcast in library.get_podcasts():
            try:
                row = self.get_row(podcast.id)
            except ValueError:
                # The row does not exist, create it
                row = PodcastRow(podcast)
                self.add_with_id(row, podcast.id)
            else:
                # The row already exists, update it
                remove_ids.remove(podcast.id)
                row.podcast = podcast
                row.update()

        # Remove the podcasts that are not in the database anymore
        for podcast_id in remove_ids:
            self.remove_id(podcast_id)

        if self.get_selected_row() is None:
            self.select_row(self.get_row_at_index(0))

    def update_podcast(self, podcast_id):
        """
        Update a podcast

        Parameters
        ----------
        podcast_id : int
            The id of the podcast
        """
        try:
            row = self.get_row(podcast_id)
        except ValueError:
            pass
        else:
            library = Library()
            library.update_counts(row.podcast)
            row.update()

    def update_current(self):
        """
        Update the selected row
        """
        row = self.get_selected_row()

        if row:
            library = Library()
            library.update_counts(row.podcast)
            row.update()

    def _on_row_selected(self, row):
        """
        Called when a row is selected.

        Emit the podcast-selected signal.
        """
        if row:
            self.emit('podcast-selected', row.podcast)

    def sort_func(self, row1, row2):
        """
        Compare two rows to determine which should be first. Sort them
        alphabetically by podcast title.

        Parameters
        ----------
        row1 : Gtk.ListBoxRow
            The first row
        row2 : Gtk.ListBoxRow
            The second row

        Returns
        -------
        int
            -1 if row1 should be before row2,
            0 if they are equal,
            1 otherwise
        """
        if row1.podcast.title < row2.podcast.title:
            return -1
        elif row1.podcast.title == row2.podcast.title:
            return 0
        else:
            return 1


class PodcastRow(Gtk.ListBoxRow):
    """
    Row in the list of podcasts
    """
    def __init__(self, podcast):
        Gtk.ListBoxRow.__init__(self)

        self.podcast = podcast

        self.grid = Gtk.Grid()
        self.grid.set_column_spacing(5)
        self.add(self.grid)

        # Podcast Image
        self.icon = Gtk.Image()
        self.grid.attach(self.icon, 0, 0, 1, 2)

        # Podcast title
        self.title = Label()
        self.title.set_hexpand(True)
        self.grid.attach(self.title, 1, 0, 1, 1)

        # Unplayed and new counts
        self.counts = Label()
        self.counts.set_alignment(xalign=1, yalign=0.5)
        self.grid.attach(self.counts, 2, 0, 1, 1)

        # Podcast subtitle
        self.subtitle = Label(lines=SUBTITLE_LINES)
        self.grid.attach(self.subtitle, 1, 1, 2, 1)

        self.show_all()

        self.update()

    def update(self):
        """
        Update the widget
        """
        self.grid.set_tooltip_markup((
            "<b>{title}</b>\n"
            "{total} episodes\n\n"

            "{summary}"
        ).format(
            title=self.podcast.title,
            total=self.podcast.episodes_count,
            summary=htmltopango.convert(self.podcast.summary)
        ))

        # Podcast Image
        if self.podcast.image_data:
            self.icon.show()
            self.icon.set_from_pixbuf(self.get_pixbuf())
        else:
            self.icon.hide()

        # Podcast title
        self.title.set_markup("<b>{}</b>".format(self.podcast.title))

        # Unplayed and new counts
        unplayed = self.podcast.episodes_count - self.podcast.played_count
        self.counts.set_text(
            "{} ({})".format(unplayed, self.podcast.new_count))

        # Podcast subtitle
        self.subtitle.set_text(self.podcast.subtitle or self.podcast.summary)

    def get_pixbuf(self):
        """
        Return the image of the podcast as a scaled pixbuf
        """
        loader = GdkPixbuf.PixbufLoader.new()
        loader.write(self.podcast.image_data)
        pixbuf = loader.get_pixbuf()
        loader.close()

        return pixbuf.scale_simple(IMAGE_SIZE, IMAGE_SIZE,
                                   GdkPixbuf.InterpType.BILINEAR)
