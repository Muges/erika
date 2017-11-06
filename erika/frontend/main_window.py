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
Main window of the application
"""

from gi.repository import Gtk

from erika.__version__ import __appname__
from erika.library.models import Episode
from .details import Details
from .downloads import DownloadsButton
from .episode_list import EpisodeList
from .player import Player
from .player_widgets import PlayerTitle, PlayerControls
from .podcast_list import PodcastList
from .util import cb, get_builder
from .widgets import StatusBox, NetworkButton, Paned


class MainWindow(Gtk.ApplicationWindow):
    """
    Main window of the application
    """
    def __init__(self, application):
        Gtk.ApplicationWindow.__init__(self, application=application,
                                       title=__appname__)
        self.set_default_size(800, 600)
        self.connect("destroy", self._on_close)

        # Header bar
        menu_button = Gtk.MenuButton()
        menu_button.set_image(Gtk.Image.new_from_icon_name(
            "open-menu-symbolic", Gtk.IconSize.BUTTON))

        builder = get_builder('data/menu.glade')
        menu_button.set_menu_model(builder.get_object("app-menu"))

        self.downloads_button = DownloadsButton()
        self.downloads_button.connect("episode-updated",
                                      self._on_episode_updated)

        # Player
        self.player = Player()
        player_title = PlayerTitle(self.player)
        player_controls = PlayerControls(self.player)

        self.player.connect("episode-updated", self._on_episode_updated)
        self.player.connect('progress-changed', cb(player_title.set_progress))
        self.player.connect('state-changed',
                            cb(player_controls.set_player_state, 2))
        self.player.connect('state-changed',
                            cb(player_title.set_player_state))

        # Error bar
        self.error_bar = Gtk.InfoBar()
        self.error_bar.set_no_show_all(True)
        self.error_bar.set_message_type(Gtk.MessageType.ERROR)
        self.error_bar.set_show_close_button(True)
        self.error_bar.connect('response', cb(self.error_bar.hide, 2))

        self.error_label = Gtk.Label()
        self.error_label.show()
        self.error_bar.get_content_area().add(self.error_label)

        # Views
        self.details = Details()

        self.podcast_list = PodcastList()
        self.episode_list = EpisodeList(self.player)

        self.podcast_list.connect('podcast-selected',
                                  cb(self.episode_list.select))
        self.podcast_list.connect('podcast-selected',
                                  cb(self.details.show_podcast))

        self.episode_list.connect('episodes-changed',
                                  self._on_episodes_changed)
        self.episode_list.connect('download',
                                  cb(self.downloads_button.download))
        self.episode_list.connect('episode-selected',
                                  cb(self.details.show_episode))
        self.episode_list.connect('podcast-selected',
                                  cb(self.details.show_podcast))

        self.player.connect('progress-changed',
                            cb(self.episode_list.set_player_progress))
        self.player.connect('state-changed',
                            cb(self.episode_list.set_player_state))

        # Header bar
        headerbar = Gtk.HeaderBar()
        headerbar.set_custom_title(player_title)
        headerbar.set_show_close_button(True)
        headerbar.pack_start(menu_button)
        headerbar.pack_start(player_controls)
        headerbar.pack_end(self.downloads_button)
        headerbar.props.title = __appname__
        self.set_titlebar(headerbar)

        # Statusbar
        self.counts = Gtk.Label()
        self.statusbox = StatusBox()

        self._build_layout()

        self.update_counts()
        self.podcast_list.update()

    def _build_layout(self):
        vbox = Gtk.VBox()
        self.add(vbox)

        vbox.pack_start(self.error_bar, False, False, 0)

        right_paned = Paned()
        right_paned.set_limit_width(700)
        right_paned.set_position(800)
        right_paned.add1(self.episode_list)
        right_paned.add2(self.details)

        paned = Gtk.Paned()
        paned.set_position(300)
        vbox.pack_start(paned, True, True, 0)

        paned.add1(self.podcast_list)
        paned.add2(right_paned)

        # Status bar
        status_bar = Gtk.HBox()
        status_bar.set_margin_top(5)
        status_bar.set_margin_bottom(5)
        status_bar.set_margin_start(5)
        status_bar.set_margin_end(5)
        vbox.pack_start(status_bar, False, False, 0)

        status_bar.pack_start(NetworkButton(), False, False, 0)
        status_bar.pack_start(self.counts, False, False, 0)
        status_bar.pack_end(self.statusbox, False, False, 0)

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

    def _on_close(self, window):
        """
        Called when the window is closed.
        """
        self.player.stop()
        self.downloads_button.stop()

    def _on_episodes_changed(self, episodes_list):
        """
        Called when episodes are modified (e.g. marked as played) in the
        episodes list.

        Update the current podcast.
        """
        self.podcast_list.update_current()
        self.update_counts()

    def _on_episode_updated(self, widget, episode):
        """
        Called when an episode is updated by a widget
        """
        self.podcast_list.update_podcast(episode.podcast)
        self.episode_list.update_episode(episode)
