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
A Gtk.Label with sane defaults
"""

from gi.repository import Gtk
from gi.repository import Pango


class Label(Gtk.Label):
    """A Gtk.Label with sane defaults

    Creates a label aligned to the left, ellipsized at the end, and with
    optional line wrapping.

    Parameters
    ----------
    lines : Optional[int]
        If lines is set to an integer greater than 1, enable wrapping and limit
        the number of lines that should be displayed.
    """
    def __init__(self, lines=1):
        super().__init__()

        self.set_alignment(xalign=0, yalign=0.5)
        self.set_ellipsize(Pango.EllipsizeMode.END)

        if lines > 1:
            self.set_line_wrap(True)
            self.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            self.set_lines(lines)
