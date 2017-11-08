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
A field used to store an image.
"""

import base64
from io import BytesIO
from PIL import Image as PImage
from peewee import BlobField

from gi.repository import GdkPixbuf


class ImageField(BlobField):
    """A field used to store an image."""
    def db_value(self, image):
        return image.data

    def python_value(self, data):
        return Image(data)


class Image(object):
    """
    Object representing an image.

    If an Image is used in a format string, it will be returned as a data uri,
    making it possible to embed it in html as follow::

        '<img src="{image}" />'.format(image=image)
    """
    def __init__(self, data):
        self.data = data

    def __bool__(self):
        return self.data is not None

    def get_data(self, width=None):
        """
        Return a byte sequence containing the image in png format.

        Parameters
        ----------
        width : int, optional
            The width of the image, or None to keep the original width.
        """
        if self.data:
            image = PImage.open(BytesIO(self.data))
        else:
            image = PImage.new('RGBA', (1, 1), (0, 0, 0, 0))

        if width:
            image = image.resize(
                (width, width * image.height // image.width),
                PImage.LANCZOS)

        data = BytesIO()
        image.save(data, format='PNG')
        return data.getvalue()

    def as_pixbuf(self, width=None):
        """
        Return the image as :class:`GdkPixbuf.Pixbuf`.

        Parameters
        ----------
        width : int, optional
            The width of the pixbuf, or None to keep the original width.
        """
        loader = GdkPixbuf.PixbufLoader.new_with_mime_type("image/png")
        loader.write(self.get_data(width))
        loader.close()
        pixbuf = loader.get_pixbuf()

        return pixbuf

    def __format__(self, spec=None):
        """
        Return the data uri corresponding to the image.

        Parameters
        ----------
        spec : str, optional
            The width of the image, or None to keep the original width.
        """
        if spec:
            width = int(spec)
        else:
            width = None

        return "data:image/png;base64,{}".format(
            base64.b64encode(self.get_data(width)).decode())
