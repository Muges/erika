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


class String(object):
    @staticmethod
    def read(value):
        return value

    @staticmethod
    def write(value):
        return value

    @staticmethod
    def read_widget(widget):
        return widget.get_text()

    @staticmethod
    def write_widget(widget, value):
        widget.set_text(value)

class Path(String):
    @staticmethod
    def read_widget(widget):
        return widget.get_filename()

    @staticmethod
    def write_widget(widget, value):
        widget.set_filename(value)

class Integer(object):
    @staticmethod
    def read(value):
        return int(value)

    @staticmethod
    def write(value):
        return str(value)

    @staticmethod
    def read_widget(widget):
        return int(widget.get_value())

    @staticmethod
    def write_widget(widget, value):
        widget.set_value(value)

class Boolean(object):
    @staticmethod
    def read(value):
        return value == "true"

    @staticmethod
    def write(value):
        if value:
            return "true"
        else:
            return "false"

    @staticmethod
    def read_widget(widget):
        return widget.get_active()

    @staticmethod
    def write_widget(widget, value):
        widget.set_active(value)
