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

import threading
from gi.repository import Gio
from gi.repository import GObject
from gi.repository import Gtk

from podcasts.__version__ import __appname__
from podcasts.frontend.downloads import DownloadsButton
from podcasts.frontend.podcast_list import PodcastList
from podcasts.frontend.episode_list import EpisodeList
from podcasts.frontend.player import Player
from podcasts.frontend.widgets import StatusBox
from podcasts.library import Library
from podcasts.opml import import_opml, export_opml

# Library update interval in seconds
UPDATE_INTERVAL = 15*60


class MainWindow(Gtk.ApplicationWindow):
    """
    Main window of the application.
    """
    def __init__(self, application):
        Gtk.ApplicationWindow.__init__(self, application=application,
                                       title=__appname__)
        self.set_default_size(800, 600)
        self.connect("delete-event", self._on_close)

        # Header bar
        self.menu_button = Gtk.MenuButton()
        self.menu_button.set_image(Gtk.Image.new_from_icon_name(
            "open-menu-symbolic", Gtk.IconSize.BUTTON))

        builder = Gtk.Builder.new_from_file("data/menu.ui")
        self.menu_button.set_menu_model(builder.get_object("app-menu"))

        self.downloads_button = DownloadsButton()
        self.downloads_button.connect("episode-updated",
                                      self._on_episode_updated)

        # Player
        self.player = Player()
        self.player.connect("episode-updated", self._on_episode_updated)

        # Views
        self.podcast_list = PodcastList()
        self.podcast_list.connect('podcast-selected',
                                  self._on_podcast_selected)

        self.episode_list = EpisodeList()
        self.episode_list.connect('episodes-changed',
                                  self._on_episodes_changed)
        self.episode_list.connect('play', self._on_episode_play)
        self.episode_list.connect('download', self._on_episode_download)

        # Statusbar
        self.counts = Gtk.Label()
        self.update_counts()

        self.statusbox = StatusBox()

        # Layout
        vbox = Gtk.VBox()
        self.add(vbox)

        headerbar = Gtk.HeaderBar()
        headerbar.set_custom_title(self.player.widgets.title)
        headerbar.pack_start(self.menu_button)
        headerbar.pack_start(self.player.widgets.controls)
        headerbar.pack_end(self.downloads_button)
        vbox.pack_start(headerbar, False, False, 0)

        paned = Gtk.Paned()
        paned.set_position(300)
        vbox.pack_start(paned, True, True, 0)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add_with_viewport(self.podcast_list)
        paned.add1(scrolled_window)

        paned.add2(self.episode_list)

        status_bar = Gtk.HBox()
        status_bar.set_margin_top(5)
        status_bar.set_margin_bottom(5)
        status_bar.set_margin_start(5)
        status_bar.set_margin_end(5)
        vbox.pack_start(status_bar, False, False, 0)

        status_bar.pack_start(self.counts, False, False, 0)
        status_bar.pack_end(self.statusbox, False, False, 0)

        self.show_all()
        self.podcast_list.update()

        # Library update
        self.update_library(scan=True)
        GObject.timeout_add_seconds(UPDATE_INTERVAL, self.update_library)

    def update_counts(self):
        """
        Update counts label
        """
        library = Library()
        new, played, total = library.get_counts()
        unplayed = total - played
        self.counts.set_text("{} new episodes, {} unplayed".format(
            new,
            unplayed
        ))

    def update_library(self, scan=False):
        """
        Update the podcasts library
        """
        message_id = self.statusbox.add("Updating library...")

        def _end():
            self.statusbox.remove(message_id)

            self.podcast_list.update()
            self.episode_list.update()
            self.update_counts()

        def _update():
            # TODO : handle errors
            library = Library()
            library.update_podcasts()
            if scan:
                library.scan()

            GObject.idle_add(_end)

        thread = threading.Thread(target=_update)
        thread.start()

    def add_podcast(self):
        """
        Add a new podcast.
        """
        # Open the "Add a podcast" dialog
        builder = Gtk.Builder.new_from_file("data/add_podcast.ui")
        dialog = builder.get_object("add_dialog")
        url_entry = builder.get_object("url_entry")
        dialog.set_transient_for(self)

        response = dialog.run()
        url = url_entry.get_text()
        dialog.destroy()

        if response == Gtk.ResponseType.OK and url:
            message_id = self.statusbox.add("Adding podcast...")

            def _end():
                self.statusbox.remove(message_id)

                self.podcast_list.update()
                self.episode_list.update()
                self.update_counts()

            def _add(url):
                # TODO : handle errors
                library = Library()
                library.add_source("feed", url)

                GObject.idle_add(_end)

            thread = threading.Thread(target=_add, args=(url,))
            thread.start()

    def import_opml(self):
        """
        Import the podcasts subscriptions from an OPML file.
        """
        dialog = Gtk.FileChooserDialog(
            "Import OPML file", self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        # Add filters
        filter_xml = Gtk.FileFilter()
        filter_xml.set_name("XML files")
        filter_xml.add_mime_type("text/xml")
        dialog.add_filter(filter_xml)

        filter_text = Gtk.FileFilter()
        filter_text.set_name("Text files")
        filter_text.add_mime_type("text/plain")
        dialog.add_filter(filter_text)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
        elif response == Gtk.ResponseType.CANCEL:
            filename = None
        dialog.destroy()

        if filename:
            message_id = self.statusbox.add("Importing OPML...")

            def _end():
                self.statusbox.remove(message_id)

                self.podcast_list.update()
                self.episode_list.update()
                self.update_counts()

            def _import(filename):
                # TODO : handle errors
                import_opml(filename)

                GObject.idle_add(_end)

            thread = threading.Thread(target=_import, args=(filename,))
            thread.start()

    def export_opml(self):
        """
        Export the podcasts subscriptions in an OPML file.
        """
        dialog = Gtk.FileChooserDialog(
            "Export OPML file", self,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.OK))

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
        elif response == Gtk.ResponseType.CANCEL:
            filename = None
        dialog.destroy()

        if filename:
            message_id = self.statusbox.add("Exporting OPML...")

            def _end():
                self.statusbox.remove(message_id)

            def _export(filename):
                export_opml(filename)
                GObject.idle_add(_end)

            thread = threading.Thread(target=_export, args=(filename,))
            thread.start()

    def _on_close(self, window, event):
        """
        Called when the window is closed.
        """
        self.player.stop()
        self.downloads_button.stop()

    def _on_podcast_selected(self, podcast_list, podcast):
        """
        Called when a podcast is selected in the podcast list.

        Show the podcast's episodes in the episode list.
        """
        self.episode_list.select(podcast)

    def _on_episodes_changed(self, episodes_list):
        """
        Called when episodes are modified (e.g. marked as played) in the
        episodes list.

        Update the current podcast.
        """
        self.podcast_list.update_current()
        self.update_counts()

    def _on_episode_download(self, episode_list, episode):
        """
        Called when the download button of an episode is clicked
        """
        self.downloads_button.download(episode)

    def _on_episode_play(self, episode_list, episode):
        """
        Called when the play button of an episode is clicked
        """
        self.player.play(episode)

    def _on_episode_updated(self, widget, episode):
        """
        Called when an episode is updated by a widget
        """
        self.podcast_list.update_podcast(episode.podcast_id)
        self.episode_list.update_episode(episode)
