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
    """A toggle button used to represent filtering options

    The button has three possible states:
     - None or inactive (i.e. show everything);
     - True (e.g. show new episodes);
     - False (e.g. show non new episodes).

    Parameters
    ----------
    icon_name : str
        The name of the icon of the button
    name : str
        The name of the filter, it is used in the tooltip of the button ("Show
        all", "Show only {name}" or "Hide {name}").
    key : Any
        This is not used by the FilterButton itself, but can be used to store a
        filter key, which will then be accessible through the key attribute.
    """
    def __init__(self, icon_name, name, key=None):
        Gtk.ToggleButton.__init__(self)
        self.connect("button-press-event", FilterButton._on_button_press_event)

        self.name = name
        self.key = key
        self.state = None

        self.inactive_image = Gtk.Image.new_from_icon_name(
            icon_name, Gtk.IconSize.SMALL_TOOLBAR)
        self.filter_true_image = Gtk.Image.new_from_icon_name(
            icon_name, Gtk.IconSize.SMALL_TOOLBAR)
        self.filter_false_image = Gtk.Image.new_from_icon_name(
            icon_name, Gtk.IconSize.SMALL_TOOLBAR)
        self.filter_false_image.set_opacity(0.5)

        self._set_state(None)

    def _set_state(self, state):
        """Set the state of the button

        Parameters
        ----------
        state : Union[bool, None]
        """
        self.state = state
        self.set_active(state is not None)

        if self.state is None:
            self.set_image(self.inactive_image)
            self.set_tooltip_text("Show only {}".format(self.name))
        elif self.state:
            self.set_image(self.filter_true_image)
            self.set_tooltip_text("Hide {}".format(self.name))
        else:
            self.set_image(self.filter_false_image)
            self.set_tooltip_text("Show all")

    def _on_button_press_event(self, event):
        """Called when the button is clicked"""
        # Propagate the event if it is not a single left button click
        if event.type != Gdk.EventType.BUTTON_PRESS or event.button != 1:
            return False

        # Rotate through the states (None -> True -> False -> None...)
        if self.state is None:
            self._set_state(True)
        elif self.state:
            self._set_state(False)
            self.emit("toggled")
        else:
            self._set_state(None)

        return True
