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

import logging
import os

from gi.repository import GObject
from gi.repository import Gst
from gi.repository import GLib

from erika.library.models import Config, EpisodeAction

# For some reason this is not defined in the python gstreamer bindings.
GST_PLAY_FLAG_DOWNLOAD = 1 << 7


class Player(GObject.Object):
    """
    Object handling the audio playback

    Signals
    -------
    episode-updated(Episode)
        Emitted at the end of the playback of an episode.
    progress-changed(position, duration)
        Emitted every 200ms during playback.
    state-changed(episode, state)
        Emitted when the player state has changed.
    """

    STOPPED = 0
    PLAYING = 1
    PAUSED = 2
    BUFFERING = 3

    __gsignals__ = {
        'episode-updated':
            (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
        'progress-changed':
            (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_LONG,
                                              GObject.TYPE_LONG)),
        'state-changed':
            (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_PYOBJECT,
                                              GObject.TYPE_INT,)),
    }

    def __init__(self):
        GObject.Object.__init__(self)

        self.logger = logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__))

        self.episode = None
        self.state = Player.STOPPED
        self._started = 0
        self._duration = 0

        self.progress_timer = None

        # Create player
        self.player = Gst.ElementFactory.make("playbin")
        flags = self.player.get_property("flags")
        flags |= GST_PLAY_FLAG_DOWNLOAD
        self.player.set_property("flags", flags)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_message)

    def play_episode(self, episode):
        """Start the playback of an episode

        Parameters
        ----------
        episode : Episode
        """
        self.stop()
        self.episode = episode
        self._started = self.episode.progress

        self.set_state(Player.BUFFERING)

        if episode.local_path and os.path.isfile(episode.local_path):
            uri = Gst.filename_to_uri(episode.local_path)
        else:
            uri = episode.file_url

        self.player.set_property("uri", uri)
        self.player.set_state(Gst.State.PLAYING)

        self.progress_timer = GObject.timeout_add(200, self._emit_progress)

    def stop(self):
        """Stop the playback of an episode"""
        if self.progress_timer:
            GLib.source_remove(self.progress_timer)
            self.progress_timer = None

        if not self.episode:
            return

        self.set_state(Player.STOPPED)

        smart_mark_seconds = Config.get_value("player.smart_mark_seconds")

        position = self.get_position() // Gst.SECOND
        duration = self.get_duration() // Gst.SECOND
        if position + smart_mark_seconds >= duration:
            # Mark as read and unset progress
            self.episode.progress = 0
            self.episode.mark_as_played()
            position = duration
        else:
            # Save progress
            self.episode.progress = position
        self.episode.save()

        action = EpisodeAction(episode=self.episode, action="play",
                               started=self._started, position=position,
                               total=duration)
        action.save()

        self.emit("episode-updated", self.episode)

        self.player.set_state(Gst.State.NULL)
        self.episode = None
        self._duration = 0

    def get_duration(self):
        """Return the duration of the current episode, or 0 if it is unknown"""
        if not self._duration:
            success, duration = self.player.query_duration(Gst.Format.TIME)
            if success:
                self._duration = duration

        return self._duration

    def get_position(self):
        """Return the current playback position, or 0 if it is unknown"""
        success, position = self.player.query_position(Gst.Format.TIME)
        if success:
            return position

        return 0

    def get_seconds_duration(self):
        """Return the duration of the current episode in seconds, or 0 if it
        is unknown"""
        return self.get_duration() // Gst.SECOND

    def get_seconds_position(self):
        """Return the current playback position in seconds, or 0 if it is
        unknown"""
        return self.get_position() // Gst.SECOND

    def percent_to_time(self, percent):
        """Convert a time in format Gst.Format.PERCENT to Gst.Format.TIME

        Parameters
        ----------
        percent : int
        """
        duration = self.get_duration()
        return percent * duration / 1000000

    def get_buffered(self):
        """Return the percentage of the episode that has been buffered"""
        position = self.player.query_position(Gst.Format.PERCENT)[1] or 0

        query = Gst.Query.new_buffering(Gst.Format.PERCENT)
        if self.player.query(query):
            stop = query.parse_buffering_range()[2]
            if stop >= position:
                return self.percent_to_time(stop)

            for range_index in range(0, query.get_n_buffering_ranges()):
                stop = query.parse_nth_buffering_range(range_index)[2]
                if stop >= position:
                    return self.percent_to_time(stop)

        return self.get_position()

    def seek(self, position):
        """Send a seek event to the player

        Parameters
        ----------
        position : int
            Position in nanoseconds
        """
        if position < 0:
            position = 0

        self.player.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            position)

    def seek_relative(self, offset):
        """Send a seek event relative to the current position

        Parameters
        ----------
        offset : int
            Offset in nanoseconds
        """
        position = self.player.query_position(Gst.Format.TIME)[1] or 0
        position += offset
        self.seek(position)

    def _on_message(self, bus, message):
        """Handle gstreamer bus messages"""
        if message.type == Gst.MessageType.EOS:
            # End of stream
            self.stop()
        elif message.type == Gst.MessageType.ERROR:
            # The stream ended because of an error
            self.stop()

            err, _ = message.parse_error()
            self.logger.error(err.message)
            self.logger.error("Debugging info: %s", err.message)
        elif message.type == Gst.MessageType.DURATION_CHANGED:
            # The duration of the stream changed
            success, duration = self.player.query_duration(Gst.Format.TIME)
            if success:
                self._duration = duration
        elif message.type == Gst.MessageType.STATE_CHANGED:
            oldstate, newstate, _ = message.parse_state_changed()
            if oldstate == newstate:
                return

            if message.src != self.player:
                return

            if all((oldstate == Gst.State.READY,
                    newstate == Gst.State.PAUSED,
                    self.episode.progress > 0)):
                self.seek(self.episode.progress * Gst.SECOND)

            if newstate == Gst.State.READY:
                self.set_state(Player.BUFFERING)
            if newstate == Gst.State.PLAYING:
                self.set_state(Player.PLAYING)
            elif newstate == Gst.State.PAUSED:
                self.set_state(Player.PAUSED)

    def _emit_progress(self):
        """Emit a progress-changed signal. Called every 200ms during
        playback"""
        position = self.get_position()
        duration = self.get_duration()
        self.emit('progress-changed', position, duration)

        return True

    def set_state(self, state):
        """Set the current state of the player"""
        self.state = state
        self.emit('state-changed', self.episode, state)

    def play(self):
        """Start the playback"""
        self.player.set_state(Gst.State.PLAYING)

    def pause(self):
        """Pause the playback"""
        self.player.set_state(Gst.State.PAUSED)

    def toggle(self):
        """Toggle between play and pause"""
        if self.state == Player.PLAYING or self.state == Player.BUFFERING:
            self.pause()
        else:
            self.play()
