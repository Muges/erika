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

# TODO : prevent 6-10 seconds delay at the beginning? (same problem with totem)

import logging
import os

from gi.repository import GObject
from gi.repository import Gst
from gi.repository import Gtk
from gi.repository import GLib

from podcasts.__version__ import __appname__
from podcasts.library import Library, EpisodeAction
from podcasts.util import format_duration

# Mark episodes as read if there are less than MARK_MARGIN seconds remaining
MARK_MARGIN = 30

# For some reason this is not defined in the python gstreamer bindings.
GST_PLAY_FLAG_DOWNLOAD = 1 << 7


class Player(GObject.Object):
    """
    Object handling the audio playback

    Signals
    -------
    episode-updated(Episode)
        Emitted at the end of the playback of an episode.
    """

    __gsignals__ = {
        'episode-updated':
            (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
    }

    def __init__(self):
        GObject.Object.__init__(self)

        self.logger = logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__))

        self.episode = None
        self._position = 0
        self._duration = 0

        # Create player
        self.player = Gst.ElementFactory.make("playbin")
        flags = self.player.get_property("flags")
        flags |= GST_PLAY_FLAG_DOWNLOAD
        self.player.set_property("flags", flags)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_message)

        # Create widgets
        self.widgets = PlayerWidgets(self)

    def play(self, episode):
        """
        Start the playback of an episode

        Parameters
        ----------
        episode : Episode
        """
        self.stop()
        self.episode = episode

        self.widgets.set_current_episode(episode)

        if episode.local_path and os.path.isfile(episode.local_path):
            uri = Gst.filename_to_uri(episode.local_path)
        else:
            uri = episode.file_url

        self.player.set_property("uri", uri)
        self.player.set_state(Gst.State.PLAYING)

    def stop(self):
        """
        Stop the playback of an episode.
        """
        if not self.episode:
            return

        position = self.get_position() // Gst.SECOND
        duration = self.get_duration() // Gst.SECOND
        if position >= duration - MARK_MARGIN:
            # Mark as read and unset progress
            self.episode.progress = 0
            self.episode.mark_as_played()
        else:
            # Save progress
            self.episode.progress = position

        library = Library()
        action = EpisodeAction.new(self.episode, "play", 0, position, duration)
        library.commit([self.episode, action])

        self.emit("episode-updated", self.episode)

        self.player.set_state(Gst.State.NULL)
        self.widgets.set_state(PlayerWidgets.TITLE)
        self.episode = None
        self._position = 0
        self._duration = 0

    def get_duration(self):
        """
        Return the duration of the current episode, or 0 if it is unknown.
        """
        if not self._duration:
            success, duration = self.player.query_duration(Gst.Format.TIME)
            if success:
                self._duration = duration

        return self._duration

    def get_position(self):
        """
        Return the current playback position, or 0 if it is unknown.

        Parameters
        ----------
        format : Gst.Format
        """
        success, position = self.player.query_position(Gst.Format.TIME)
        if success:
            self._position = position

        return self._position

    def percent_to_time(self, percent):
        """
        Convert a time in format Gst.Format.PERCENT to Gst.Format.TIME

        Parameters
        ----------
        percent : int
        """
        duration = self.get_duration()
        return percent * duration / 1000000

    def get_buffered(self):
        """
        Return the percentage of the episode that has been buffered
        """
        position = self.player.query_position(Gst.Format.PERCENT)[1] or 0

        query = Gst.Query.new_buffering(Gst.Format.PERCENT)
        if self.player.query(query):
            stop = query.parse_buffering_range()[2]
            if stop >= position:
                return self.percent_to_time(stop)

            for n in range(0, query.get_n_buffering_ranges()):
                stop = query.parse_nth_buffering_range(n)[2]
                if stop >= position:
                    return self.percent_to_time(stop)

        return self.get_position()

    def set_state(self, state):
        """
        Set the player state

        Parameters
        ----------
        state : Gst.State
        """
        self.player.set_state(state)

    def seek(self, position):
        """
        Send a seek event to the player.

        Parameters
        ----------
        position : int
            Position in nanoseconds
        """
        if position < 0:
            position = 0

        self._position = int(position)

        self.player.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            position)

    def seek_relative(self, offset):
        """
        Send a seek event relative to the current position.

        Parameters
        ----------
        offset : int
            Offset in nanoseconds
        """
        position = self.player.query_position(Gst.Format.TIME)[1] or 0
        position += offset
        self.seek(position)

    def _on_message(self, bus, message):
        """
        Handle gstreamer bus messages
        """
        if message.type == Gst.MessageType.EOS:
            # End of stream
            self.stop()
        elif message.type == Gst.MessageType.ERROR:
            # The stream ended because of an error
            self.stop()

            err, debug = message.parse_error()
            self.logger.error(err.message)
            self.logger.error("Debugging info: %s", err.message)
        elif message.type == Gst.MessageType.DURATION_CHANGED:
            # The duration of the stream changed
            success, duration = self.player.query_duration(Gst.Format.TIME)
            if success:
                self._duration = duration
        elif message.type == Gst.MessageType.STATE_CHANGED:
            oldstate, newstate, pending = message.parse_state_changed()
            if oldstate == newstate:
                return

            if message.src != self.player:
                return

            if all((oldstate == Gst.State.READY,
                    newstate == Gst.State.PAUSED,
                    self.episode.progress > 0)):
                # TODO : try to seek earlier (before having buffered 30s...)
                self.seek(self.episode.progress * Gst.SECOND)

            if newstate == Gst.State.READY:
                self.widgets.set_state(PlayerWidgets.BUFFERING)
            if newstate == Gst.State.PLAYING:
                self.widgets.set_state(PlayerWidgets.PLAYING)
            elif newstate == Gst.State.PAUSED:
                self.widgets.set_state(PlayerWidgets.PAUSED)


class PlayerWidgets(GObject.Object):
    """
    Object handling the playback interface
    """
    TITLE = 0
    PLAYING = 1
    PAUSED = 2
    BUFFERING = 3

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

        self.set_state(PlayerWidgets.TITLE)

    def set_state(self, state):
        """
        Set the current state (called by the player)

        Parameters
        ----------
        state : int
        """
        self.state = state

        if state in [PlayerWidgets.PLAYING, PlayerWidgets.PAUSED]:
            self.pause.set_visible(state == PlayerWidgets.PLAYING)
            self.play.set_visible(state == PlayerWidgets.PAUSED)
            self.controls.show()
            self.title.set_visible_child_name('player')

            self._update_progress()
            GObject.timeout_add(200, self._update_progress)
        elif state == PlayerWidgets.BUFFERING:
            self.controls.hide()
            self.title.set_visible_child_name('loading')
        elif state == PlayerWidgets.TITLE:
            self.controls.hide()
            self.title.set_visible_child_name('title')
        else:
            raise ValueError("Invalid player state : {}.".format(state))

    def set_current_episode(self, episode):
        """
        Change the episode informations in the header bar

        Parameters
        ----------
        episode : Episode
            The episode currently being played.
        """
        library = Library()

        for playing in self.playing:
            playing.set_markup(
                "<b>{}</b> from <b><i>{}</i></b>".format(
                    GLib.markup_escape_text(episode.title),
                    GLib.markup_escape_text(episode.podcast.title)))

    def _on_play_clicked(self, button):
        """
        Called when the play button is clicked
        """
        self.player.set_state(Gst.State.PLAYING)

    def _on_pause_clicked(self, button):
        """
        Called when the pause button is clicked
        """
        self.player.set_state(Gst.State.PAUSED)

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

        self.progress.set_range(0, duration)
        if not self.seeking:
            self.progress.set_value(position)
        self.progress.set_fill_level(self.player.get_buffered())

        self.position.set_text(format_duration(position // Gst.SECOND))
        self.duration.set_text(format_duration(duration // Gst.SECOND))

        return (self.state != PlayerWidgets.TITLE)
