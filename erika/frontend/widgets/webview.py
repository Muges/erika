# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Muges
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
The :mod:`erika.frontend.widgets.webview` provides a webview that is styled
using the current gtk theme.
"""

import os
from tempfile import NamedTemporaryFile
from string import Template
import webbrowser

from gi.repository import Gst
from gi.repository import Gtk
from gi.repository import Pango
from gi.repository import WebKit


class WebView(WebKit.WebView):
    """A webview styled using the current gtk theme."""
    def __init__(self):
        super().__init__()

        # Make the webview transparent (to use default background color)
        screen = self.get_screen()
        rgba = screen.get_rgba_visual()
        self.set_visual(rgba)

        self.set_transparent(True)

        # Disable scripts, plugins and context menu
        settings = self.get_settings()
        settings.set_property('enable-java-applet', False)
        settings.set_property('enable-plugins', False)
        settings.set_property('enable-scripts', False)
        settings.set_property('enable-default-context-menu', False)

        self.first_draw = True
        self.stylesheet_filename = None

        self.connect('navigation-policy-decision-requested',
                     self._on_link_clicked)
        self.connect('destroy', self._on_destroy)

    def do_draw(self, cr):
        if self.first_draw:
            context = self.get_style_context()
            settings = self.get_settings()

            # Set default font
            font = context.get_font(Gtk.StateFlags.NORMAL)
            settings.set_property('default-font-size',
                                  font.get_size() // Pango.SCALE)
            settings.set_property('default-font-family', font.get_family())

            # Generate stylesheet with default colors
            normal_color = context.get_color(Gtk.StateFlags.NORMAL).to_string()
            link_color = context.get_color(Gtk.StateFlags.LINK).to_string()

            stylesheet = Template("""
            body {
                color: $normal_color;
            }
            a {
                color: $link_color;
            }
            """).substitute(normal_color=normal_color, link_color=link_color)

            # Store the stylesheet in a temporary file
            # (the user-stylesheet-uri property does not support data uris)
            with NamedTemporaryFile(suffix='.css', delete=False) as fileobj:
                fileobj.write(stylesheet.encode('utf8'))
                self.stylesheet_filename = fileobj.name

            stylesheet_uri = Gst.filename_to_uri(self.stylesheet_filename)
            settings.set_property('user-stylesheet-uri', stylesheet_uri)

            self.first_draw = False

        return WebKit.WebView.do_draw(self, cr)

    def _on_link_clicked(self, view, frame, request, action, decision):
        """Called when a link is clicked"""
        # pylint: disable=too-many-arguments,no-self-use
        webbrowser.open(request.get_uri())
        decision.ignore()
        return True

    def _on_destroy(self, _):
        """Called when the widget is destroyed"""
        # Remove the temporary stylesheet
        os.remove(self.stylesheet_filename)
