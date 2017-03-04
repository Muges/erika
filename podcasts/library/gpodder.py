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
Synchronization with gpodder.net
"""

import logging
from mygpoclient.api import MygPodderClient
from mygpoclient.simple import MissingCredentials
from mygpoclient.http import Unauthorized

from .config import Config


class GPodderUnauthorized(Exception):
    """Raised when the clients tries to connect to gpodder.net with
    invalid credentials."""

    def __init__(self):
        super().__init__("Invalid credentials. Unable to connect to "
                         "gpodder.net.")


class GPodderClient(object):
    """Client handling the synchronization of the database with gpodder.net"""
    def __init__(self):
        self.logger = logging.getLogger(
            ".".join((__name__, self.__class__.__name__)))

        self.configuration = Config.get_group("gpodder")

        self.client = None

    def enabled(self, connecting=False):
        """Returns True if the synchronization is enabled and the client is
        connected

        Parameters
        ----------
        connecting : Optional[Bool]
            True to return True even if the client is not connected yet
            (default is False)
        """
        return all((self.configuration.synchronize,
                    self.configuration.username,
                    self.configuration.password,
                    self.configuration.hostname,
                    self.client or connecting))

    def connect(self, raise_exception=False):
        """Connect to gpodder.net

        Parameters
        ----------
        raise_exception : Optional[Bool]
            True to raise an exception when the connection was unsuccessful
            (default is False)

        Returns
        -------
        bool
            True if the connection was successful
        """
        if not self.enabled(connecting=True):
            return False

        self.logger.debug("Connecting to gpodder.net.")
        try:
            self.client = MygPodderClient(self.configuration.username,
                                          self.configuration.password,
                                          self.configuration.hostname)
            self.update_device()
        except (MissingCredentials, Unauthorized):
            self.logger.warning('Invalid credentials. Unable to connect to '
                                'gpodder.net.')
            self.client = None
            if raise_exception:
                raise GPodderUnauthorized()
        except Exception:  # pylint: disable=broad-except
            self.logger.exception("Unable to connect to gpodder.net.")
            self.client = None
            if raise_exception:
                raise

        return self.client is not None

    def update_device(self):
        """Update the device name"""
        if not self.enabled():
            return

        if self.configuration.devicename_changed:
            # The device name changed locally, send it to gpodder.net
            self.client.update_device_settings(self.configuration.deviceid,
                                               self.configuration.devicename)
            Config.set_value("gpodder.devicename_changed", False)
        else:
            # The device name was not changed locally, get it from gpodder.net
            devices = self.client.get_devices()
            for device in devices:
                if device.device_id == self.configuration.deviceid:
                    Config.set_value("gpodder.devicename", device.caption)
                    break
