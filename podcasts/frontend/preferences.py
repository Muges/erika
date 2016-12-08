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

DEFAULT_HOSTNAME = "gpodder.net"
DEFAULT_DEVICEID = "podcasts-{}".format(platform.node())
DEFAULT_DEVICENAME = "Podcasts on {}".format(platform.node())


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

    synchronize = library.get_config("gpodder.synchronize")
    hostname = library.get_config("gpodder.hostname")
    username = library.get_config("gpodder.username")
    password = library.get_config("gpodder.password")
    deviceid = library.get_config("gpodder.deviceid")
    devicename = DEFAULT_DEVICENAME

    if synchronize:
        # Test connection and get device name
        try:
            client = MygPodderClient(username, password, hostname)
            devices = client.get_devices()
        except:
            logger.exception("Unable to connect to gpodder.net")
            error_bar.show()
        else:
            for device in devices:
                if device.device_id == deviceid:
                    devicename = device.caption
                    break
    
    synchronize_checkbutton.set_active(synchronize)
    hostname_entry.set_text(hostname)
    username_entry.set_text(username)
    deviceid_entry.set_text(deviceid)
    devicename_entry.set_text(devicename)
    
    while True:
        response = dialog.run()
        if response == Gtk.ResponseType.CANCEL:
            break

        synchronize = synchronize_checkbutton.get_active()
        hostname = hostname_entry.get_text()
        username = username_entry.get_text()
        deviceid = deviceid_entry.get_text()
        devicename = devicename_entry.get_text()
        if password_entry.get_text():
            password = password_entry.get_text()

        if synchronize:
            # Test connection and set device name
            try:
                client = MygPodderClient(username, password, hostname)
                client.update_device_settings(deviceid, devicename, "desktop")
            except:
                logger.exception("Unable to connect to gpodder.net")
                error_bar.show()
                dialog.run()
                continue

        # Save preferences
        library.set_config("gpodder.synchronize", synchronize)
        library.set_config("gpodder.hostname", hostname)
        library.set_config("gpodder.username", username)
        library.set_config("gpodder.password", password)
        library.set_config("gpodder.deviceid", deviceid)
        break

    dialog.destroy()
