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
Dialog used to edit the configuration
"""

from gi.repository import Gtk

from erika.library.models import database, Config
from .util import get_builder


class PreferencesDialog(Gtk.Dialog):
    """Dialog used to edit the configuration"""

    ENTRIES = ['library.podcast_directory_template',
               'library.episode_file_template', 'gpodder.deviceid',
               'gpodder.devicename', 'gpodder.password', 'gpodder.username',
               'gpodder.hostname']
    SPINS = ['library.synchronize_interval', 'downloads.workers',
             'player.smart_mark_seconds']
    CHECKS = ['gpodder.synchronize']
    FILES = ['library.root']

    def __init__(self, parent=None):
        Gtk.Dialog.__init__(self, "Preferences", parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_APPLY, Gtk.ResponseType.OK))

        # Initialize dialog and widgets
        self.builder = get_builder('data/preferences.glade')
        content = self.builder.get_object("dialog-content")
        self.get_content_area().add(content)

    def save_config(self):
        """Save the configuration in the database"""
        with database.transaction():
            for key in self.ENTRIES:
                entry = self.builder.get_object(key)
                Config.set_value(key, entry.get_text())

            for key in self.SPINS:
                spinbutton = self.builder.get_object(key)
                Config.set_value(key, spinbutton.get_value_as_int())

            for key in self.CHECKS:
                checkbutton = self.builder.get_object(key)
                Config.set_value(key, checkbutton.get_active())

            for key in self.FILES:
                filechooser = self.builder.get_object(key)
                Config.set_value(key, filechooser.get_filename())

    def load_config(self):
        """Load the configuration from the database"""
        for key in self.ENTRIES:
            entry = self.builder.get_object(key)
            entry.set_text(Config.get_value(key))

        for key in self.SPINS:
            spinbutton = self.builder.get_object(key)
            spinbutton.set_value(Config.get_value(key))

        for key in self.CHECKS:
            checkbutton = self.builder.get_object(key)
            checkbutton.set_active(Config.get_value(key))

        for key in self.FILES:
            filechooser = self.builder.get_object(key)
            filechooser.set_filename(Config.get_value(key))


def run(window=None):
    """Show the dialog and edit the configuration"""
    dialog = PreferencesDialog(window)
    dialog.load_config()

    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        dialog.save_config()

    dialog.destroy()
