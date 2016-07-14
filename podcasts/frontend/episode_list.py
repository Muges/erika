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
# TODO : icons fallback

"""
List of episodes
"""

from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gtk

from podcasts.library import Library
from podcasts.util import format_duration
from .widgets import Label, IndexedListBox

SUBTITLE_LINES = 4
CHUNK_SIZE = 10


class EpisodeList(IndexedListBox):
    """
    List of episodes

    Signals
    -------
    episodes-changed
        Emitted when episodes are modified (e.g. marked as played)
    play(Episode)
        Emitted when the play button of an episode is clicked
    download(Episode)
        Emitted when the download button of an episode is clicked
    """

    __gsignals__ = {
        'episodes-changed':
            (GObject.SIGNAL_RUN_FIRST, None, ()),
        'play':
            (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
        'download':
            (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
    }

    def __init__(self):
        IndexedListBox.__init__(self)
        self.current_podcast = None

        self.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        self.set_sort_func(self.sort_func, -1)
        self.connect("popup-menu", EpisodeList._on_popup_menu)

    def select(self, podcast):
        """
        Display the episodes of a podcast.

        Parameters
        ----------
        podcast : podcasts.library.Podcast
            The podcast whose episodes will be displayed
        """
        self.current_podcast = podcast

        # Remove children
        self.clear()

        library = Library()
        self._load_by_chunks(library.get_episodes(podcast), set())

    def update(self):
        """
        Update the list of episodes of the current podcast.
        """
        library = Library()
        self._load_by_chunks(library.get_episodes(self.current_podcast),
                             self.get_ids())

    def update_episode(self, episode):
        """
        Update an episode.

        Parameters
        ----------
        episode : Episode
        """
        try:
            row = self.get_row(episode.id)
        except ValueError:
            pass
        else:
            row.episode = episode
            row.update()

    def _load_by_chunks(self, episodes, remove_ids):
        """
        Load episodes by chunks of size CHUNK_SIZE to prevent rendering delay

        Parameters
        ----------
        episodes : Iterable[podcasts.library.Episode]
            The episodes which will be displayed
        remove_ids : Set
            Set of ids that were in the list but have not been updated yet
            (these should be removed of the list at the end)
        """
        for i in range(0, CHUNK_SIZE):
            try:
                episode = next(episodes)
            except StopIteration:
                # Remove the episodes that are not in the database anymore
                for episode_id in remove_ids:
                    self.remove_id(episode_id)

                return
            else:
                try:
                    row = self.get_row(episode.id)
                except ValueError:
                    # The row does not exist, create it
                    row = EpisodeRow(episode)
                    row.connect("play", self._play)
                    row.connect("download", self._download)
                    self.add_with_id(row, episode.id)
                else:
                    # The row already exists, update it
                    remove_ids.remove(episode.id)
                    row.episode = episode
                    row.update()

        # Load the rest of the episodes in a future iteration of the main
        # loop (after this chunk has been rendered).
        GLib.idle_add(self._load_by_chunks, episodes, remove_ids)

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

    def _on_popup_menu(self):
        """
        Display the context menu
        """
        selection = self.get_selected_rows()

        if selection == []:
            return

        menu = Gtk.Menu()

        if any(not row.episode.played for row in selection):
            menu_item = Gtk.MenuItem("Mark as played")
            menu_item.connect("activate", self._mark_as_played, selection)
            menu.append(menu_item)

        if any(row.episode.played for row in selection):
            menu_item = Gtk.MenuItem("Mark as unplayed")
            menu_item.connect("activate", self._mark_as_unplayed, selection)
            menu.append(menu_item)

        if any(row.episode.progress > 0 for row in selection):
            menu_item = Gtk.MenuItem("Reset progress")
            menu_item.connect("activate", self._reset_progress, selection)
            menu.append(menu_item)

        menu.show_all()
        menu.popup(None, None, None, None, 0, Gtk.get_current_event_time())

    def _mark_as_played(self, menu_item, rows):
        """
        Mark selected rows as unplayed

        Parameters
        ----------
        menu_item : Gtk.MenuItem
            The menu item that was emitted the signal
        rows : List[EpisodeRow]
            The selected rows
        """
        for row in rows:
            row.episode.mark_as_played()
            row.update()

        library = Library()
        library.commit(row.episode for row in rows)

        self.emit("episodes-changed")

    def _mark_as_unplayed(self, menu_item, rows):
        """
        Mark selected rows as unplayed

        Parameters
        ----------
        menu_item : Gtk.MenuItem
            The menu item that was emitted the signal
        rows : List[EpisodeRow]
            The selected rows
        """
        for row in rows:
            row.episode.mark_as_unplayed()
            row.update()

        library = Library()
        library.commit(row.episode for row in rows)

    def _reset_progress(self, menu_item, rows):
        """
        Reset the progresses of the selected rows

        Parameters
        ----------
        menu_item : Gtk.MenuItem
            The menu item that was emitted the signal
        rows : List[EpisodeRow]
            The selected rows
        """
        for row in rows:
            row.episode.progress = 0
            row.update()

        library = Library()
        library.commit(row.episode for row in rows)

    def _play(self, row):
        """
        Called when the play button of an episode is clicked
        """
        self.emit("play", row.episode)

    def _download(self, row):
        """
        Called when the download button of an episode is clicked
        """
        self.emit("download", row.episode)


class EpisodeRow(Gtk.ListBoxRow):
    """
    Row in the list of episodes

    Signals
    -------
    play
        Emitted when the play button is clicked
    download
        Emitted when the download button is clicked
    """

    __gsignals__ = {
        'play': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'download': (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    def __init__(self, episode):
        Gtk.ListBoxRow.__init__(self)

        self.episode = episode

        self.grid = Gtk.Grid()
        self.grid.set_column_spacing(5)
        self.add(self.grid)

        # Episode status
        self.icon = Gtk.Image()
        self.icon.set_margin_start(7)
        self.icon.set_margin_end(7)
        self.grid.attach(self.icon, 0, 0, 1, 1)

        topgrid = Gtk.Grid()
        self.grid.attach(topgrid, 1, 0, 1, 1)

        bottomgrid = Gtk.Grid()
        self.grid.attach(bottomgrid, 1, 1, 1, 1)

        # Episode title
        self.title = Label()
        self.title.set_hexpand(True)
        self.title.set_margin_top(3)
        topgrid.attach(self.title, 0, 0, 1, 1)

        # Publication date
        self.date = Label()
        self.date.set_hexpand(True)
        topgrid.attach(self.date, 0, 1, 1, 1)

        # Download button
        button = Gtk.Button.new_from_icon_name("document-save-symbolic",
                                               Gtk.IconSize.BUTTON)
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.connect('clicked', self._on_download_clicked)
        topgrid.attach(button, 1, 0, 1, 2)

        # Play button
        button = Gtk.Button.new_from_icon_name("media-playback-start-symbolic",
                                               Gtk.IconSize.BUTTON)
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.connect('clicked', self._on_play_clicked)
        topgrid.attach(button, 2, 0, 1, 2)

        # Episode subtitle
        self.subtitle = Label(lines=SUBTITLE_LINES)
        self.subtitle.set_margin_top(7)
        self.subtitle.set_margin_bottom(7)
        bottomgrid.attach(self.subtitle, 0, 0, 2, 1)

        # Episode duration
        self.duration = Label()
        bottomgrid.attach(self.duration, 0, 1, 1, 1)

        # Playback progress
        self.progress = Gtk.ProgressBar()
        self.progress.set_hexpand(True)
        self.progress.set_valign(Gtk.Align.CENTER)
        self.progress.set_margin_start(20)
        self.progress.set_margin_end(20)
        bottomgrid.attach(self.progress, 1, 1, 1, 1)

        # Separator
        separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(5)
        self.grid.attach(separator, 0, 2, 2, 1)

        self.show_all()

        self.update()

    def update(self):
        """
        Update the widget
        """
        self.grid.set_tooltip_text(self.episode.subtitle)

        # Episode status
        if self.episode.new:
            self.icon.set_from_icon_name("starred-symbolic",
                                         Gtk.IconSize.BUTTON)
        else:
            self.icon.set_from_icon_name("unstarred-symbolic",
                                         Gtk.IconSize.BUTTON)

        # Episode title
        self.title.set_sensitive(not self.episode.played)
        self.title.set_markup("<b>{}</b>".format(
            GLib.markup_escape_text(self.episode.title)))

        # Publication date
        self.date.set_sensitive(not self.episode.played)
        self.date.set_text("{:%d/%m/%Y}".format(self.episode.pubdate))

        # Episode subtitle
        self.subtitle.set_sensitive(not self.episode.played)
        self.subtitle.set_text(self.episode.subtitle.split("\n")[0])

        # Episode duration
        self.duration.set_sensitive(not self.episode.played)
        if self.episode.duration:
            self.duration.set_text(format_duration(self.episode.duration))
            self.duration.show()
        else:
            self.duration.hide()

        # Playback progress
        if self.episode.duration and self.episode.progress > 0:
            self.progress.show()
            self.progress.set_fraction(
                self.episode.progress/self.episode.duration)
        else:
            self.progress.hide()

    def _on_play_clicked(self, button):
        """
        Called when the play button is clicked
        """
        self.emit("play")

    def _on_download_clicked(self, button):
        """
        Called when the download button is clicked
        """
        self.emit("download")
