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
Module handling the conversion of html into plaintext
"""

import logging
import re
import lxml.etree
import lxml.html

BLOCKS = ["p", "br", "div", "h1", "h2", "h3", "h4", "h5", "h6"]
BLOCK_SUFFIX = {
    "br": "\n"
}


class Parser(object):
    """Parser converting html into plaintext"""
    def __init__(self):
        self.logger = logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__))

        self.text = ""

    def clear(self):
        """Reinitialize the parser"""
        self.text = ""

    def parse_string(self, html):
        """Parse an html string

        Parameters
        ----------
        html : str
            A html formatted string
        """
        self.clear()

        parser = lxml.etree.HTMLParser(remove_blank_text=True,
                                       remove_comments=True,
                                       remove_pis=True)
        fragments = lxml.html.fragments_fromstring(html, parser=parser)

        if not fragments:
            return ""

        # Add the trailing text
        if isinstance(fragments[0], str):
            text = fragments.pop(0)

            if fragments:
                text = re.sub(r"\s+", " ", text)

            self._add_text(text)

        for node in fragments:
            self._parse_node(node)

        return self.get_text()

    def _parse_node(self, node):
        """Parse an html node

        Parameters
        ----------
        node : lxml.html.HtmlElement
            The current node.
        """
        is_block = node.tag in BLOCKS

        # Handle node's text
        if node.text:
            text = re.sub(r"\s+", " ", node.text)
            if is_block:
                if len(node):  # pylint: disable=len-as-condition
                    text = text.lstrip()
                else:
                    text = text.strip()
            self._add_text(text)

        # Parse children
        for child in node.iterchildren():
            self._parse_node(child)

        if is_block:
            self._rstrip_text()
            self._add_text(BLOCK_SUFFIX.get(node.tag, "\n\n"))

        # Handle node's tail
        if node.tail:
            tail = re.sub(r"\s+", " ", node.tail)
            if is_block:
                tail = tail.strip()
            self._add_text(tail)

    def get_text(self):
        """Return the converted string"""
        return self.text.rstrip(" \t\n")

    def _add_text(self, text):
        """Add text at the end of the output string"""
        try:
            if self.text[-1] == " " and text[0] == " ":
                text = text.rstrip()
        except IndexError:
            pass
        self.text += text

    def _rstrip_text(self):
        """Remove whitespaces at the end of the output string"""
        self.text = self.text.rstrip(" \t\n")


def html_to_plaintext(html):
    """Convert html into plaintext

    Parameters
    ----------
    html : str
        A html formatted string
    """
    if not html:
        return ""

    parser = Parser()
    return parser.parse_string(html)
