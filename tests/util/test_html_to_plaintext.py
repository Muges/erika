# -*- coding : utf-8 -*-
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

import os
import glob
import pytest

from podcasts.util.html_to_plaintext import html_to_plaintext

DATA_DIRECTORY = "tests/util/data/html_to_plaintext"

PATTERN = os.path.join(DATA_DIRECTORY, "*.txt")
FILES = glob.glob(PATTERN)
NAMES = [os.path.splitext(path)[0] for path in FILES]

@pytest.mark.parametrize("filename", NAMES)
def test_html_to_plaintext(filename):
    with open(filename + ".txt") as fileobj:
        plaintext = fileobj.read().rstrip()
    with open(filename + ".html") as fileobj:
        html = fileobj.read()

    assert html_to_plaintext(html) == plaintext
