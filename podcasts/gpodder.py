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

from mygpoclient.api import MygPodderClient, EpisodeAction
from mygpoclient.util import iso8601_to_datetime

from podcasts.library import Library


def make_action(dictionnary):
    """
    Parameters
    ----------
    dictionnary : dict
        A dictionnary representing an episode action

    Returns
    -------
    EpisodeAction
        The corresponding EpisodeAction object
    """
    if dictionnary["action"] != "play":
        del dictionnary["started"]
        del dictionnary["position"]
        del dictionnary["total"]

    return EpisodeAction(**dictionnary)

def synchronize_subscriptions():
    """
    Synchronize the podcasts subscriptions with a gpodder.net account.
    """
    logger = logging.getLogger(__name__)

    library = Library()

    # Check that the synchronization is enabled
    synchronize = library.get_config("gpodder.synchronize") == "true"
    if not synchronize:
        return

    logger.info("Synchronizing subscriptions.")

    # Get the identifiers from the library
    hostname = library.get_config("gpodder.hostname")
    username = library.get_config("gpodder.username")
    password = library.get_config("gpodder.password")
    deviceid = library.get_config("gpodder.deviceid")
    last_subscription_sync = library.get_config("gpodder.last_subscription_sync", "0")

    # Get the podcasts changes from the library
    added = library.get_added_podcasts()
    removed = library.get_removed_podcasts()

    try:
        logger.debug("Connecting to gpodder.net.")
        client = MygPodderClient(username, password, hostname)

        logger.debug("Downloading subscription changes.")
        changes = client.pull_subscriptions(deviceid, last_subscription_sync)

        logger.debug("Uploading subscription changes.")
        result = client.update_subscriptions(deviceid, added, removed)
    except:
        logger.exception("Unable to sync subscriptions with gpodder.net")
        return
    else:
        logger.debug("Syncing with library.")
        library.update_urls(result.update_urls)

        for url in changes.remove:
            library.remove_podcast_with_url(url)

        for url in changes.add:
            library.add_source("rss", url, synced=True)

        library.reset_podcast_synchronization()
        library.set_config("gpodder.last_subscription_sync", result.since)

def synchronize_episode_actions(download=True):
    """
    Synchronize the episode actions with a gpodder.net account.
    """
    logger = logging.getLogger(__name__)

    library = Library()

    # Check that the synchronization is enabled
    synchronize = library.get_config("gpodder.synchronize") == "true"
    if not synchronize:
        return

    logger.info("Synchronizing episode actions.")

    # Get the identifiers from the library
    hostname = library.get_config("gpodder.hostname")
    username = library.get_config("gpodder.username")
    password = library.get_config("gpodder.password")
    deviceid = library.get_config("gpodder.deviceid")
    last_episodes_sync = library.get_config("gpodder.last_episodes_sync", "0")

    # Get the episode actions from the library
    actions = [make_action(a) for a in library.get_episode_actions()]

    try:
        logger.debug("Connecting to gpodder.net.")
        client = MygPodderClient(username, password, hostname)

        logger.debug("Uploading episode actions.")
        since = client.upload_episode_actions(actions)

        if download:
            logger.debug("Downloading episode actions.")
            changes = client.download_episode_actions(last_episodes_sync, device_id=deviceid)
    except:
        logger.exception("Unable to sync episode actions with gpodder.net")
        return
    else:
        logger.debug("Syncing with library.")
        library.remove_episode_actions()

        if download:
            actions = sorted(changes.actions, key=lambda a: iso8601_to_datetime(a.timestamp))

            for action in actions:
                library.handle_episode_action(action)

            library.set_config("gpodder.last_episodes_sync", since)

def upload_episode_actions():
    """
    Upload the episode actions to a gpodder.net account.
    """
    synchronize_episode_actions(download=False)
