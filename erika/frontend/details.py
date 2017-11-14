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
Widget displaying the details of a podcast or episode
"""

import threading
import pkgutil

from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import Gio

from erika.frontend.widgets import WebView


class Details(Gtk.ScrolledWindow):
    """Widget displaying the details of a podcast or episode"""
    EPISODE_TEMPLATE = pkgutil.get_data(
        'erika.frontend', 'data/episode_details_template.html'
    ).decode('utf-8')
    PODCAST_TEMPLATE = pkgutil.get_data(
        'erika.frontend', 'data/podcast_details_template.html'
    ).decode('utf-8')

    def __init__(self):
        super().__init__()

        self.current = None  # Current episode or podcast being shown

        self.view = WebView()
        self.add(self.view)

    def show_episode(self, episode, get_image=True):
        """Show the details of an episode"""
        self.current = episode

        html = self.EPISODE_TEMPLATE.format(episode=episode)
        self.view.load_html_string(html, "")

        # If the image is not available, download it in a thread, and
        # update the view at the end
        application = Gio.Application.get_default()
        if all((get_image,
                not episode.image_downloaded,
                application.get_online())):
            def _end():
                if episode == self.current:
                    self.show_episode(episode, get_image=False)

            def _thread():
                episode.get_image()
                GObject.idle_add(_end)

            thread = threading.Thread(target=_thread)
            thread.start()

    def show_podcast(self, podcast):
        """Show the details of a podcast"""
        self.current = podcast

        html = self.PODCAST_TEMPLATE.format(podcast=podcast)
        self.view.load_html_string(html, "")
