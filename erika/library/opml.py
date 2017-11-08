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
The :mod:`erika.library.opml` module provides functions to import and export
opml files.
"""

from email.utils import formatdate
from lxml import etree

from .models import Podcast


def import_opml(filename):
    """
    Import podcasts subscriptions from an opml file.

    Parameters
    ----------
    filename : str
        The opml file.
    """
    document = etree.parse(filename)

    for outline in document.xpath("/opml/body/outline"):
        Podcast.new(outline.get("type", "rss"), outline.get("xmlUrl"))


def export_opml(filename):
    """
    Export the podcasts subscriptions to an opml file.

    Parameters
    ----------
    filename : str
        The opml file.
    """
    root = etree.Element('opml')
    document = etree.ElementTree(root)

    # Head
    head = etree.SubElement(root, 'head')

    title = etree.SubElement(head, 'title')
    title.text = "Podcasts subscriptions"

    date = etree.SubElement(head, 'dateCreated')
    date.text = formatdate()

    # Body
    body = etree.SubElement(root, 'body')

    for podcast in Podcast.select():
        etree.SubElement(body, 'outline',
                         text=podcast.title,
                         title=podcast.title,
                         type=podcast.parser,
                         xmlUrl=podcast.url,
                         htmlUrl=podcast.link)

    document.write(filename, xml_declaration=True, encoding='utf-8',
                   pretty_print=True)
