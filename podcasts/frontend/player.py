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
Module handling the audio playback
"""

# TODO : seeking
# TODO : mark episode as read
# TODO : save progress
# TODO : display progress in episode list
# TODO : display buffering
# TODO : better buffering?

import logging
from types import SimpleNamespace

from gi.repository import GObject
from gi.repository import Gst
from gi.repository import Gtk

from podcasts.library import Library
from podcasts.util import format_position, format_duration


class Player(GObject.Object):
    """
    Object handling the audio playback
    """

    def __init__(self):
        GObject.Object.__init__(self)

        self.logger = logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__))

        self.episode = None
        self.playing = False

        # Create player
        self.player = Gst.ElementFactory.make("playbin")
        bus = self.player.get_bus()
        bus.connect("message", self._on_message)
        self.player.connect("about-to-finish",  self._on_finished)

        # Create widgets
        self.widgets = SimpleNamespace()

        builder = Gtk.Builder()
        builder.add_from_file("data/player.ui")
        builder.connect_signals(self)

        self.widgets.controls = builder.get_object("controls")
        self.widgets.state = builder.get_object("state")

        self.widgets.toggle = builder.get_object("toggle_image")
        self.widgets.progress = builder.get_object("progress")
        self.widgets.position = builder.get_object("position")
        self.widgets.duration = builder.get_object("duration")
        self.widgets.playing = builder.get_object("playing")

    def play(self, episode):
        """
        Start the playback of an episode
        """
        self.episode = episode

        library = Library()
        podcast = library.get_podcast(self.episode)

        self.widgets.playing.set_markup(
            "<b>{}</b> from <b><i>{}</i></b>".format(
                self.episode.title, podcast.title))

        self.player.set_property("uri", episode.file_url)
        self.player.set_state(Gst.State.PLAYING)
        self._set_playing()
        self._update_progress()
        GObject.timeout_add(100, self._update_progress)

    def _on_message(self, bus, message):
        """
        Handle gstreamer bus messages
        """
        if message.type == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)
            self._set_stopped()
        elif message.type == Gst.MessageType.ERROR:
            self.player.set_state(Gst.State.NULL)
            self._set_stopped()

            err, debug = message.parse_error()
            self.logger.error(err.message)
            self.logger.error("Debugging info: %s", err.message)

    def _on_finished(self, player):
        """
        Called when the playback ends
        """
        self._set_stopped()

    def _set_playing(self):
        """
        Change the widgets to show that an episode is playing
        """
        self.playing = True
        self.widgets.toggle.set_from_icon_name('media-playback-pause-symbolic',
                                               Gtk.IconSize.BUTTON)
        self.widgets.controls.show()
        self.widgets.state.set_visible_child_name('player')

    def _set_paused(self):
        """
        Change the widgets to show that the episode is paused
        """
        self.playing = False
        self.widgets.toggle.set_from_icon_name('media-playback-start-symbolic',
                                               Gtk.IconSize.BUTTON)
        self.widgets.controls.show()
        self.widgets.state.set_visible_child_name('player')

    def _set_stopped(self):
        """
        Change the widgets to show that the playback has stopped
        """
        self.playing = False
        self.widgets.controls.hide()
        self.widgets.state.set_visible_child_name('title')

    def _update_progress(self):
        """
        Update the slider
        """
        position = self.player.query_position(Gst.Format.TIME)[1] or 0
        duration = (
            self.player.query_duration(Gst.Format.TIME)[1] or
            self.episode.duration * Gst.SECOND or
            0
        )

        # Progress bar
        if duration:
            self.widgets.progress.set_range(0, duration)
            self.widgets.progress.set_value(position)
        else:
            self.widgets.progress.set_value(0)

        position = position // Gst.SECOND
        duration = duration // Gst.SECOND

        # Labels
        self.widgets.position.set_text(format_position(position, duration))
        self.widgets.duration.set_text(format_duration(duration))

        return True

    def _on_play_toggled(self, button):
        """
        Called when the play/pause button is clicked
        """
        if self.playing:
            self.player.set_state(Gst.State.PAUSED)
            self._set_paused()
        else:
            self.player.set_state(Gst.State.PLAYING)
            self._set_playing()

    def _on_forward_clicked(self, button):
        """
        Called when the forward button is clicked
        """
        position = self.player.query_position(Gst.Format.TIME)[1] or 0
        position += 30 * Gst.SECOND
        self.player.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            position)

    def _on_backward_clicked(self, button):
        """
        Called when the backward button is clicked
        """
        position = self.player.query_position(Gst.Format.TIME)[1] or 0
        position -= 30 * Gst.SECOND
        if position < 0:
            position = 0

        self.player.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            position)
