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

from mygpoclient.api import MygPodderClient

from podcasts.library import Library


def synchronize():
    logger = logging.getLogger(__name__)

    library = Library()

    synchronize = library.get_config("gpodder.synchronize") == "true"
    if not synchronize:
        return

    logger.debug("Synchronizing library.")
    
    hostname = library.get_config("gpodder.hostname")
    username = library.get_config("gpodder.username")
    password = library.get_config("gpodder.password")
    deviceid = library.get_config("gpodder.deviceid")
    last_subscription_sync = library.get_config("gpodder.last_subscription_sync", "0")

    added = library.get_added_podcasts()
    removed = library.get_removed_podcasts()

    try:
        client = MygPodderClient(username, password, hostname)
        result = client.update_subscriptions(deviceid, added, removed)
        changes = client.pull_subscriptions(deviceid, last_subscription_sync)
    except:
        logger.exception("Unable to sync subscriptions with gpodder.net")
    else:
        library.update_urls(result.update_urls)

        for url in changes.remove:
            library.remove_podcast_with_url(url)

        for url in changes.add:
            library.add_source("rss", url)
            
        library.reset_podcast_synchronization()
        library.set_config("gpodder.last_subscription_sync", result.since)
