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
A toggle button used to represent filtering options.
"""

from gi.repository import Gtk
from gi.repository import Gdk


class FilterButton(Gtk.ToggleButton):
    """
    A toggle button used to represent filtering options.

    The button has three states:
     - inactive (i.e. show everything);
     - filter true (e.g. show new episodes);
     - filter false (e.g. show non new episodes).
    """
    def __init__(self, icon_name):
        Gtk.ToggleButton.__init__(self)
        self.connect("button-press-event", FilterButton._on_button_press_event)

        self.state = None

        self.inactive_image = Gtk.Image.new_from_icon_name(
            icon_name, Gtk.IconSize.SMALL_TOOLBAR)
        self.filter_true_image = Gtk.Image.new_from_icon_name(
            icon_name, Gtk.IconSize.SMALL_TOOLBAR)
        self.filter_false_image = Gtk.Image.new_from_icon_name(
            icon_name, Gtk.IconSize.SMALL_TOOLBAR)
        self.filter_false_image.set_opacity(0.5)

        self.set_state(None)

    def set_state(self, state):
        """
        Set the state of the button.

        Parameters
        ----------
        state : Union[bool, None]
        """
        self.state = state
        self.set_active(state is not None)

        if self.state is None:
            self.set_image(self.inactive_image)
        elif self.state:
            self.set_image(self.filter_true_image)
        else:
            self.set_image(self.filter_false_image)

    def get_state(self):
        """
        Get the state of the button.

        Returns
        -------
        Union[bool, None]
        """
        return self.state

    def _on_button_press_event(self, event):
        """
        Called when the button is clicked.
        """
        # Propagate the event if it is not a single left button click
        if event.type != Gdk.EventType.BUTTON_PRESS or event.button != 1:
            return False

        if self.state is None:
            self.set_state(True)
        elif self.state:
            self.set_state(False)
            self.emit("toggled")
        else:
            self.set_state(None)

        return True
