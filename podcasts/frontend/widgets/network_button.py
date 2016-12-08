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
A button used to represent network connectivity options.
"""

from gi.repository import Gtk


class NetworkButton(Gtk.Button):
    """
    A button used to represent network connectivity options.
    """
    def __init__(self):
        Gtk.Button.__init__(self)
        self.set_relief(Gtk.ReliefStyle.NONE)

        self.online_image = Gtk.Image.new_from_icon_name(
            "network-transmit-receive-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        self.offline_image = Gtk.Image.new_from_icon_name(
            "network-offline-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        self.error_image = Gtk.Image.new_from_icon_name(
            "network-error-symbolic", Gtk.IconSize.SMALL_TOOLBAR)

        self.offline = False
        self.error = False
        self.set_online()

    def set_state(self, offline, error):
        """
        Change the state of the button.
        """
        self.offline = offline
        self.error = error
        if self.error:
            self.set_image(self.error_image)
        elif self.offline:
            self.set_image(self.offline_image)
        else:
            self.set_image(self.online_image)

    def set_error(self):
        self.set_state(True, True)

    def set_online(self):
        self.set_state(False, False)

    def set_offline(self):
        self.set_state(True, False)

    def get_offline(self):
        return self.offline
