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
Module handling the conversion of html into pango markup.
"""

# TODO : more tags
# TODO : inline css
# TODO : titles

import logging
from io import StringIO
import re
import lxml.etree
import lxml.html

from gi.repository import GLib

BLOCKS = ["p", "br", "div"]
BLOCK_PREFIX = {
    "p": "  "
}
BLOCK_SUFFIX = {
}
INLINE = ["span", "em", "strong", "img"]
TAG_STYLES = {
    "em": {"style": "italic"},
    "strong": {"weight": "bold"}
}


def strip_url(url):
    if not url:
        return ""

    if url.startswith("http://"):
        url = url[7:]
    elif url.startswith("https://"):
        url = url[8:]

    if url.startswith("www."):
        url = url[4:]

    return url


class Parser(object):
    def __init__(self):
        self.logger = logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__))

        self.text = ""
        self.link_counter = 1
        self.links = []

    def clear(self):
        """
        Reinitialize the parser.
        """
        self.text = ""
        self.link_counter = 1
        self.links = []

    def parse_string(self, html):
        """
        Parse a html string

        Parameters
        ----------
        html : str
            A html formatted string

        Returns
        -------
        str
            A string formatted with pango markup
        """
        self.clear()

        fragments = lxml.html.fragments_fromstring(html)

        if not fragments:
            return ""

        # Add the trailing text
        if isinstance(fragments[0], str):
            text = fragments.pop(0)

            if fragments:
                text = re.sub("\s+", " ", text)

            self._add_text(text)

        for node in fragments:
            self._parse_node(node)

        return self.get_text()

    def _parse_node(self, node):
        """
        Parse a html node.

        Parameters
        ----------
        node : lxml.html.HtmlElement
            The current node.
        """
        is_block = node.tag in BLOCKS
        is_inline = node.tag in INLINE
        is_link = node.tag == "a"

        style = {}

        try:
            style.update(TAG_STYLES[node.tag])
        except KeyError:
            pass

        if not (is_block or is_inline or is_link):
            self.logger.warning("Unknown tag '%s'.", node.tag)

        if style:
            self._add_span(style)

        if is_block:
            self._add_text(BLOCK_PREFIX.get(node.tag, ""))

        # Handle node's text
        if node.text:
            text = re.sub("\s+", " ", node.text)
            if is_block:
                if len(node):
                    text = text.lstrip()
                else:
                    text = text.strip()
            self._add_text(text)

        # Parse children
        for child in node.iterchildren():
            self._parse_node(child)

        if is_link:
            href = node.get("href")
            if not href:
                self.logger.debug("Met a link without href attribute.")
            elif strip_url(href) == strip_url(node.text):
                pass
            elif href in self.links:
                self._add_text(" [{}]".format(self.links.index(href) + 1))
            else:
                self._add_text(" [{}]".format(self.link_counter))
                self.link_counter += 1
                self.links.append(href)

        if style:
            self._close_span()

        if is_block:
            self._rstrip_text()
            self._add_text(BLOCK_SUFFIX.get(node.tag, "\n"))

        # Handle node's tail
        if node.tail:
            tail = re.sub("\s+", " ", node.tail)
            self._add_text(tail)

    def get_text(self):
        """
        Return the converted string.

        Returns
        -------
        str
            A string formatted with pango markup
        """
        if self.links:
            return (
                self.text + "\n\n" +
                "\n".join("[{}] {}".format(i+1, GLib.markup_escape_text(link))
                          for i, link in enumerate(self.links))
            )
        else:
            return self.text

    def _add_text(self, text):
        """
        Add text at the end of the output string.

        Special characters will be escaped before adding the text.
        """
        try:
            if self.text[-1] == " " and text[0] == " ":
                text = text.rstrip()
        except IndexError:
            pass
        self.text += GLib.markup_escape_text(text)

    def _rstrip_text(self):
        """
        Remove whitespaces at the end of the output string.
        """
        self.text = self.text.rstrip(" \t\n")

    def _add_span(self, attrs):
        """
        Add a span at the end of the output string.

        Parameters
        ----------
        attrs : Dict[str, str]
            A dictionnary containing the attributes of the span.
        """
        self.text += "<span{}>".format(
            "".join(" {}=\"{}\"".format(k, v) for k, v in attrs.items())
        )

    def _close_span(self):
        """
        Close a span at the end of the output string.
        """
        self.text += "</span>"


def convert(html):
    """
    Convert html into pango markup

    Parameters
    ----------
    html : str
        A html formatted string

    Returns
    -------
    str
        A string formatted with pango markup
    """
    if html == None:
        return ""

    parser = Parser()
    return parser.parse_string(html)
