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
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk

from podcasts.frontend.main_window import MainWindow
from podcasts.frontend import preferences
from podcasts.library import Library
from podcasts.opml import import_opml, export_opml
from podcasts import gpodder


class Application(Gtk.Application):
    """
    Signals
    -------
    network-state-changed(online, error)
        Emitted when the network state changes
    """
    __gsignals__ = {
        'network-state-changed':
            (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_BOOLEAN, GObject.TYPE_BOOLEAN)),
    }

    def __init__(self, *args, **kwargs):
        Gtk.Application.__init__(self, application_id="fr.muges.podcasts",
                                 flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

        self.logger = logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__))

        self.window = None
        self.syncing = False
        self.online = True

        self.add_main_option("offline", ord("o"), GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, "Enable offline mode", None)

    def do_startup(self):
        Gtk.Application.do_startup(self)

        self.add_podcast_action = Gio.SimpleAction.new("add-podcast", None)
        self.add_podcast_action.connect("activate", lambda a, p: self.add_podcast())
        self.add_action(self.add_podcast_action)

        action = Gio.SimpleAction.new("import-opml", None)
        action.connect("activate", lambda a, p: self.import_opml())
        self.add_action(action)

        action = Gio.SimpleAction.new("export-opml", None)
        action.connect("activate", lambda a, p: self.export_opml())
        self.add_action(action)

        self.update_action = Gio.SimpleAction.new("update", None)
        self.update_action.connect("activate", lambda a, p: self.synchronize_library())
        self.add_action(self.update_action)

        self.sync_action = Gio.SimpleAction.new("force-synchronization", None)
        self.sync_action.connect("activate", lambda a, p: self.force_synchronization())
        self.add_action(self.sync_action)

        action = Gio.SimpleAction.new("preferences", None)
        action.connect("activate", lambda a, p: preferences.run(self.window))
        self.add_action(action)

        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", lambda a, p: self.quit())
        self.add_action(action)
        self.add_accelerator("<Primary>q", "app.quit", None)

        if self.prefers_app_menu():
            builder = Gtk.Builder.new_from_file("data/menu.ui")
            self.set_app_menu(builder.get_object("app-menu"))

    def do_activate(self):
        if not self.window:
            try:
                self.window = MainWindow(self)
            except BaseException:
                self.logger.exception("Unable to create main window.")
                self.quit()
                return

            self.set_network_state(self.online)

            library = Library()
            interval = library.get_config("library.synchronize_interval")

            self.synchronize_library(scan=True)
            GObject.timeout_add_seconds(interval*60, self.synchronize_library)

        self.window.present()

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()

        if options.contains("offline"):
            self.logger.info("Started in offline mode.")
            self.online = False

        self.activate()
        return 0

    def do_shutdown(self):
        if self.window:
            self.window.close()

        self.synchronize_library(update=False)

        Gtk.Application.do_shutdown(self)

    def force_synchronization(self):
        """
        Synchronize the podcasts library with gpodder.net, taking into account
        every episode action and every subscriptions changes.
        """
        library = Library()
        library.set_config("gpodder.last_subscription_sync", "0")
        library.set_config("gpodder.last_episodes_sync", "0")

        self.synchronize_library()

    def synchronize_library(self, update=True, scan=False):
        """
        Synchronize the podcasts library with gpodder.net.
        """
        # Prevent concurrent synchronizations
        if self.syncing or not self.online:
            return

        # Test connection
        if not gpodder.check_connection():
            self.set_network_state(False, error=True)
            return

        self.syncing = True

        if self.window:
            message_id = self.window.statusbox.add("Synchronizing subscriptions...")
        else:
            message_id = None

        def _update():
            if self.window and message_id:
                self.window.statusbox.edit(message_id, "Updating library...")

        def _synchronize():
            if self.window and message_id:
                self.window.statusbox.edit(message_id, "Synchronizing episode actions...")

        def _end():
            if self.window:
                if message_id:
                    self.window.statusbox.remove(message_id)

                self.window.podcast_list.update()
                self.window.episode_list.update()
                self.window.update_counts()

            self.syncing = False

        def _thread():
            # TODO : handle errors
            if update:
                gpodder.synchronize_subscriptions()

                GObject.idle_add(_update)
                library = Library()
                library.update_podcasts()
                if scan:
                    library.scan()

                GObject.idle_add(_synchronize)
                gpodder.synchronize_episode_actions()
            else:
                gpodder.upload_subscriptions()

                GObject.idle_add(_synchronize)
                gpodder.upload_episode_actions()

            GObject.idle_add(_end)

        thread = threading.Thread(target=_thread)
        thread.start()

        return True

    def add_podcast(self):
        """
        Add a new podcast.
        """
        # Open the "Add a podcast" dialog
        builder = Gtk.Builder.new_from_file("data/add_podcast.ui")
        dialog = builder.get_object("add_dialog")
        url_entry = builder.get_object("url_entry")

        if self.window:
            dialog.set_transient_for(self.window)

        response = dialog.run()
        url = url_entry.get_text()
        dialog.destroy()

        if response != Gtk.ResponseType.OK or not url:
            return

        if self.window:
            message_id = self.window.statusbox.add("Adding podcast...")
        else:
            message_id = None

        def _end():
            if self.window:
                if message_id:
                    self.window.statusbox.remove(message_id)

                self.window.podcast_list.update()
                self.window.episode_list.update()
                self.window.update_counts()

        def _add(url):
            # TODO : handle errors
            library = Library()
            library.add_source("rss", url)

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

        if self.window:
            message_id = self.window.statusbox.add("Importing OPML...")
        else:
            message_id = None

        def _end():
            if self.window:
                if message_id:
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

        if self.window:
            message_id = self.window.statusbox.add("Exporting OPML...")
        else:
            message_id = None

        def _end():
            if self.window and message_id:
                self.window.statusbox.remove(message_id)

        def _export(filename):
            export_opml(filename)

            GObject.idle_add(_end)

        thread = threading.Thread(target=_export, args=(filename,))
        thread.start()

    def _on_import_opml(self, action, param):
        if self.window:
            self.window.import_opml()

    def _on_export_opml(self, action, param):
        if self.window:
            self.window.export_opml()

    def set_network_state(self, online=True, error=False):
        if online and not error:
            error = not gpodder.check_connection()
        if error:
            online = False

        self.online = online

        self.add_podcast_action.set_enabled(online)
        self.update_action.set_enabled(online)
        self.sync_action.set_enabled(online)

        self.emit('network-state-changed', online, error)

    def get_online(self):
        return self.online
