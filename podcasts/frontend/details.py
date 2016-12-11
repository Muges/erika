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
Widget displaying the details of a podcast or episode.
"""

import webbrowser

from gi.repository import Gtk
from gi.repository import WebKit
from gi.repository import GObject
from gi.repository import Pango


class DetailsStyle(object):
    def __init__(self):
        self.background = '#ffffff'
        self.foreground = '#000000'


class Details(Gtk.ScrolledWindow):
    """
    Widget displaying the details of a podcast or episode.
    """
    def __init__(self):
        super().__init__()
        self.view = WebKit.WebView()
        self.add(self.view)

        settings = self.view.get_settings()
        settings.set_property('enable-java-applet', False)
        settings.set_property('enable-plugins', False)
        settings.set_property('enable-scripts', False)
        settings.set_property('enable-default-context-menu', False)

        self.style = DetailsStyle()
        GObject.idle_add(self._set_style)

        self.view.connect('navigation-policy-decision-requested', self._on_link_clicked)

    def _set_style(self):
        """
        Get colors and font from the GTK theme.
        """
        context = self.view.get_style_context()
        font = context.get_font(Gtk.StateFlags.NORMAL)

        settings = self.view.get_settings()
        #settings.set_property('default-font-size', font.get_size() // Pango.SCALE)
        settings.set_property('default-font-family', font.get_family())

        success, background = context.lookup_color('bg_color')
        if success:
            self.style.background = background.to_string()

        success, foreground = context.lookup_color('fg_color')
        if success:
            self.style.foreground = foreground.to_string()

    def show_episode(self, episode):
        """
        Show the details of an episode.
        """
        with open("data/episode_details_template.html", 'r') as fileobj:
            template = fileobj.read()

        html = template.format(
            style=self.style,
            episode=episode
        )
        self.view.load_html_string(html, "")

    def show_podcast(self, podcast):
        """
        Show the details of a podcast.
        """
        with open("data/podcast_details_template.html", 'r') as fileobj:
            template = fileobj.read()

        html = template.format(
            style=self.style,
            podcast=podcast
        )
        self.view.load_html_string(html, "")

    def _on_link_clicked(self, view, frame, request, action, decision):
        webbrowser.open(request.get_uri())
        decision.ignore()
        return True
