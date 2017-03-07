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
#from podcasts.frontend.downloads import DownloadsButton
#from podcasts.frontend.podcast_list import PodcastList
#from podcasts.frontend.episode_list import EpisodeList
#from podcasts.frontend.player import Player
#from podcasts.frontend.player_widgets import PlayerWidgets
#from podcasts.frontend.details import Details
from podcasts.frontend.widgets import StatusBox, NetworkButton, Paned
from podcasts.library.models import Episode
from podcasts.util import cb


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

        #self.downloads_button = DownloadsButton()
        #self.downloads_button.connect("episode-updated",
        #                              self._on_episode_updated)

        # Player
        #self.player = Player()
        #self.player.connect("episode-updated", self._on_episode_updated)

        #self.player_widgets = PlayerWidgets(self.player)

        #self.player.connect('progress-changed', cb(self.player_widgets.set_progress))
        #self.player.connect('state-changed', cb(self.player_widgets.set_state))

        # Views
        #self.details = Details()

        #self.podcast_list = PodcastList()
        #self.podcast_list.connect('podcast-selected', self._on_podcast_selected)
        #self.podcast_list.connect('podcast-selected', cb(self.details.show_podcast))

        #self.episode_list = EpisodeList(self.player)
        #self.episode_list.connect('episodes-changed',
        #                          self._on_episodes_changed)
        #self.episode_list.connect('download', self._on_episode_download)
        #self.episode_list.connect('episode-selected', cb(self.details.show_episode))
        #self.episode_list.connect('podcast-selected', cb(self.details.show_podcast))

        #self.player.connect('progress-changed', cb(self.episode_list.set_player_progress))
        #self.player.connect('state-changed', cb(self.episode_list.set_player_state))

        # Statusbar
        self.network_button = NetworkButton()

        self.counts = Gtk.Label()
        self.update_counts()

        self.statusbox = StatusBox()

        # Layout
        vbox = Gtk.VBox()
        self.add(vbox)

        headerbar = Gtk.HeaderBar()
        #headerbar.set_custom_title(self.player_widgets.title)
        headerbar.set_show_close_button(True)
        headerbar.pack_start(self.menu_button)
        #headerbar.pack_start(self.player_widgets.controls)
        #headerbar.pack_end(self.downloads_button)
        self.set_titlebar(headerbar)

        right_paned = Paned()
        right_paned.set_limit_width(700)
        right_paned.set_position(800)
        #right_paned.add1(self.episode_list)
        #right_paned.add2(self.details)

        paned = Gtk.Paned()
        paned.set_position(300)
        vbox.pack_start(paned, True, True, 0)

        #paned.add1(self.podcast_list)
        paned.add2(right_paned)

        status_bar = Gtk.HBox()
        status_bar.set_margin_top(5)
        status_bar.set_margin_bottom(5)
        status_bar.set_margin_start(5)
        status_bar.set_margin_end(5)
        vbox.pack_start(status_bar, False, False, 0)

        status_bar.pack_start(self.network_button, False, False, 0)
        status_bar.pack_start(self.counts, False, False, 0)
        status_bar.pack_end(self.statusbox, False, False, 0)

        #self.podcast_list.update()

    def update_counts(self):
        """
        Update counts label
        """
        new, played, total = Episode.get_counts()
        unplayed = total - played
        self.counts.set_text("{} new episodes, {} unplayed".format(
            new,
            unplayed
        ))

    def _on_close(self, window, event):
        """
        Called when the window is closed.
        """
        #self.player.stop()
        #self.downloads_button.stop()

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

    def _on_episode_updated(self, widget, episode):
        """
        Called when an episode is updated by a widget
        """
        self.podcast_list.update_podcast(episode.podcast_id)
        self.episode_list.update_episode(episode)
