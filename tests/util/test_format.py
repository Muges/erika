# -*- coding : utf-8 -*-

import pytest

from podcasts.util.format import format_duration, format_fulltext_duration, format_size


@pytest.mark.parametrize("duration_int, duration_str", [
    # Seconds
    (0, "0:00"),
    (13, "0:13"),
    (59, "0:59"),

    # Minutes
    (60, "1:00"),
    (60 + 17, "1:17"),
    (60 + 59, "1:59"),
    (2*60, "2:00"),
    (10*60 + 25, "10:25"),
    (10*60 + 35, "10:35"),
    (59*60 + 59, "59:59"),

    # Hours
    (3600, "1:00:00"),
    (3600 + 60, "1:01:00"),
    (3600 + 60 + 10, "1:01:10"),
    (2*3600 + 11*60 + 10, "2:11:10"),
    (3*3600 + 11*60 + 10, "3:11:10"),
    (11*3600 + 11*60 + 10, "11:11:10"),
])
def test_format_duration(duration_int, duration_str):
    """Tests for format_duration"""
    assert format_duration(duration_int) == duration_str


@pytest.mark.parametrize("duration_int, duration_str", [
    # Seconds
    (0, "0 seconds"),
    (13, "13 seconds"),
    (59, "59 seconds"),

    # Minutes
    (60, "1 minutes, 0 seconds"),
    (60 + 17, "1 minutes, 17 seconds"),
    (60 + 59, "1 minutes, 59 seconds"),
    (2*60, "2 minutes, 0 seconds"),
    (10*60 + 25, "10 minutes"),
    (10*60 + 35, "11 minutes"),
    (59*60 + 59, "60 minutes"),

    # Hours
    (3600, "1 hours, 0 minutes"),
    (3600 + 60, "1 hours, 1 minutes"),
    (3600 + 60 + 10, "1 hours, 1 minutes"),
    (2*3600 + 11*60 + 10, "2 hours, 11 minutes"),
    (3*3600 + 11*60 + 10, "3 hours"),
    (11*3600 + 11*60 + 10, "11 hours"),
])
def test_fulltext_format_duration(duration_int, duration_str):
    """Tests for format_fulltext_duration"""
    assert format_fulltext_duration(duration_int) == duration_str

@pytest.mark.parametrize("size_int, size_str", [
    # Bytes
    (0, "0.00 bytes"),
    (1, "1.00 bytes"),
    (2, "2.00 bytes"),
    (534, "534.00 bytes"),
    (1023, "1023.00 bytes"),

    # Kilobytes
    (1024, "1.00 kB"),
    (2.25*1024, "2.25 kB"),
    (1023*1024, "1023.00 kB"),

    # Megabytes
    (1024*1024, "1.00 MB"),
    (2.25*1024*1024, "2.25 MB"),
    (1023*1024*1024, "1023.00 MB"),

    # Gigabytes
    (1024*1024*1024, "1.00 GB"),
    (2.25*1024*1024*1024, "2.25 GB"),
    (1023*1024*1024*1024, "1023.00 GB"),

    # More
    (1024*1024*1024*1024, "1024.00 GB"),
    (2*1024*1024*1024*1024, "2048.00 GB"),
])
def test_format_size(size_int, size_str):
    """Tests for format_size"""
    assert format_size(size_int) == size_str
