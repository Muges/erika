# -*- coding : utf-8 -*-

import string
import pytest

from podcasts.library.models.database import slugify


@pytest.mark.parametrize("name, slug", [
    # Lowercase alphanumeric strings
    ("", ""),
    ("abcdef", "abcdef"),
    ("abc123", "abc123"),
    ("abc123", "abc123"),
    (string.ascii_lowercase, string.ascii_lowercase),
    (string.digits, string.digits),

    # Alphanumeric strings
    ("aAbBcCdD1", "aabbccdd1"),
    (string.ascii_uppercase, string.ascii_lowercase),

    # Non-alphanumeric strings
    ("abc-def", "abcdef"),
    ("Abc.D1f", "abcd1f"),
    ("Abc D1f", "abcd1f"),
    (string.punctuation, ""),
    (string.whitespace, ""),
])
def test_slugify(name, slug):
    """Test for slugify"""
    assert slugify(name) == slug
