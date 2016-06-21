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

from gi.repository import Gtk

from podcasts.__version__ import __appname__
from podcasts.frontend.podcast_list import PodcastList
from podcasts.frontend.episode_list import EpisodeList


class MainWindow(Gtk.Window):
    """
    Main window of the application.
    """
    def __init__(self):
        Gtk.Window.__init__(self, title=__appname__)
        self.set_default_size(800, 600)

        # Create widgets
        builder = Gtk.Builder()
        builder.add_from_file("data/headerbar.ui")

        self.headerbar = builder.get_object("headerbar")

        self.podcast_list = PodcastList()
        self.podcast_list.connect('podcast-selected',
                                  self._on_podcast_selected)
        self.episode_list = EpisodeList()

        # Layout
        vbox = Gtk.VBox()
        self.add(vbox)

        vbox.pack_start(self.headerbar, False, False, 0)

        paned = Gtk.Paned()
        paned.set_position(300)
        vbox.pack_start(paned, True, True, 0)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add_with_viewport(self.podcast_list)
        paned.add1(scrolled_window)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add_with_viewport(self.episode_list)
        paned.add2(scrolled_window)

    def _on_podcast_selected(self, podcast_list, podcast):
        """
        Called when a podcast is selected in the podcast list.

        Show the podcast's episodes in the episode list.
        """
        self.episode_list.select(podcast)
