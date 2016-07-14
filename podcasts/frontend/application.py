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

from gi.repository import Gio
from gi.repository import Gtk

from podcasts.frontend.main_window import MainWindow


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        Gtk.Application.__init__(self, application_id="fr.muges.podcasts")

        self.logger = logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__))

        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)

        action = Gio.SimpleAction.new("update", None)
        action.connect("activate", self._on_update_library)
        self.add_action(action)

        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self._on_quit)
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

        self.window.present()

    def _on_quit(self, action, param):
        self.quit()

    def _on_update_library(self, action, param):
        if self.window:
            self.window.update_library()
