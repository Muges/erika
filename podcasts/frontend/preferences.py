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

import logging
import platform

from gi.repository import Gtk
from mygpoclient.api import MygPodderClient

from podcasts.library import Library
from podcasts.config import CONFIG_TYPES
from podcasts.config_types import String, Path, Integer, Boolean


def run(window=None):
    logger = logging.getLogger(__name__)

    # Initialize dialog and widgets
    builder = Gtk.Builder.new_from_file("data/preferences.ui")

    dialog = builder.get_object("preferences-dialog")
    dialog.set_transient_for(window)

    error_bar = builder.get_object("error-bar")
    synchronize_checkbutton = builder.get_object("synchronize-checkbutton")
    hostname_entry = builder.get_object("hostname-entry")
    username_entry = builder.get_object("username-entry")
    password_entry = builder.get_object("password-entry")
    deviceid_entry = builder.get_object("deviceid-entry")
    devicename_entry = builder.get_object("devicename-entry")

    # Get values from library
    library = Library()
    config = library.get_all_config()

    for key, value in config.items():
        widget = builder.get_object(key)
        if widget:
            CONFIG_TYPES[key].write_widget(widget, value)

    response = dialog.run()

    if response == Gtk.ResponseType.APPLY:
        # Save values to library
        for key in config:
            widget = builder.get_object(key)
            if widget:
                value = CONFIG_TYPES[key].read_widget(widget)
                config[key] = value

        library.save_config(config)

    dialog.destroy()
