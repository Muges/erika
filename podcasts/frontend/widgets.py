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
Simple widgets
"""

from collections import OrderedDict
import logging

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango


def Label(lines=1):
    """
    Return a Gtk.Label widget.

    Parameters
    ----------
    lines : Optional[int]
        If lines is set to an integer greater than 1, enable wrapping and limit
        the number of lines that should be displayed.

    Returns
    -------
    Gtk.Label
    """
    label = Gtk.Label()
    label.set_alignment(xalign=0, yalign=0.5)
    label.set_ellipsize(Pango.EllipsizeMode.END)

    if lines > 1:
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_lines(lines)

    return label


class ListBox(Gtk.ListBox):
    """
    A Gtk.ListBox patched to handle multiple selection
    """
    # TODO : test with filtering.
    # TODO : Add Select All shortcut
    def __init__(self):
        Gtk.ListBox.__init__(self)
        self.connect("button-press-event", ListBox._on_button_press_event)
        self.connect("key-press-event", ListBox._on_key_press_event)

        self.last_clicked = None
        self.last_focused = None

    def remove(self, child):
        if self.last_clicked == child:
            self.last_clicked = None
        if self.last_focused == child:
            self.last_focused = None
        Gtk.ListBox.remove(self, child)

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
            index -= 1
        elif event.keyval == Gdk.KEY_Down:
            index += 1

        # Get the row
        row = self.get_row_at_index(index)
        if row is None:
            return True

        if event.state & Gdk.ModifierType.SHIFT_MASK:
            self._select_interval(row)
        else:
            self._select_single(row)

        return True

    def _add_to_selection(self, row):
        """
        Add the row to the current selection

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
        """
        Add the row to the current selection

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
        """
        Select the all the rows between the one that was clicked last and the
        one in the parameters.

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

        for index in range(first, last+1):
            self.select_row(self.get_row_at_index(index))


class IndexedListBox(ListBox):
    """
    A ListBox whose rows are indexed.
    """
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__))

        self.rows = {}

    def get_ids(self):
        """
        Return the ids of all the rows.

        Returns
        -------
        set
        """
        return set(self.rows.keys())

    def get_row(self, row_id):
        """
        Return the row certain id

        Parameters
        ----------
        row_id
            The id of the row

        Returns
        -------
        Gtk.ListBoxRow

        Raises
        ------
        ValueError if there is no row with this id
        """
        if row_id not in self.rows:
            raise ValueError(
                "The ListBox has no row with id '{}'.".format(row_id))

        return self.rows[row_id]

    def add_with_id(self, row, row_id):
        """
        Add a row certain id

        Parameters
        ----------
        row : Gtk.ListBoxRow
            The row
        row_id
            The id of the row

        Raises
        ------
        ValueError if there is already a row with this id
        """
        if row_id in self.rows:
            raise ValueError(
                "The ListBox already has a row with id '{}'.".format(row_id))

        self.rows[row_id] = row
        self.add(row)

    def remove_id(self, row_id):
        """
        Remove a row with a certain id

        Parameters
        ----------
        row_id
            The id of the row to remove

        Raises
        ------
        ValueError if there is no row with this id
        """
        try:
            row = self.rows.pop(row_id)
        except KeyError:
            raise ValueError(
                "The ListBox has no row with id '{}'.".format(row_id))

        self.remove(row)

    def clear(self):
        """
        Remove all the rows.
        """
        for child in self.get_children():
            child.destroy()

        self.rows = {}


class StatusBox(Gtk.HBox):
    """
    Widget allowing to easily display loading messages in a status bar.

    The add method adds a new message to the StatusBox. The messages are
    displayed in the order they where added. As long as at least one message
    is being displayed, a spinner is displayed at the start (usually left) of
    the StatusBox.

    Each message can be removed by calling the remove method with the
    corresponding message id, which is returned by the add method.
    """
    def __init__(self):
        Gtk.HBox.__init__(self)
        self.set_spacing(5)

        self.next_id = 0
        self.messages = OrderedDict()
        self.separators = []

        self.spinner = Gtk.Spinner()
        self.pack_start(self.spinner, False, False, 0)

    def _get_message_index(self, message_id):
        """
        Get the position of the message.
        """
        for index, key in enumerate(self.messages.keys()):
            if key == message_id:
                return index

    def add(self, message):
        """
        Add a new message.

        Parameters
        ----------
        message : str
            The message that will be displayed.

        Returns
        -------
        int
            A unique message id.
        """
        message_id = self.next_id
        self.next_id += 1

        # Add a separator between this message and the previous one if needed
        if self.messages:
            separator = Gtk.Separator.new(Gtk.Orientation.VERTICAL)
            separator.show()
            self.pack_start(separator, False, False, 0)
            self.separators.append(separator)

        # Add a label displaying the message
        label = Gtk.Label(message)
        label.show()
        self.pack_start(label, False, False, 0)
        self.messages[message_id] = label

        # Start the spinner
        self.spinner.start()

        return message_id

    def remove(self, message_id):
        """
        Remove a message.

        Parameters
        ----------
        message_id : int
            The id of the message.
        """
        index = self._get_message_index(message_id)

        # Remove the label
        label = self.messages.pop(message_id)
        label.destroy()

        # Remove the separator
        try:
            separator = self.separators.pop(max(0, index-1))
        except IndexError:
            pass
        else:
            separator.destroy()

        # Stop the spinner if no message is being displayed
        if not self.messages:
            self.spinner.stop()
