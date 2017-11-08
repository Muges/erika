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
The :mod:`erika.library.gpodder` module handles the synchronization of the
library with gpodder.net.
"""

import logging
from mygpoclient.api import MygPodderClient
from mygpoclient.simple import MissingCredentials
from mygpoclient.http import Unauthorized
from mygpoclient.util import iso8601_to_datetime

from .models import (database, Config, Episode, EpisodeAction, Podcast,
                     PodcastAction)


class GPodderUnauthorized(Exception):
    """Exception raised when the clients tries to connect to gpodder.net with
    invalid credentials."""

    def __init__(self):
        super().__init__("Invalid credentials. Unable to connect to "
                         "gpodder.net.")


class RemoteEpisodeAction(object):  # pylint: disable=too-few-public-methods
    """Object representing a remote episode action.

    It has the same attributes as an
    :class:`~erika.library.models.EpisodeAction`.
    """
    def __init__(self, action):
        self.podcast_url = action.podcast
        self.episode_url = action.episode,
        self.action = action.action
        self.time = iso8601_to_datetime(action.timestamp)
        self.started = action.started
        self.position = action.position
        self.total = action.total

    def __str__(self):
        attrs = ["podcast_url", "episode_url", "action", "time", "started",
                 "position", "total"]
        formatted_attrs = ["{}={}".format(attr, repr(getattr(self, attr)))
                           for attr in attrs]
        return "RemoteEpisodeAction({})".format(", ".join(formatted_attrs))


class GPodderClient(object):
    """Client handling the synchronization of the library with gpodder.net."""
    def __init__(self):
        self.logger = logging.getLogger(
            ".".join((__name__, self.__class__.__name__)))

        self.configuration = Config.get_group("gpodder")
        self.smart_mark_seconds = Config.get_value("player.smart_mark_seconds")

        self.client = None

    def enabled(self, connecting=False):
        """Return True if the synchronization is enabled and the client is
        connected.

        Parameters
        ----------
        connecting : bool, optional
            True to return True even if the client is not connected yet
            (default is False).
        """
        return all((self.configuration.synchronize,
                    self.configuration.username,
                    self.configuration.password,
                    self.configuration.hostname,
                    self.client or connecting))

    def connect(self):
        """Connect to gpodder.net.

        Returns
        -------
        bool
            True if the connection attempt was successful.
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
            raise GPodderUnauthorized()
        except Exception:  # pylint: disable=broad-except
            self.logger.exception("Unable to connect to gpodder.net.")
            self.client = None
            raise

        return self.client is not None

    def update_device(self):
        """Update the device name."""
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

        self.configuration = Config.get_group("gpodder")

    def pull_subscriptions(self):
        """Pull the subscriptions changes from gpodder.net and process them."""
        if not self.enabled():
            return

        self.logger.debug("Pulling subscription changes.")

        try:
            changes = self.client.pull_subscriptions(
                self.configuration.deviceid,
                self.configuration.last_subscription_sync)
        except Exception:  # pylint: disable=broad-except
            self.logger.exception("Unable to pull subscriptions from "
                                  "gpodder.net.")
            return

        with database.transaction():
            # Apply the changes
            for url in changes.remove:
                self.logger.debug("Removing podcast %s.", url)
                (Podcast
                 .delete()
                 .where(Podcast.url == url)
                 .execute())

            for url in changes.add:
                self.logger.debug("Adding podcast %s.", url)
                Podcast.new("rss", url)

            Config.set_value("gpodder.last_subscription_sync", changes.since)

    def push_subscriptions(self):
        """Push the local subscriptions changes to gpodder.net.

        Returns
        -------
        datetime, optional
            The time at which the subscriptions were synchronized.
        """
        if not self.enabled():
            return

        self.logger.debug("Pushing subscription changes.")

        # Get the podcasts that were added or removed since the last
        # synchronization
        add = PodcastAction().select().where(
            PodcastAction.action == 'add'
        )
        added_urls = [action.podcast_url for action in add]

        remove = PodcastAction().select().where(
            PodcastAction.action == 'remove'
        )
        removed_urls = [action.podcast_url for action in remove]

        # Send them to gpodder.net
        if added_urls or removed_urls:
            try:
                result = self.client.update_subscriptions(
                    self.configuration.deviceid, added_urls, removed_urls)
            except Exception:  # pylint: disable=broad-except
                self.logger.exception("Unable to push subscriptions to "
                                      "gpodder.net.")
                return

            with database.transaction():
                # Update the podcasts urls
                for old_url, new_url in result.update_urls:
                    if new_url:
                        self.logger.debug("Updating url '%s' to '%s'.",
                                          old_url, new_url)
                        (Podcast
                         .update(url=new_url)
                         .where(Podcast.url == old_url)
                         .on_conflict("REPLACE")
                         .execute())

                # Remove the actions
                for action in add:
                    action.delete_instance()
                for action in remove:
                    action.delete_instance()

            return result.since

        return None

    def synchronize_subscriptions(self):
        """Synchronize the subscriptions changes with gpodder.net."""
        if not self.enabled():
            return

        self.pull_subscriptions()
        since = self.push_subscriptions()

        if since is not None:
            Config.set_value("gpodder.last_subscription_sync", since)

    def process_episode_actions(self, actions):
        """Process the episodes actions.

        Parameters
        ----------
        actions : list of :class:`EpisodeAction` and :class:`RemoteEpisodeAction`
            A list containing all the local and remote episode actions.
        since : int
            The time at which the remote actions were pulled.
        """
        actions.sort(key=lambda a: a.time)

        with database.transaction():
            for action in actions:
                try:
                    self.process_episode_action(action)
                except Exception:  # pylint: disable=broad-except
                    self.logger.exception("Unable to process action %s",
                                          action)

    def process_episode_action(self, action):
        """Process an episode action."""
        if action.action == "play":
            if action.position + self.smart_mark_seconds >= action.total:
                (Episode
                 .update(played=True, progress=0)
                 .where(Episode.file_url == action.episode_url)
                 .execute())
            else:
                (Episode
                 .update(progress=action.position)
                 .where(Episode.file_url == action.episode_url)
                 .execute())
        elif action.action == "new":
            (Episode
             .update(played=False)
             .where(Episode.file_url == action.episode_url)
             .execute())

    def pull_episode_actions(self):
        """Pull episode actions from gpodder.net."""
        if not self.enabled():
            return

        self.logger.debug("Pulling episode actions.")

        try:
            changes = self.client.download_episode_actions(
                self.configuration.last_episodes_sync)
        except Exception:  # pylint: disable=broad-except
            self.logger.exception("Unable to pull episode actions from "
                                  "gpodder.net.")
            return

        local_actions = [action for action in EpisodeAction.select()]
        remote_actions = [RemoteEpisodeAction(action)
                          for action in changes.actions]
        self.process_episode_actions(local_actions + remote_actions)

        Config.set_value("gpodder.last_episodes_sync", changes.since)

    def push_episode_actions(self):
        """Push episode actions to gpodder.net."""
        if not self.enabled():
            return

        self.logger.debug("Pushing episode actions.")

        actions = [action for action in EpisodeAction.select()]

        try:
            since = self.client.upload_episode_actions(
                [action.for_gpodder() for action in actions])
        except Exception:  # pylint: disable=broad-except
            self.logger.exception("Unable to push episode actions to "
                                  "gpodder.net.")
            return

        # Remove actions
        with database.transaction():
            for action in actions:
                action.delete_instance()

        return since

    def synchronize_episode_actions(self):
        """Synchronize episode actions with gpodder.net."""
        if not self.enabled():
            return

        self.pull_episode_actions()
        since = self.push_episode_actions()

        if since is not None:
            Config.set_value("gpodder.last_episodes_sync", since)
