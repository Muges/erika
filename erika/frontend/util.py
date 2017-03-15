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
Frontend utility functions
"""

import pkgutil
from gi.repository import Gtk


def cb(function, n=1):  # pylint: disable=invalid-name
    """Create a callback whose first n argument are ignored

    Returns a function whose first n arguments are ignored, and which returns
    the result of the function passed in parameters :
    cb(f)(ignored, *args) == f(*args)
    cb(f, 2)(i1, i2, *args) == f(*args)
    """
    return lambda *args: function(*args[n:])


def get_builder(filename):
    """Create a Gtk.Builder from a package data file"""
    data = pkgutil.get_data('erika.frontend', filename).decode('utf-8')
    return Gtk.Builder.new_from_string(data, -1)
