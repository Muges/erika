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

from podcasts.__version__ import __appname__
from podcasts.util import format_duration
from podcasts.frontend.player import Player


class PlayerWidgets(GObject.Object):
    """
    Object handling the playback interface
    """
    def __init__(self, player):
        self.player = player
        self.state = None
        self.seeking = False

        builder = Gtk.Builder()
        builder.add_from_file("data/player.ui")
        builder.connect_signals(self)

        self.controls = builder.get_object("controls")
        self.title = builder.get_object("title")

        self.play = builder.get_object("play")
        self.pause = builder.get_object("pause")

        self.playing = [
            builder.get_object("playing_1"),
            builder.get_object("playing_2")
        ]
        self.progress = builder.get_object("progress")
        self.position = builder.get_object("position")
        self.duration = builder.get_object("duration")

        self.set_state(None, Player.STOPPED)

    def set_state(self, episode, state):
        """
        Set the current state (called by the player)

        Parameters
        ----------
        episode : Episode
            The episode currently being played.
        state : int
        """
        self.state = state

        if episode:
            for playing in self.playing:
                playing.set_markup(
                    "<b>{}</b> from <b><i>{}</i></b>".format(
                        GLib.markup_escape_text(episode.title),
                        GLib.markup_escape_text(episode.podcast.title)))

        if state in [Player.PLAYING, Player.PAUSED]:
            self.pause.set_visible(state == Player.PLAYING)
            self.play.set_visible(state == Player.PAUSED)
            self.controls.show()
            self.title.set_visible_child_name('player')

            self._update_progress()
        elif state == Player.BUFFERING:
            self.controls.hide()
            self.title.set_visible_child_name('loading')
        elif state == Player.STOPPED:
            self.controls.hide()
            self.title.set_visible_child_name('title')
        else:
            raise ValueError("Invalid player state : {}.".format(state))

    def set_progress(self, position, duration):
        self.progress.set_range(0, duration)
        if not self.seeking:
            self.progress.set_value(position)
        self.progress.set_fill_level(self.player.get_buffered())

        self.position.set_text(format_duration(position // Gst.SECOND))
        self.duration.set_text(format_duration(duration // Gst.SECOND))

    def _on_play_clicked(self, button):
        """
        Called when the play button is clicked
        """
        self.player.play()

    def _on_pause_clicked(self, button):
        """
        Called when the pause button is clicked
        """
        self.player.pause()

    def _on_forward_clicked(self, button):
        """
        Called when the forward button is clicked
        """
        self.player.seek_relative(30 * Gst.SECOND)
        self._update_progress()

    def _on_backward_clicked(self, button):
        """
        Called when the backward button is clicked
        """
        self.player.seek_relative(-30 * Gst.SECOND)
        self._update_progress()

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
