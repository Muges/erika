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
List of episodes
"""

from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Gst
from gi.repository import Gio

from erika.library.models import database, Episode, EpisodeAction
from erika.util import format_duration
from .widgets import Label, IndexedListBox, FilterButton, SortButton
from .player import Player
from .util import cb

SUBTITLE_LINES = 4
CHUNK_SIZE = 10


class EpisodeList(Gtk.VBox):
    """List of episodes

    Signals
    -------
    episodes-changed
        Emitted when episodes are modified (e.g. marked as played)
    download(Episode)
        Emitted when the download button of an episode is clicked
    """

    __gsignals__ = {
        'episodes-changed':
            (GObject.SIGNAL_RUN_FIRST, None, ()),
        'download':
            (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
        'episode-selected':
            (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
        'podcast-selected':
            (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
    }

    def __init__(self, player):
        Gtk.VBox.__init__(self)

        self.current_podcast = None
        self.update_id = None

        self.player = player

        # Episode list
        self.listbox = IndexedListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        self.listbox.set_sort_func(self.sort_func)
        self.listbox.set_filter_func(self.filter_func)
        self.listbox.connect("popup-menu", self._on_popup_menu)
        self.listbox.connect("selected-rows-changed",
                             self._on_selected_rows_changed)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add_with_viewport(self.listbox)

        # Filter and sort buttons
        action_bar = Gtk.ActionBar()

        filter_new = FilterButton("feed-article-unread-symbolic",
                                  "new episodes",
                                  lambda episode: episode.new)
        filter_new.connect("toggled", cb(self.listbox.invalidate_filter))

        filter_played = FilterButton("media-playback-start-symbolic",
                                     "played episodes",
                                     lambda episode: episode.played)
        filter_played.connect("toggled", cb(self.listbox.invalidate_filter))

        filter_downloaded = FilterButton("document-save-symbolic",
                                         "downloaded episodes",
                                         lambda episode: episode.downloaded)
        filter_downloaded.connect("toggled",
                                  cb(self.listbox.invalidate_filter))

        self.filters = [filter_new, filter_played, filter_downloaded]

        self.sort = SortButton("publication date")
        self.sort.connect("clicked", cb(self.listbox.invalidate_sort))

        # Layout
        action_bar.pack_start(filter_new)
        action_bar.pack_start(filter_played)
        action_bar.pack_start(filter_downloaded)
        action_bar.pack_end(self.sort)

        self.pack_start(action_bar, False, False, 0)
        self.pack_start(scrolled_window, True, True, 0)

        self.application = Gio.Application.get_default()
        self.application.connect('network-state-changed',
                                 cb(self.set_network_state))

    def select(self, podcast):
        """Display the episodes of a podcast

        Parameters
        ----------
        podcast : Podcast
            The podcast whose episodes will be displayed
        """
        self.current_podcast = podcast

        # Remove children
        self.listbox.clear()

        self.update()

    def update(self):
        """Update the list of episodes of the current podcast"""
        if self.current_podcast:
            # Interrupt the previous update
            if self.update_id:
                GLib.source_remove(self.update_id)

            episodes = self.current_podcast.episodes

            order_clauses = []

            # Put the results that are not shown at the end (so that
            # they can be shown if the user changes the filter, but do
            # not delay the display of the ones that are currently
            # visible)
            for filter_button in self.filters:
                if filter_button.state is True:
                    order_clauses.append(filter_button.key(Episode).desc())
                elif filter_button.state is False:
                    order_clauses.append(filter_button.key(Episode).asc())

            # Sort by date
            if self.sort.get_descending():
                order_clauses.append(Episode.pubdate.desc())
            else:
                order_clauses.append(Episode.pubdate.asc())

            episodes = episodes.order_by(*order_clauses)

            self._load_by_chunks(iter(episodes), self.listbox.get_ids())

    def update_episode(self, episode):
        """Update an episode

        Parameters
        ----------
        episode : Episode
        """
        try:
            row = self.listbox.get_row(episode.id)
        except ValueError:
            pass
        else:
            row.episode = episode
            row.update()

    def _load_by_chunks(self, episodes, remove_ids):
        """Load episodes by chunks of size CHUNK_SIZE to prevent rendering
        delay

        Parameters
        ----------
        episodes : Iterable[Episode]
            The episodes which will be displayed
        remove_ids : Set
            Set of ids that were in the list but have not been updated yet
            (these should be removed of the list at the end)

        """
        for _ in range(0, CHUNK_SIZE):
            try:
                episode = next(episodes)
            except StopIteration:
                # Remove the episodes that are not in the database anymore
                for episode_id in remove_ids:
                    self.listbox.remove_id(episode_id)

                self.update_id = None
                return
            else:
                try:
                    row = self.listbox.get_row(episode.id)
                except ValueError:
                    # The row does not exist, create it
                    row = EpisodeRow(episode)
                    row.connect("toggle", self._toggle)
                    row.connect("download", self._download)
                    row.set_online(self.application.get_online())

                    if episode == self.player.episode:
                        # The episode is currently being played
                        row.set_progress(self.player.get_seconds_position(),
                                         self.player.get_seconds_duration())
                        row.set_player_state(self.player.state)

                    self.listbox.add_with_id(row, episode.id)
                else:
                    # The row already exists, update it
                    remove_ids.remove(episode.id)
                    row.episode = episode
                    row.update()

        # Load the rest of the episodes in a future iteration of the main
        # loop (after this chunk has been rendered).
        self.update_id = GLib.idle_add(self._load_by_chunks, episodes,
                                       remove_ids)

    def sort_func(self, row1, row2):
        """Compare two rows to determine which should be first. Sort them
        by date

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
        if self.sort.get_descending():
            delta = 1
        else:
            delta = -1

        if row1.episode.pubdate < row2.episode.pubdate:
            return delta
        elif row1.episode.pubdate == row2.episode.pubdate:
            return 0
        else:
            return -delta

    def filter_func(self, row):
        """Check if a row should be visible or not

        Parameters
        ----------
        row : Gtk.ListBoxRow
            The row

        Returns
        -------
        bool
            True if the row should be visible.
        """
        for filter_button in self.filters:
            state = filter_button.state
            if state is not None and filter_button.key(row.episode) != state:
                return False

        return True

    def _on_popup_menu(self, listbox):
        """Display the context menu"""
        selection = self.listbox.get_selected_rows()

        if selection == []:
            return

        menu = Gtk.Menu()

        if any(not row.episode.local_path for row in selection):
            menu_item = Gtk.MenuItem("Download")
            menu_item.connect("activate", cb(self._download_selection),
                              selection)
            menu.append(menu_item)

            menu_item = Gtk.MenuItem("Import file")
            menu_item.connect("activate", cb(self._import_file),
                              selection)
            menu.append(menu_item)

        if any(not row.episode.played for row in selection):
            menu_item = Gtk.MenuItem("Mark as played")
            menu_item.connect("activate", cb(self._mark_as_played),
                              selection)
            menu.append(menu_item)

        if any(row.episode.played for row in selection):
            menu_item = Gtk.MenuItem("Mark as unplayed")
            menu_item.connect("activate", cb(self._mark_as_unplayed),
                              selection)
            menu.append(menu_item)

        if any(row.episode.progress > 0 for row in selection):
            menu_item = Gtk.MenuItem("Reset progress")
            menu_item.connect("activate", cb(self._reset_progress),
                              selection)
            menu.append(menu_item)

        menu.show_all()
        menu.popup(None, None, None, None, 0, Gtk.get_current_event_time())

    def _mark_as_played(self, rows):
        """Mark selected rows as unplayed

        Parameters
        ----------
        rows : List[EpisodeRow]
            The selected rows
        """
        with database.transaction():
            for row in rows:
                row.episode.mark_as_played()
                row.update()
                row.episode.save()

                action = EpisodeAction(episode=row.episode, action="play",
                                       started=row.episode.duration,
                                       position=row.episode.duration,
                                       total=row.episode.duration)
                action.save()

        self.emit("episodes-changed")

    def _mark_as_unplayed(self, rows):
        """Mark selected rows as unplayed

        Parameters
        ----------
        rows : List[EpisodeRow]
            The selected rows
        """
        with database.transaction():
            for row in rows:
                row.episode.mark_as_unplayed()
                row.update()
                row.episode.save()

                action = EpisodeAction(episode=row.episode, action="new")
                action.save()

        self.emit("episodes-changed")

    def _reset_progress(self, rows):
        """Reset the progresses of the selected rows

        Parameters
        ----------
        rows : List[EpisodeRow]
            The selected rows
        """
        with database.transaction():
            for row in rows:
                row.episode.progress = 0
                row.update()
                row.episode.save()

                action = EpisodeAction(episode=row.episode, action="play",
                                       started=0, position=0,
                                       total=row.episode.duration)
                action.save()

        self.emit("episodes-changed")

    def _toggle(self, row):
        """Called when the toggle button of an episode is clicked"""
        if self.player.episode == row.episode:
            self.player.toggle()
        else:
            self.player.play_episode(row.episode)

    def _download(self, row):
        """Called when the download button of an episode is clicked"""
        self.emit("download", row.episode)

    def _download_selection(self, rows):
        """Download the episodes of the selected rows

        Parameters
        ----------
        rows : List[EpisodeRow]
            The selected rows
        """
        for row in rows:
            if row.episode.local_path is None:
                self.emit("download", row.episode)

    def _import_file(self, rows):
        """Import files for the episodes of the selected rows

        Parameters
        ----------
        rows : List[EpisodeRow]
            The selected rows
        """
        # Get parent window
        window = self.get_toplevel()

        for row in rows:
            if row.episode.local_path is None:
                dialog = Gtk.FileChooserDialog(
                    '"{}" file selection'.format(row.episode.title),
                    window, Gtk.FileChooserAction.OPEN,
                    (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                     Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
                dialog.set_current_folder(row.episode.podcast.get_directory())

                response = dialog.run()
                if response == Gtk.ResponseType.OK:
                    path = dialog.get_filename()
                elif response == Gtk.ResponseType.CANCEL:
                    path = None
                dialog.destroy()

                if path:
                    row.episode.local_path = row.episode.import_file(path)
                    row.episode.save()
                    row.update()

                    action = EpisodeAction(episode=row.episode,
                                           action="download")
                    action.save()

    def set_player_progress(self, position, duration):
        """Called when the progress of the playback changes. Updates the
        row of the episode being played"""
        try:
            row = self.listbox.get_row(self.player.episode.id)
        except ValueError:
            pass
        else:
            row.set_progress(position // Gst.SECOND, duration // Gst.SECOND)

    def set_player_state(self, episode, state):
        """Called when the state of the player changes. Updates the
        row of the episode being played"""
        try:
            row = self.listbox.get_row(episode.id)
        except ValueError:
            pass
        else:
            row.set_player_state(state)

    def set_network_state(self, online, _):
        """Called when the network state changes"""
        for row in self.listbox.rows.values():
            row.set_online(online)

    def _on_selected_rows_changed(self, listbox):
        rows = self.listbox.get_selected_rows()
        if len(rows) == 1:
            self.emit("episode-selected", rows[0].episode)
        else:
            self.emit("podcast-selected", self.current_podcast)


class EpisodeRow(Gtk.ListBoxRow):
    # pylint: disable=too-many-instance-attributes
    """Row in the list of episodes

    Signals
    -------
    toggle
        Emitted when the toggle button is clicked
    download
        Emitted when the download button is clicked
    """

    __gsignals__ = {
        'toggle': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'download': (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    def __init__(self, episode):
        Gtk.ListBoxRow.__init__(self)

        self.episode = episode

        grid = Gtk.Grid()
        grid.set_column_spacing(5)
        self.add(grid)

        # Episode status
        self.icon = Gtk.Image()
        self.icon.set_margin_start(7)
        self.icon.set_margin_end(7)
        grid.attach(self.icon, 0, 0, 1, 1)

        topgrid = Gtk.Grid()
        grid.attach(topgrid, 1, 0, 1, 1)

        bottomgrid = Gtk.Grid()
        grid.attach(bottomgrid, 1, 1, 1, 1)

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
        self.download_button = Gtk.Button.new_from_icon_name(
            "document-save-symbolic", Gtk.IconSize.BUTTON)
        self.download_button.set_tooltip_text("Download the episode")
        self.download_button.set_relief(Gtk.ReliefStyle.NONE)
        self.download_button.connect('clicked', cb(self.emit), "download")
        topgrid.attach(self.download_button, 1, 0, 1, 2)

        # Play button
        self.toggle_button = Gtk.Button()
        self.toggle_button.set_relief(Gtk.ReliefStyle.NONE)
        self.toggle_button.connect('clicked', cb(self.emit), "toggle")
        topgrid.attach(self.toggle_button, 2, 0, 1, 2)

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
        grid.attach(separator, 0, 2, 2, 1)

        self.show_all()

        self.update()

    def update(self):
        """Update the widget"""
        # Episode status
        if self.episode.new:
            self.icon.set_from_icon_name("feed-article-unread",
                                         Gtk.IconSize.BUTTON)
            self.icon.set_tooltip_text("New episode")
        else:
            self.icon.set_from_icon_name("feed-article-read",
                                         Gtk.IconSize.BUTTON)
            self.icon.set_tooltip_text("Old episode")

        # Episode title
        self.title.set_sensitive(not self.episode.played)
        self.title.set_markup("<b>{}</b>".format(
            GLib.markup_escape_text(self.episode.title)))

        # Publication date
        self.date.set_sensitive(not self.episode.played)
        self.date.set_text("{:%d/%m/%Y}".format(self.episode.pubdate))

        # Episode subtitle
        self.subtitle.set_sensitive(not self.episode.played)
        self.subtitle.set_text(self.episode.subtitle)

        # Episode duration
        self.duration.set_sensitive(not self.episode.played)

        self.set_progress(self.episode.progress, self.episode.duration)
        self.set_player_state(Player.STOPPED)

        # Download button
        self.download_button.set_visible(not self.episode.local_path)

    def set_progress(self, position, duration):
        """Set the progress of the playback of the episode"""
        # Episode duration
        if duration:
            self.duration.set_text(format_duration(duration))
            self.duration.show()
        else:
            self.duration.hide()

        # Playback progress
        if duration and position > 0:
            self.progress.show()
            self.progress.set_fraction(position / duration)
        else:
            self.progress.hide()

    def set_player_state(self, state):
        """Set the state of the player for this episode"""
        if state == Player.PLAYING or state == Player.BUFFERING:
            self.toggle_button.set_image(
                Gtk.Image.new_from_icon_name("media-playback-pause-symbolic",
                                             Gtk.IconSize.BUTTON))
            self.toggle_button.set_tooltip_text("Pause the episode")
        else:
            self.toggle_button.set_image(
                Gtk.Image.new_from_icon_name("media-playback-start-symbolic",
                                             Gtk.IconSize.BUTTON))
            self.toggle_button.set_tooltip_text("Play the episode")

    def set_online(self, online):
        """Called when the network state changes"""
        self.download_button.set_sensitive(online)
        self.toggle_button.set_sensitive(online or self.episode.downloaded)
