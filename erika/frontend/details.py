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

from collections import namedtuple
import webbrowser
import threading
import pkgutil

from gi.repository import Gtk
from gi.repository import WebKit
from gi.repository import GObject
from gi.repository import Gio
from gi.repository import Pango

from erika.library.models import Podcast


DetailsStyle = namedtuple('Style', ['background', 'foreground'])


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
        self.style = None

        self.view = WebKit.WebView()
        self.add(self.view)

        settings = self.view.get_settings()
        settings.set_property('enable-java-applet', False)
        settings.set_property('enable-plugins', False)
        settings.set_property('enable-scripts', False)
        settings.set_property('enable-default-context-menu', False)

        # This needs to be called from the main loop to be able to get
        # the colors from the gtk theme
        GObject.idle_add(self._set_style)

        self.view.connect('navigation-policy-decision-requested',
                          self._on_link_clicked)

    def _set_style(self):
        """Get colors and font from the GTK theme"""
        context = self.view.get_style_context()

        # Get default font
        font = context.get_font(Gtk.StateFlags.NORMAL)

        settings = self.view.get_settings()
        settings.set_property('default-font-size',
                              font.get_size() // Pango.SCALE)
        settings.set_property('default-font-family', font.get_family())

        # Get colors
        success, background = context.lookup_color('bg_color')
        background = background.to_string() if success else "#000000"

        success, foreground = context.lookup_color('fg_color')
        foreground = foreground.to_string() if success else "#ffffff"

        self.style = DetailsStyle(background, foreground)

        if not self.current:
            return

        # Update the view
        if isinstance(self.current, Podcast):
            self.show_podcast(self.current)
        else:
            self.show_episode(self.current)

    def show_episode(self, episode, get_image=True):
        """Show the details of an episode"""
        self.current = episode

        if not self.style:
            # Wait for the style to be set before showing anything to
            # avoid flickering
            return

        html = self.EPISODE_TEMPLATE.format(
            style=self.style,
            episode=episode
        )
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

        if not self.style:
            return

        html = self.PODCAST_TEMPLATE.format(
            style=self.style,
            podcast=podcast
        )
        self.view.load_html_string(html, "")

    def _on_link_clicked(self, view, frame, request, action, decision):
        """Called when a link is clicked"""
        # pylint: disable=too-many-arguments,no-self-use
        webbrowser.open(request.get_uri())
        decision.ignore()
        return True
