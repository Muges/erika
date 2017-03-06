# -*- coding : utf-8 -*-

import string
import pytest  #pylint: disable=unused-import

from podcasts.library.models.database import slugify


def test_slugify():
    # Lowercase alphanumeric strings
    assert slugify("") == ""
    assert slugify("abcdef") == "abcdef"
    assert slugify("abc123") == "abc123"
    assert slugify("abc123") == "abc123"
    assert slugify(string.ascii_lowercase) == string.ascii_lowercase
    assert slugify(string.digits) == string.digits

    # Alphanumeric strings
    assert slugify("aAbBcCdD1") == "aabbccdd1"
    assert slugify(string.ascii_uppercase) == string.ascii_lowercase

    # Non-alphanumeric strings
    assert slugify("abc-def") == "abcdef"
    assert slugify("Abc.D1f") == "abcd1f"
    assert slugify("Abc D1f") == "abcd1f"
    assert slugify(string.punctuation) == ""
    assert slugify(string.whitespace) == ""
