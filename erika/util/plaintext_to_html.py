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
Module handling the conversion of plaintext into html
"""

import html
import re
import string

SPACES_PATTERN = re.compile(r"[ \t]+")
NEWLINE_PATTERN = re.compile(r"[ \t]*\n[ \t]*")
PARAGRAPH_PATTERN = re.compile(r"[ \t]*\n[ \t]*\n[ \t]*")
URL_PATTERN = re.compile(
    # Protocol
    r"(http|ftp|https)://"
    # Domain
    r"([\w_-]+(?:(?:\.[\w_-]+)+))"
    # Path
    r"([\w.,@?^=%&:;/~+#-]*[\w@?^=%&/~+#-])?"
)


def paragraph_to_html(paragraph):
    """Convert a paragraph to html"""
    paragraph = paragraph.strip(string.whitespace)
    paragraph = html.escape(paragraph)

    # Line breaks
    paragraph = NEWLINE_PATTERN.sub("<br/>\n", paragraph)

    # Spaces
    paragraph = SPACES_PATTERN.sub(" ", paragraph)

    # Urls
    paragraph = URL_PATTERN.sub(r'<a href="\g<0>">\g<0></a>', paragraph)

    return "<p>{}</p>".format(paragraph)


def plaintext_to_html(plaintext):
    """Convert a text to html"""
    paragraphs = PARAGRAPH_PATTERN.split(plaintext)

    return "\n".join([
        paragraph_to_html(paragraph)
        for paragraph in paragraphs
        if not PARAGRAPH_PATTERN.match(paragraph)
    ])
