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
Button displaying the list downloads and their progress
"""

import logging

from gi.repository import GdkPixbuf
from gi.repository import GObject
from gi.repository import Gtk

from podcasts.downloads import DownloadsPool, download_with_average_speed
from podcasts.library import Library
from podcasts.util import format_fulltext_duration, format_size
from podcasts.frontend.widgets import Label

# Size of the episode icon in the download list
IMAGE_SIZE = 64

# Size of the downloads popover
POPOVER_WIDTH = 500
POPOVER_HEIGHT = 400


class DownloadsButton(Gtk.MenuButton):
    """
    Button displaying the list of downloads.
    """
    def __init__(self):
        super().__init__()

        self.logger = logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__))

        self.pool = DownloadsPool()

        self.set_image(Gtk.Image.new_from_icon_name(
            "document-save-symbolic", Gtk.IconSize.BUTTON))

        self.popover = Gtk.Popover()

        self.list = Gtk.ListBox()
        self.list.show()
        self.list.set_selection_mode(Gtk.SelectionMode.NONE)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add_with_viewport(self.list)
        scrolled_window.show_all()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_size_request(POPOVER_WIDTH, 0)
        try:
            scrolled_window.set_max_content_height(POPOVER_HEIGHT)
        except AttributeError:
            self.logger.warning(
                "Gtk.ScrolledWindow.set_max_content_height is not available, "
                "using set_size_request.")
            scrolled_window.set_size_request(POPOVER_WIDTH, POPOVER_HEIGHT)
        self.popover.add(scrolled_window)

        self.set_popover(self.popover)

    def download(self, episode):
        """
        Add an episode to the download queue.
        """
        job = DownloadJob(episode)

        row = DownloadRow(job)
        self.list.add(row)

        self.pool.add(job)

    def stop(self):
        """
        Cancel all the downloads.
        """
        self.pool.stop()


class DownloadRow(Gtk.ListBoxRow):
    """
    Row in the download list
    """
    def __init__(self, job):
        super().__init__()

        self.job = job
        self.job.connect("start", self._on_start)
        self.job.connect("progress", self._on_progress)
        self.job.connect("remove", self._on_remove)

        # Layout
        self.grid = Gtk.Grid()
        self.grid.set_column_spacing(5)
        self.add(self.grid)

        self.icon = Gtk.Image()
        self.grid.attach(self.icon, 0, 0, 1, 3)

        self.title = Label()
        self.title.set_hexpand(True)
        self.grid.attach(self.title, 1, 0, 1, 1)

        self.progress = Gtk.ProgressBar()
        self.progress.set_valign(Gtk.Align.CENTER)
        self.grid.attach(self.progress, 1, 1, 1, 1)

        self.progress_label = Label()
        self.grid.attach(self.progress_label, 1, 2, 1, 1)

        button = Gtk.Button.new_from_icon_name("edit-delete-symbolic",
                                               Gtk.IconSize.BUTTON)
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.connect('clicked', self._on_cancel_clicked)
        self.grid.attach(button, 2, 0, 1, 3)

        self.show_all()

        self.set_pending()

    def _on_start(self, job):
        """
        Update the widget to show that the download is starting.
        """
        self.progress_label.set_text("Starting...")

    def _on_progress(self, job, currentsize, totalsize, speed):
        """
        Update the widget to show the current download progress.
        """
        try:
            remaining_time = int(round((totalsize-currentsize)/speed))
        except ZeroDivisionError:
            remaining_time = None

        self.progress.set_fraction(currentsize/totalsize)
        if remaining_time is None:
            self.progress_label.set_text("{} of {} ({}/s)".format(
                format_size(currentsize), format_size(totalsize),
                format_size(speed)
            ))
        else:
            self.progress_label.set_text(
                "{} - {} of {} ({}/s)".format(
                    format_fulltext_duration(remaining_time),
                    format_size(currentsize), format_size(totalsize),
                    format_size(speed)
                ))

    def _on_remove(self, job):
        """
        Remove the download from the list.
        """
        self.destroy()

    def set_pending(self):
        """
        Update the widget to show the download is pending.
        """
        if self.job.podcast.image_data:
            self.icon.show()
            self.icon.set_from_pixbuf(self.get_pixbuf())
        else:
            self.icon.hide()

        self.title.set_markup(
            "{} - <i>{}</i>".format(self.job.episode.title,
                                    self.job.podcast.title))

        self.progress_label.set_text("Pending...")

    def get_pixbuf(self):
        """
        Return the image of the podcast as a scaled pixbuf
        """
        loader = GdkPixbuf.PixbufLoader.new()
        loader.write(self.job.podcast.image_data)
        pixbuf = loader.get_pixbuf()
        loader.close()

        return pixbuf.scale_simple(IMAGE_SIZE, IMAGE_SIZE,
                                   GdkPixbuf.InterpType.BILINEAR)

    def _on_cancel_clicked(self, button):
        """
        Called when the cancel button is clicked.
        """
        self.job.cancel()


class DownloadJob(GObject.Object):
    """
    Download job that should be added to a DownloadsPool.

    Signals
    -------
    start
        Emitted when the download starts.
    remove
        Emitted when the download should be removed from the list (e.g. removed
        or canceled).
    progress(current_size, total_size, speed)
        Emitted during the download to report its progress.
    """

    __gsignals__ = {
        'start':
            (GObject.SIGNAL_RUN_FIRST, None, ()),
        'remove':
            (GObject.SIGNAL_RUN_FIRST, None, ()),
        'progress':
            (GObject.SIGNAL_RUN_FIRST, None, (int, int, float)),
    }

    def __init__(self, episode):
        GObject.Object.__init__(self)

        library = Library()
        self.podcast = library.get_podcast(episode)
        self.episode = episode
        self.canceled = False

    def cancel(self):
        """
        Cancel the download.
        """
        self.canceled = True
        GObject.idle_add(self.emit, "remove")

    def start(self):
        """
        Start the download
        """
        GObject.idle_add(self.emit, "start")

        generator = download_with_average_speed(self.podcast, self.episode)

        for current_size, file_size, average_speed in generator:
            if self.canceled:
                generator.close()
                break

            GObject.idle_add(self.emit, "progress", current_size, file_size,
                             average_speed)

        GObject.idle_add(self.emit, "remove")