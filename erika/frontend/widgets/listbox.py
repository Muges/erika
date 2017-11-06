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
A Gtk.ListBox patched to handle multiple selection
"""

from gi.repository import Gtk
from gi.repository import Gdk


class ListBox(Gtk.ListBox):
    """A Gtk.ListBox patched to handle multiple selection"""
    def __init__(self):
        Gtk.ListBox.__init__(self)
        self.connect("button-press-event", ListBox._on_button_press_event)
        self.connect("key-press-event", ListBox._on_key_press_event)

        self.last_clicked = None
        self.last_focused = None
        self.filter_func = None

    def remove(self, child):  # pylint: disable=arguments-differ
        """Remove a child element"""
        if self.last_clicked == child:
            self.last_clicked = None
        if self.last_focused == child:
            self.last_focused = None
        Gtk.ListBox.remove(self, child)

    def set_filter_func(self, filter_func):  # pylint: disable=arguments-differ
        # Keep a references to the filter function
        self.filter_func = filter_func
        Gtk.ListBox.set_filter_func(self, filter_func)

    def invalidate_filter(self):  # pylint: disable=arguments-differ
        Gtk.ListBox.invalidate_filter(self)

        if self.last_clicked and not self.filter_func(self.last_clicked):
            self.last_clicked = None
        if self.last_focused and not self.filter_func(self.last_focused):
            self.last_focused = None

        # Unselect the rows that are not visible
        for row in self.get_selected_rows():
            if not self.filter_func(row):
                self.unselect_row(row)

    def _on_button_press_event(self, event):
        # Propagate the event if it is not a single left button click or in
        # single selection mode
        if any((self.get_selection_mode() != Gtk.SelectionMode.MULTIPLE,
                event.type != Gdk.EventType.BUTTON_PRESS,
                event.button != 1 and event.button != 3)):
            return False

        # Get the row that was clicked
        row = self.get_row_at_y(event.y)

        if event.button == 1:
            # Left click
            if row is None:
                return True

            if self.last_clicked is None:
                self.last_clicked = self.get_row_at_index(0)

            if event.state & Gdk.ModifierType.SHIFT_MASK:
                self._select_interval(row)
            elif event.state & Gdk.ModifierType.CONTROL_MASK:
                self._add_to_selection(row)
            else:
                self._select_single(row)

            return True
        elif event.button == 3:
            # Right click
            if row and not row.is_selected():
                self._select_single(row)

            self.emit("popup-menu")

            return False

    def _on_key_press_event(self, event):
        # Propagate the event if the key pressed is not up or down or in single
        # selection mode
        if any((self.get_selection_mode() != Gtk.SelectionMode.MULTIPLE,
                event.keyval != Gdk.KEY_Up and event.keyval != Gdk.KEY_Down)):
            return False

        if self.last_clicked is None:
            self.last_clicked = self.get_row_at_index(0)
        if self.last_focused is None:
            self.last_focused = self.get_row_at_index(0)

        # Get the index of the next or previous row depending on the key
        # pressed
        index = self.last_focused.get_index()
        if event.keyval == Gdk.KEY_Up:
            delta = 1
        elif event.keyval == Gdk.KEY_Down:
            delta = 1

        # Get the next/previous visible row
        while True:
            index += delta
            row = self.get_row_at_index(index)
            if row is None:
                return True
            if self.filter_func(row):
                break

        if event.state & Gdk.ModifierType.SHIFT_MASK:
            self._select_interval(row)
        else:
            self._select_single(row)

        return True

    def _add_to_selection(self, row):
        """Add the row to the current selection

        Parameters
        ----------
        row : Gtk.ListBoxRow
            A child of the ListBox
        """
        self.select_row(row)
        self.last_clicked = row
        self.last_focused = row
        row.grab_focus()

    def _select_single(self, row):
        """Add the row to the current selection

        Parameters
        ----------
        row : Gtk.ListBoxRow
            A child of the ListBox
        """
        # Select only this row
        self.unselect_all()
        self.select_row(row)
        self.last_clicked = row
        self.last_focused = row
        row.grab_focus()

    def _select_interval(self, row):
        """Select the all the rows between the one that was clicked last and
        the one in the parameters

        Parameters
        ----------
        row : Gtk.ListBoxRow
            A child of the ListBox
        """
        self.unselect_all()
        self.last_focused = row
        row.grab_focus()

        first = self.last_clicked.get_index()
        last = row.get_index()
        if first > last:
            first, last = last, first

        for index in range(first, last + 1):
            row = self.get_row_at_index(index)
            # Select only the visible rows
            if self.filter_func(row):
                self.select_row(row)
