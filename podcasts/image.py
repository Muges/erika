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
Object representing an image.
"""

import base64
import imghdr
from PIL import Image as PImage
from io import BytesIO

from gi.repository import GdkPixbuf


class Image(object):
    """
    Object representing an image.
    """
    def __init__(self, data):
        self.data = data
        self.image = PImage.open(BytesIO(self.data))

    def get_data(self, size=None):
        """
        Return an array of bytes containing the image in png format.

        Parameters
        ----------
        size : Optional[int]
            The size of the image, or None to keep the original size.
        """
        if size:
            image = self.image.resize(
                (size, size * self.image.height // self.image.width),
                PImage.LANCZOS)
        else:
            image = self.image

        data = BytesIO()
        image.save(data, format='PNG')
        return data.getvalue()

    def as_pixbuf(self, size=None):
        """
        Return the GdkPixbuf.Pixbuf corresponding to the image.

        Parameters
        ----------
        size : Optional[int]
            The size of the pixbuf, or None to keep the original size.
        """
        loader = GdkPixbuf.PixbufLoader.new_with_mime_type("image/png")
        loader.write(self.get_data(size))
        pixbuf = loader.get_pixbuf()
        loader.close()

        return pixbuf

    def __format__(self, spec=None):
        """
        Return the data uri corresponding to the image.

        Parameters
        ----------
        spec : Optional[str]
            The size of the image, or None to keep the original size.
        """
        if spec:
            size = int(spec)
        else:
            size = None

        return "data:image/png;base64,{}".format(
            base64.b64encode(self.get_data(size)).decode())
