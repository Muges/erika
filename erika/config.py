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
The :mod:`erika.config` module defines constants used for the configuration or
erika.
"""

from os.path import expanduser, join
import platform
from gi.repository import GLib

from .__version__ import __appname__


# Directories
HOME = expanduser("~")
CONFIG_DIR = join(GLib.get_user_config_dir(), __appname__.lower())

DATABASE_PATH = join(CONFIG_DIR, "library")

CONFIG_DEFAULTS = {
    "library.root": join(HOME, "Podcasts"),
    "library.podcast_directory_template": "{podcast.title}",
    "library.episode_file_template":
        "{episode.pubdate:%Y.%m.%d} - {episode.title}",
    "library.synchronize_interval": 60,

    "player.smart_mark_seconds": 30,

    "downloads.workers": 2,

    "gpodder.synchronize": False,
    "gpodder.hostname": "gpodder.net",
    "gpodder.username": "",
    "gpodder.password": "",
    "gpodder.deviceid": "{}-{}".format(__appname__.lower(), platform.node()),
    "gpodder.devicename": "{} on {}".format(__appname__, platform.node()),
    "gpodder.devicename_changed": False,
    "gpodder.last_subscription_sync": 0,
    "gpodder.last_episodes_sync": 0,

    "network.connection_check_hostname": "github.com",
}
