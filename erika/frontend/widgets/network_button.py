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
A button used to represent network connectivity options
"""

from gi.repository import Gtk
from gi.repository import Gio

from erika.frontend.util import cb


class NetworkButton(Gtk.Button):
    """A button used to represent network connectivity options"""
    def __init__(self):
        Gtk.Button.__init__(self)
        self.set_relief(Gtk.ReliefStyle.NONE)

        self.online_image = Gtk.Image.new_from_icon_name(
            "network-transmit-receive-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        self.offline_image = Gtk.Image.new_from_icon_name(
            "network-offline-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        self.error_image = Gtk.Image.new_from_icon_name(
            "network-error-symbolic", Gtk.IconSize.SMALL_TOOLBAR)

        self.online = True
        self.error = False
        self.set_network_state(self.online, self.error)

        application = Gio.Application.get_default()
        application.connect('network-state-changed',
                            cb(self.set_network_state))

        self.connect('clicked',
                     lambda _: application.set_network_state(not self.online))

    def set_network_state(self, online, error):
        """Change the state of the button"""
        self.online = online
        self.error = error
        if self.online:
            self.set_image(self.online_image)
            self.set_tooltip_text("Online")
        elif self.error:
            self.set_image(self.error_image)
            self.set_tooltip_text("Unable to connect the internet")
        else:
            self.set_image(self.offline_image)
            self.set_tooltip_text("Offline mode")
