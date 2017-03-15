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
Audio player widgets
"""

from gi.repository import GObject
from gi.repository import Gst
from gi.repository import Gtk
from gi.repository import GLib

from erika.__version__ import __appname__
from erika.util import format_duration
from .player import Player
from .util import cb, get_builder


class PlayerTitle(Gtk.Stack):
    """Widget showing either the applications's name or the current
    episode being played and a progressbar"""
    def __init__(self, player):
        super().__init__()
        self.player = player
        self.seeking = False

        builder = get_builder('data/player_title.glade')
        builder.connect_signals(self)

        player = builder.get_object("player")
        loading = builder.get_object("loading")
        title = Gtk.Label()
        title.set_markup("<b>{}</b>".format(__appname__))

        self.add_named(title, "title")
        self.add_named(player, "player")
        self.add_named(loading, "loading")

        self.playing = [
            builder.get_object("playing_1"),
            builder.get_object("playing_2")
        ]
        self.progress = builder.get_object("progress")
        self.position = builder.get_object("position")
        self.duration = builder.get_object("duration")

        self.set_player_state(None, Player.STOPPED)
        # The line above does not seem to be enough for the title to be visible
        GObject.idle_add(self.set_player_state, None, Player.STOPPED)

    def set_player_state(self, episode, state):
        """Called when the state of the player changes

        Parameters
        ----------
        episode : Episode
            The episode currently being played.
        state : int
            The state of the player (Player.BUFFERING, Player.STOPPED,
            Player.PAUSED, or Player.PLAYING)
        """
        if episode:
            for playing in self.playing:
                playing.set_markup(
                    "<b>{}</b> from <b><i>{}</i></b>".format(
                        GLib.markup_escape_text(episode.title),
                        GLib.markup_escape_text(episode.podcast.title)))

        if state in [Player.PLAYING, Player.PAUSED]:
            self._update_progress()
            self.set_visible_child_name('player')
        elif state == Player.BUFFERING:
            self.set_visible_child_name('loading')
        elif state == Player.STOPPED:
            self.set_visible_child_name('title')
        else:
            raise ValueError("Invalid player state : {}.".format(state))

    def set_progress(self, position, duration):
        """Called when the progress of the playback changes"""
        self.progress.set_range(0, duration)
        if not self.seeking:
            self.progress.set_value(position)
        self.progress.set_fill_level(self.player.get_buffered())

        self.position.set_text(format_duration(position // Gst.SECOND))
        self.duration.set_text(format_duration(duration // Gst.SECOND))

    def _on_seeking_start(self, scale, event):
        """
        Called when the user starts seeking
        """
        if event.button == 1:
            self.seeking = True

    def _on_seeking_end(self, scale, event):
        """
        Called when the user ends seeking
        """
        if event.button == 1:
            self.player.seek(self.progress.get_value())
            self.seeking = False

    def _update_progress(self):
        """
        Update the slider
        """
        position = self.player.get_position()
        duration = self.player.get_duration()

        self.set_progress(position, duration)


class PlayerControls(Gtk.Box):
    """Widget containing buttons to control the player"""
    def __init__(self, player):
        super().__init__()
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_no_show_all(True)

        self.player = player

        backward = Gtk.Button.new_from_icon_name(
            "media-seek-backward-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        backward.connect("clicked", cb(self.player.seek_relative),
                         -30 * Gst.SECOND)
        backward.show()

        self.play = Gtk.Button.new_from_icon_name(
            "media-playback-start-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        self.play.connect("clicked", cb(self.player.play))

        self.pause = Gtk.Button.new_from_icon_name(
            "media-playback-pause-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        self.pause.connect("clicked", cb(self.player.pause))

        stop = Gtk.Button.new_from_icon_name(
            "media-playback-stop-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        stop.connect("clicked", cb(self.player.stop))
        stop.show()

        forward = Gtk.Button.new_from_icon_name(
            "media-seek-forward-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        forward.connect("clicked", cb(self.player.seek_relative),
                        30 * Gst.SECOND)
        forward.show()

        self.pack_start(backward, False, True, 0)
        self.pack_start(self.play, False, True, 0)
        self.pack_start(self.pause, False, True, 0)
        self.pack_start(stop, False, True, 0)
        self.pack_start(forward, False, True, 0)

        self.set_player_state(Player.STOPPED)

    def set_player_state(self, state):
        """Called when the state of the player changes

        Parameters
        ----------
        state : int
            The state of the player (Player.BUFFERING, Player.STOPPED,
            Player.PAUSED, or Player.PLAYING)
        """
        if state in [Player.PLAYING, Player.PAUSED]:
            self.pause.set_visible(state == Player.PLAYING)
            self.play.set_visible(state == Player.PAUSED)
            self.show()
        elif state == Player.BUFFERING:
            self.hide()
        elif state == Player.STOPPED:
            self.hide()
        else:
            raise ValueError("Invalid player state : {}.".format(state))
