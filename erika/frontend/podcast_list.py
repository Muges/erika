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

import locale

from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gio

from erika.library.models import Podcast
from .util import cb
from .widgets import Label, IndexedListBox

IMAGE_SIZE = 64
SUBTITLE_LINES = 2


def sort_func(row1, row2):
    """Compare two rows to determine which should be first. Sort them
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
    if row1.podcast.title is None:
        return 1
    elif row2.podcast.title is None:
        return -1
    else:
        return locale.strcoll(row1.podcast.title, row2.podcast.title)


class PodcastList(Gtk.VBox):
    """
    List of podcasts

    Signals
    -------
    podcast-selected(Podcast)
        Emitted when a podcast is selected
    """

    __gsignals__ = {
        'podcast-selected':
            (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
    }

    def __init__(self):
        super().__init__()

        # Podcast list
        self.list = IndexedListBox()
        self.list.set_selection_mode(Gtk.SelectionMode.BROWSE)
        self.list.set_sort_func(sort_func)
        self.list.connect("row-selected", self._on_row_selected)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add_with_viewport(self.list)

        # Action bar
        self.action_bar = Gtk.ActionBar()

        self.add_podcast = Gtk.Button.new_from_icon_name(
            "list-add-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        self.add_podcast.set_tooltip_text("Add a podcast")
        self.add_podcast.set_action_name("app.add-podcast")
        self.action_bar.pack_start(self.add_podcast)

        remove_podcast = Gtk.Button.new_from_icon_name(
            "list-remove-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        remove_podcast.set_tooltip_text("Remove the selected podcast")
        remove_podcast.connect("clicked", self._on_remove_podcast)
        self.action_bar.pack_start(remove_podcast)

        import_opml = Gtk.Button.new_from_icon_name(
            "document-open-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        import_opml.set_action_name("app.import-opml")
        import_opml.set_tooltip_text("Import an opml file")
        self.action_bar.pack_end(import_opml)

        export_opml = Gtk.Button.new_from_icon_name(
            "document-save-as-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        export_opml.set_action_name("app.export-opml")
        export_opml.set_tooltip_text("Export subscriptions to an opml file")
        self.action_bar.pack_end(export_opml)

        # Layout
        self.pack_start(scrolled_window, True, True, 0)
        self.pack_start(self.action_bar, False, False, 0)

        application = Gio.Application.get_default()
        application.connect('network-state-changed',
                            cb(self.set_network_state))

    def update(self):
        """Update the list of podcasts"""
        # Set of ids that should be removed
        remove_ids = self.list.get_ids()

        for podcast in Podcast.select():
            try:
                row = self.list.get_row(podcast.id)
            except ValueError:
                # The row does not exist, create it
                row = PodcastRow(podcast)
                self.list.add_with_id(row, podcast.id)
            else:
                # The row already exists, update it
                remove_ids.remove(podcast.id)
                row.podcast = podcast
                row.update()

        # Remove the podcasts that are not in the database anymore
        for podcast_id in remove_ids:
            self.list.remove_id(podcast_id)

        if self.list.get_selected_row() is None:
            self.list.select_row(self.list.get_row_at_index(0))

        self.list.invalidate_sort()

    def update_podcast(self, podcast):
        """Update a podcast

        Parameters
        ----------
        podcast_id : int
            The id of the podcast
        """
        try:
            row = self.list.get_row(podcast.id)
        except ValueError:
            # The row does not exist, create it
            row = PodcastRow(podcast)
            self.list.add_with_id(row, podcast.id)
        else:
            row.podcast = podcast
            row.update()

    def update_current(self):
        """Update the selected row"""
        row = self.list.get_selected_row()

        if row:
            row.update()

    def _on_row_selected(self, listbox, row):
        """Called when a row is selected.

        Emit the podcast-selected signal.
        """
        if row:
            self.emit('podcast-selected', row.podcast)

    def _on_remove_podcast(self, button):
        selection = self.list.get_selected_row()

        if selection is None:
            return

        # Get parent window
        window = self.get_toplevel()

        # Ask for confirmation
        dialog = Gtk.MessageDialog(window, 0, Gtk.MessageType.QUESTION,
                                   Gtk.ButtonsType.YES_NO)
        dialog.set_markup(
            "Are you sure you want to remove the podcast <b>{}</b>?".format(
                GLib.markup_escape_text(selection.podcast.display_title)))
        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.NO:
            return

        # Delete the podcast
        selection.podcast.delete_instance(recursive=True)
        selection.destroy()

        # Select the first row
        first_row = self.list.get_row_at_index(0)
        self.list.select_row(first_row)

    def set_network_state(self, online, _):
        """Called when the network state is changed"""
        self.add_podcast.set_sensitive(online)


class PodcastRow(Gtk.ListBoxRow):
    """Row in the list of podcasts"""
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
        self.grid.attach(self.counts, 2, 0, 2, 1)

        # Podcast subtitle
        self.subtitle = Label(lines=SUBTITLE_LINES)
        self.grid.attach(self.subtitle, 1, 1, 3, 1)

        self.error_icon = Gtk.Image.new_from_icon_name(
            'gtk-dialog-error', Gtk.IconSize.BUTTON)
        self.error_icon.set_tooltip_text(
            'The last update of this podcast failed.')

        self.update()

    def update(self):
        """Update the widget"""
        self.grid.set_tooltip_markup((
            "<b>{title}</b>\n"
            "{episodes} episodes"
        ).format(
            title=GLib.markup_escape_text(self.podcast.display_title),
            episodes=self.podcast.episodes_count
        ))

        # Podcast Image
        self.icon.set_from_pixbuf(self.podcast.image.as_pixbuf(IMAGE_SIZE))

        # Podcast title
        self.title.set_markup("<b>{}</b>".format(
            GLib.markup_escape_text(self.podcast.display_title)))

        # Unplayed and new counts
        if self.podcast.unplayed_count > 0:
            unplayed = str(self.podcast.unplayed_count)
        else:
            unplayed = ""

        if self.podcast.new_count > 0:
            new = "<b>({})</b>".format(self.podcast.new_count)
        else:
            new = ""

        if unplayed and new:
            self.counts.set_markup(unplayed + " " + new)
        else:
            self.counts.set_markup(unplayed + " " + new)

        # Update layout if there was an error
        self.grid.remove(self.counts)
        self.grid.remove(self.error_icon)
        if self.podcast.update_failed:
            self.grid.attach(self.counts, 2, 0, 1, 1)
            self.grid.attach(self.error_icon, 3, 0, 1, 1)
        else:
            self.grid.attach(self.counts, 2, 0, 2, 1)

        # Podcast subtitle (only the first line)
        self.subtitle.set_text(
            self.podcast.display_subtitle.split('\n')[0])

        self.show_all()
