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
        headerbar.set_show_close_button(True)
        headerbar.pack_start(self.menu_button)
        headerbar.pack_start(self.player.widgets.controls)
        headerbar.pack_end(self.downloads_button)
        vbox.pack_start(headerbar, False, False, 0)

        paned = Gtk.Paned()
        paned.set_position(300)
        vbox.pack_start(paned, True, True, 0)

        paned.add1(self.podcast_list)
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
