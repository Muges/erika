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
import threading
import pkg_resources
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk

from erika import library
from erika.library.models import Config, Episode, Podcast
from erika.library.opml import import_opml, export_opml
from erika.library.gpodder import GPodderClient, GPodderUnauthorized
from erika.util import check_connection
from . import preferences
from .main_window import MainWindow
from .util import cb, get_builder


class Application(Gtk.Application):
    """
    Signals
    -------
    network-state-changed(online, error)
        Emitted when the network state changes
    """
    __gsignals__ = {
        'network-state-changed':
            (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_BOOLEAN,
                                              GObject.TYPE_BOOLEAN)),
    }

    def __init__(self):
        Gtk.Application.__init__(
            self, application_id="fr.muges.erika",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

        self.logger = logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__))

        self.window = None
        self.online = True
        self.synchronization_lock = threading.Lock()

        self.add_main_option("offline", ord("o"), GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, "Enable offline mode", None)

        self.connect("startup", cb(self._on_startup))
        self.connect("activate", cb(self._on_activate))
        self.connect("command-line", cb(self._on_command_line))
        self.connect("shutdown", cb(self.close_main_window))
        self.connect("shutdown", cb(self._on_shutdown))

    def _on_startup(self):
        """Called when the first instance of the application is launched"""
        # pylint: disable=attribute-defined-outside-init

        Gtk.Application.do_startup(self)

        # Creates the actions
        self.add_podcast_action = Gio.SimpleAction.new("add-podcast", None)
        self.add_podcast_action.connect("activate", cb(self.add_podcast, 2))
        self.add_action(self.add_podcast_action)

        action = Gio.SimpleAction.new("import-opml", None)
        action.connect("activate", cb(self.import_opml, 2))
        self.add_action(action)

        action = Gio.SimpleAction.new("export-opml", None)
        action.connect("activate", cb(self.export_opml, 2))
        self.add_action(action)

        self.update_action = Gio.SimpleAction.new("update", None)
        self.update_action.connect("activate", cb(self.synchronize_library, 2))
        self.add_action(self.update_action)

        self.sync_action = Gio.SimpleAction.new("force-synchronization", None)
        self.sync_action.connect("activate", cb(self.force_synchronization, 2))
        self.add_action(self.sync_action)

        action = Gio.SimpleAction.new("preferences", None)
        action.connect("activate", cb(preferences.run, 2), self.window)
        self.add_action(action)

        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", cb(self.quit, 2))
        self.add_action(action)
        self.add_accelerator("<Primary>q", "app.quit", None)

        if self.prefers_app_menu():
            # Create the menu
            builder = get_builder('data/menu.glade')
            self.set_app_menu(builder.get_object("app-menu"))

        # Load custom icons
        icons_path = pkg_resources.resource_filename(
            'erika.frontend', 'data/icons')
        icon_theme = Gtk.IconTheme.get_default()
        icon_theme.append_search_path(icons_path)

        # Set windows icons
        Gtk.Window.set_default_icon_name('erika')

        try:
            self.window = MainWindow(self)
        except BaseException:
            self.logger.exception("Unable to create main window.")

    def _on_activate(self):
        """Called when the application is launched"""
        if self.window is None:
            self.quit()
            return

        self.set_network_state(self.online)

        interval = Config.get_value("library.synchronize_interval")

        self.synchronize_library(scan=True)
        GObject.timeout_add_seconds(interval * 60, self.synchronize_library)

        self.window.show_all()
        self.window.present()

    def _on_command_line(self, command_line):
        """Called when the application is launched from the command line"""
        options = command_line.get_options_dict()

        if options.contains("offline"):
            self.logger.info("Started in offline mode.")
            self.online = False

        self.activate()
        return 0

    def _on_shutdown(self):
        """Called when the application is closed"""
        if self.window is None:
            return

        self.close_main_window()

        Episode.update(new=False).execute()
        self.synchronize_library(update=False)

        Gtk.Application.do_shutdown(self)

    def _synchronization_end(self, message_id):
        """Called at the end of the synchronization"""
        self.window.statusbox.remove(message_id)

        self.window.podcast_list.update()
        self.window.episode_list.update()
        self.window.update_counts()

    def _synchronization_thread(self, message_id, update=True, scan=False):
        acquired = self.synchronization_lock.acquire(blocking=False)
        if not acquired:
            # There is already another synchronization thread running : abort
            return

        try:
            client = GPodderClient()

            if not self.online:
                return

            # Check internet connection
            hostname = Config.get_value("network.connection_check_hostname")
            if not check_connection(hostname):
                self.set_network_state(False, error=True)
                return

            GObject.idle_add(self.window.statusbox.add,
                             "Synchronizing subscriptions...", message_id)

            try:
                client.connect()
            except GPodderUnauthorized:
                self.window.error_label.set_text(
                    'Unable to connect to gpodder: invalid credentials.')
                self.window.error_bar.show()
            except Exception:
                self.window.error_label.set_text(
                    'Unable to connect to gpodder.')
                self.window.error_bar.show()
            else:
                self.window.error_bar.hide()

            client.synchronize_subscriptions()

            if update:
                GObject.idle_add(self.window.statusbox.edit,
                                 message_id, "Updating library...")

                for podcast in Podcast.select():
                    podcast.update_podcast()
                    GObject.idle_add(
                        self.window.podcast_list.update_podcast, podcast)

            if update and scan:
                GObject.idle_add(self.window.statusbox.edit,
                                 message_id, "Scanning library...")
                library.scan()

            GObject.idle_add(self.window.statusbox.edit,
                             message_id, "Synchronizing episode actions...")
            if update:
                client.synchronize_episode_actions()
            else:
                client.push_episode_actions()
        finally:
            GObject.idle_add(self._synchronization_end, message_id)
            self.synchronization_lock.release()

    def synchronize_library(self, update=True, scan=False):
        """Synchronize the podcasts library with gpodder.net"""
        message_id = self.window.statusbox.get_next_message_id()

        thread = threading.Thread(target=self._synchronization_thread,
                                  args=(message_id, update, scan))
        thread.start()

        return True

    def force_synchronization(self):
        """Synchronize the podcasts library with gpodder.net, taking into
        account every episode action and every subscriptions changes"""
        Config.set_value("gpodder.last_subscription_sync", "0")
        Config.set_value("gpodder.last_episodes_sync", "0")

        self.synchronize_library()

    def add_podcast(self):
        """
        Add a new podcast.
        """
        # Open the "Add a podcast" dialog
        builder = get_builder('data/add_podcast.glade')
        dialog = builder.get_object("add_dialog")
        url_entry = builder.get_object("url_entry")

        dialog.set_transient_for(self.window)

        response = dialog.run()
        url = url_entry.get_text()
        dialog.destroy()

        if response != Gtk.ResponseType.OK or not url:
            return

        message_id = self.window.statusbox.get_next_message_id()
        self.window.statusbox.add("Adding podcast...", message_id)

        def _end():
            self.window.statusbox.remove(message_id)

            self.window.podcast_list.update()
            self.window.episode_list.update()
            self.window.update_counts()

        def _add(url):
            # TODO : handle errors
            podcast = Podcast.new("rss", url)
            podcast.update_podcast()

            GObject.idle_add(_end)

        thread = threading.Thread(target=_add, args=(url,))
        thread.start()

    def import_opml(self):
        """
        Import the podcasts subscriptions from an OPML file.
        """
        dialog = Gtk.FileChooserDialog(
            "Import OPML file", self.window,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        # Add filters
        filter_xml = Gtk.FileFilter()
        filter_xml.set_name("XML files")
        filter_xml.add_mime_type("text/xml")
        dialog.add_filter(filter_xml)

        filter_text = Gtk.FileFilter()
        filter_text.set_name("Text files")
        filter_text.add_mime_type("text/plain")
        dialog.add_filter(filter_text)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
        elif response == Gtk.ResponseType.CANCEL:
            filename = None
        dialog.destroy()

        if not filename:
            return

        message_id = self.window.statusbox.get_next_message_id()
        self.window.statusbox.add("Importing OPML...", message_id)

        def _end():
            self.window.statusbox.remove(message_id)

            self.window.podcast_list.update()
            self.window.episode_list.update()
            self.window.update_counts()

        def _import(filename):
            # TODO : handle errors
            import_opml(filename)

            GObject.idle_add(_end)

        thread = threading.Thread(target=_import, args=(filename,))
        thread.start()

    def export_opml(self):
        """
        Export the podcasts subscriptions in an OPML file.
        """
        dialog = Gtk.FileChooserDialog(
            "Export OPML file", self.window,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.OK))

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
        elif response == Gtk.ResponseType.CANCEL:
            filename = None
        dialog.destroy()

        if not filename:
            return

        message_id = self.window.statusbox.get_next_message_id()
        self.window.statusbox.add("Exporting OPML...", message_id)

        def _end():
            self.window.statusbox.remove(message_id)

        def _export(filename):
            export_opml(filename)

            GObject.idle_add(_end)

        thread = threading.Thread(target=_export, args=(filename,))
        thread.start()

    def set_network_state(self, online=True, error=False):
        if online and not error:
            hostname = Config.get_value("network.connection_check_hostname")
            error = not check_connection(hostname)
        if error:
            online = False

        self.online = online

        self.add_podcast_action.set_enabled(online)
        self.update_action.set_enabled(online)
        self.sync_action.set_enabled(online)

        self.emit('network-state-changed', online, error)

    def get_online(self):
        """Return True if the application is connected to the internet"""
        return self.online

    def close_main_window(self):
        if self.window is not None:
            self.window.destroy()
