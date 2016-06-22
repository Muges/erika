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

# TODO : pagination (50, 100?)
# TODO : correct rendering lag
# TODO : icons fallback

"""
List of episodes
"""

from gi.repository import GLib
from gi.repository import Gtk

from podcasts.library import Library
from podcasts.util import format_duration
from .widgets import Label, ListBox

SUBTITLE_LINES = 4
CHUNK_SIZE = 10


class EpisodeList(ListBox):
    """
    List of episodes
    """
    def __init__(self):
        ListBox.__init__(self)
        self.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        self.set_sort_func(self.sort_func, -1)

    def select(self, podcast):
        """
        Update the list of episodes

        Parameters
        ----------
        podcast : podcasts.library.Podcast
            The podcast whose episodes will be displayed
        """
        # Remove children
        for child in self.get_children():
            self.remove(child)

        library = Library()
        self._load_by_chunks(library.get_episodes(podcast))

    def _load_by_chunks(self, episodes):
        """
        Load episodes by chunks of size CHUNK_SIZE to prevent rendering delay

        Parameters
        ----------
        episodes : Iterable[podcasts.library.Episode]
            The episodes which will be displayed
        """
        finished = False

        for i in range(0, CHUNK_SIZE):
            try:
                episode = next(episodes)
            except StopIteration:
                finished = True
                break
            else:
                self.add(EpisodeRow(episode))

        self.show_all()

        if not finished:
            # Load the rest of the episodes in a future iteration of the main
            # loop (after this chunk has been rendered).
            GLib.idle_add(self._load_by_chunks, episodes)

    def sort_func(self, row1, row2, asc):
        """
        Compare two rows to determine which should be first. Sort them
        by date.

        Parameters
        ----------
        row1 : Gtk.ListBoxRow
            The first row
        row2 : Gtk.ListBoxRow
            The second row
        asc : int
            1 to sort by ascending dates
            -1 to sort by descending dates

        Returns
        -------
        int
            -1 if row1 should be before row2,
            0 if they are equal,
            1 otherwise
        """
        if row1.episode.pubdate < row2.episode.pubdate:
            return -1*asc
        elif row1.episode.pubdate == row2.episode.pubdate:
            return 0
        else:
            return 1*asc


class EpisodeRow(Gtk.ListBoxRow):
    """
    Row in the list of episodes
    """
    def __init__(self, episode):
        Gtk.ListBoxRow.__init__(self)

        self.episode = episode

        grid = Gtk.Grid()
        grid.set_column_spacing(5)
        grid.set_tooltip_text(self.episode.subtitle)
        self.add(grid)

        # Episode status
        if self.episode.new:
            image = Gtk.Image.new_from_icon_name("starred-symbolic",
                                                 Gtk.IconSize.BUTTON)
        else:
            image = Gtk.Image.new_from_icon_name("unstarred-symbolic",
                                                 Gtk.IconSize.BUTTON)
        image.set_margin_start(7)
        image.set_margin_end(7)
        grid.attach(image, 0, 0, 1, 1)

        topgrid = Gtk.Grid()
        grid.attach(topgrid, 1, 0, 1, 1)

        bottomgrid = Gtk.Grid()
        grid.attach(bottomgrid, 1, 1, 1, 1)

        # Title label
        label = Label(sensitive=not self.episode.played)
        label.set_hexpand(True)
        label.set_margin_top(3)
        label.set_markup("<b>{}</b>".format(
            GLib.markup_escape_text(self.episode.title)))
        topgrid.attach(label, 0, 0, 1, 1)

        # Date label
        label = Label(sensitive=not self.episode.played)
        label.set_hexpand(True)
        label.set_text("{:%d/%m/%Y}".format(self.episode.pubdate))
        topgrid.attach(label, 0, 1, 1, 1)

        # Download button
        button = Gtk.Button.new_from_icon_name("document-save-symbolic",
                                               Gtk.IconSize.BUTTON)
        button.set_relief(Gtk.ReliefStyle.NONE)
        topgrid.attach(button, 1, 0, 1, 2)

        # Play button
        button = Gtk.Button.new_from_icon_name("media-playback-start-symbolic",
                                               Gtk.IconSize.BUTTON)
        button.set_relief(Gtk.ReliefStyle.NONE)
        topgrid.attach(button, 2, 0, 1, 2)

        # Subtitle label
        label = Label(sensitive=not self.episode.played, lines=SUBTITLE_LINES)
        label.set_margin_top(7)
        label.set_margin_bottom(7)
        label.set_text(self.episode.subtitle.split("\n")[0])
        bottomgrid.attach(label, 0, 0, 2, 1)

        # Duration label
        if self.episode.duration:
            label = Label(sensitive=not self.episode.played)
            label.set_text(format_duration(self.episode.duration))
            bottomgrid.attach(label, 0, 1, 1, 1)

        # Playback progress
        if self.episode.duration and self.episode.progress > 0:
            progress = Gtk.ProgressBar()
            progress.set_hexpand(True)
            progress.set_valign(Gtk.Align.CENTER)
            progress.set_margin_start(20)
            progress.set_margin_end(20)
            progress.set_fraction(self.episode.progress/self.episode.duration)
            bottomgrid.attach(progress, 1, 1, 1, 1)

        # Separator
        separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(5)
        grid.attach(separator, 0, 2, 2, 1)
