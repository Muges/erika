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
The :mod:`erika.downloads` module provides a dowloading function with average
speed computation, as well as a :class:`DownloadPool` to implement parallel
downloading.
"""

import logging
import os
from queue import Queue, Empty
from threading import Thread
import time
import requests

from . import tags
from .library.models import Config, EpisodeAction
from .util import guess_extension

# Smoothing factor used to compute the average download speed
SMOOTHING_FACTOR = 0.01

# The time step used to compute the average download speed, in seconds
TIME_DELTA = 0.05


def download_chunks(episode):
    """Download an episode by chunks.

    Yields
    ------
    int, int
        The size of the previous chunk, and the total size of the file.
    """
    logger = logging.getLogger(__name__)

    # Start the download and get the mimetype of the file
    logger.debug("Getting file mimetype.")
    response = requests.get(episode.file_url, stream=True)
    mimetype = (
        response.headers.get('content-type') or episode.mimetype
    )
    try:
        file_size = int(response.headers.get('content-length'))
    except TypeError:
        file_size = None

    # Set the extension of the file
    ext = guess_extension(mimetype)

    filename = episode.get_default_filename(ext)
    tempfilename = filename + ".part"
    dirname = os.path.dirname(filename)

    # Create the podcast directory if necessary
    if not os.path.isdir(dirname):
        os.makedirs(dirname)

    logger.debug("Downloading to temporary file '%s'.", tempfilename)
    try:
        # Download to a temporary file
        with open(tempfilename, "wb") as fileobj:
            if file_size is None:
                fileobj.write(response.content)
            else:
                for data in response.iter_content(chunk_size=1024):
                    # Write the downloaded data to the temporary file
                    fileobj.write(data)
                    chunk_size = len(data)

                    yield (chunk_size, file_size)

        # Move the temporary file to the destination file
        os.rename(tempfilename, filename)

        # Set the tags of the downloaded file
        tags.set_tags(filename, episode)

        episode.local_path = filename
        episode.save()

        action = EpisodeAction(episode=episode, action="download")
        action.save()
    finally:
        # Remove the temporary file if it exists (if the download failed or was
        # canceled)
        if os.path.isfile(tempfilename):
            os.remove(tempfilename)


def download_with_average_speed(episode):
    """Download an episode by chunks, and compute the average speed (see
    https://en.wikipedia.org/wiki/Moving_average#Exponential_moving_average).

    Yields
    ------
    int, int, float
        - The current downloaded size in bytes;
        - the total file size in bytes;
        - the average downloading speed in bytes per second.
    """
    previous_time = time.time()  # Time of the previous step
    current_size = 0  # Total downloaded size
    step_size = 0  # Size downloaded during the current time step
    average_speed = 0  # Average download speed

    for chunk_size, file_size in download_chunks(episode):
        now = time.time()

        current_size += chunk_size
        step_size += chunk_size

        if now - previous_time >= TIME_DELTA:
            # Compute the average speed during current time step
            current_speed = step_size / (now - previous_time)

            # Compute the smoothed average download speed
            if average_speed == 0:
                average_speed = current_speed
            else:
                average_speed = (
                    SMOOTHING_FACTOR * current_speed +
                    (1 - SMOOTHING_FACTOR) * average_speed)

            yield (current_size, file_size, average_speed)

            step_size = 0
            previous_time = now


class DownloadsPool(object):
    """Download pool, handling the downloads queue and the workers to make
    concurrent downloads possible."""
    def __init__(self):
        self.queue = Queue()

        workers = Config.get_value("downloads.workers")

        self.workers = [
            DownloadWorker(self.queue) for _ in range(0, workers)
        ]

    def add(self, job):
        """Add a new job to the queue.

        A job should have :

        - a ``cancel`` method, which stops the job cleanly and as soon as
          possible;
        - a ``start`` method, which starts the job.

        See :class:`erika.frontend.downloads.DownloadJob` for an example.
        """
        self.queue.put(job)

    def stop(self):
        """Stop all the workers (and the jobs being currently executed)."""
        for worker in self.workers:
            worker.stop()


class DownloadWorker(Thread):
    """Thread waiting for jobs to be added to the queue and executing them."""
    def __init__(self, queue):
        Thread.__init__(self)

        self.logger = logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__))

        self.queue = queue
        self.stopped = False
        self.current_job = None

        self.start()

    def run(self):
        while not self.stopped:
            try:
                self.current_job = self.queue.get(timeout=1)
            except Empty:
                continue

            try:
                self.current_job.start()
            except Exception:  # pylint: disable=broad-except
                self.logger.exception("Download failed.")
            finally:
                self.current_job = None
                self.queue.task_done()

    def stop(self):
        """Stop the worker (and the job being currently executed)."""
        self.stopped = True
        if self.current_job:
            self.current_job.cancel()
            self.current_job = None
