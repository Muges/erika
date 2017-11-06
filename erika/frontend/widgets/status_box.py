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
Widget allowing to easily display loading messages in a status bar
"""

# pylint: disable=arguments-differ

from collections import OrderedDict

from gi.repository import Gtk


class StatusBox(Gtk.HBox):
    """Widget allowing to easily display loading messages in a status bar

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

        self.next_id = 1
        self.messages = OrderedDict()
        self.separators = []

        self.spinner = Gtk.Spinner()
        self.pack_start(self.spinner, False, False, 0)

    def _get_message_index(self, message_id):
        """Get the position of a message given its id"""
        for index, key in enumerate(self.messages.keys()):
            if key == message_id:
                return index

    def get_next_message_id(self):
        """Return the id of the next message"""
        message_id = self.next_id
        self.next_id += 1
        return message_id

    def add(self, message, message_id):
        """Add a new message

        Parameters
        ----------
        message : str
            The message that will be displayed.
        message_id : int
            The id of the message (this should be the value returned by
            self.get_next_message_id())
        """
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

    def edit(self, message_id, message):
        """Edit a message

        Parameters
        ----------
        message_id : int
            The id of the message.
        """
        # Edit the label
        label = self.messages[message_id]
        label.set_text(message)

    def remove(self, message_id):
        """Remove a message

        Parameters
        ----------
        message_id : int
            The id of the message.
        """
        index = self._get_message_index(message_id)
        if index is None:
            # The message does not exist
            return

        # Remove the label
        label = self.messages.pop(message_id)
        label.destroy()  # pylint: disable=no-member

        # Remove the separator
        try:
            separator = self.separators.pop(max(0, index - 1))
        except IndexError:
            pass
        else:
            separator.destroy()

        # Stop the spinner if no message is being displayed
        if not self.messages:
            self.spinner.stop()
