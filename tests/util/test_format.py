# -*- coding : utf-8 -*-

import pytest  #pylint: disable=unused-import

from podcasts.util.format import format_duration, format_fulltext_duration, format_size


def test_format_duration():
    # Seconds
    assert format_duration(0) == "0:00"
    assert format_duration(13) == "0:13"
    assert format_duration(59) == "0:59"

    # Minutes
    assert format_duration(60) == "1:00"
    assert format_duration(60 + 17) == "1:17"
    assert format_duration(60 + 59) == "1:59"
    assert format_duration(2*60) == "2:00"
    assert format_duration(10*60 + 25) == "10:25"
    assert format_duration(10*60 + 35) == "10:35"
    assert format_duration(59*60 + 59) == "59:59"

    # Hours
    assert format_duration(3600) == "1:00:00"
    assert format_duration(3600 + 60) == "1:01:00"
    assert format_duration(3600 + 60 + 10) == "1:01:10"
    assert format_duration(2*3600 + 11*60 + 10) == "2:11:10"
    assert format_duration(3*3600 + 11*60 + 10) == "3:11:10"
    assert format_duration(11*3600 + 11*60 + 10) == "11:11:10"


def test_fulltext_format_duration():
    # Seconds
    assert format_fulltext_duration(0) == "0 seconds"
    assert format_fulltext_duration(13) == "13 seconds"
    assert format_fulltext_duration(59) == "59 seconds"

    # Minutes
    assert format_fulltext_duration(60) == "1 minutes, 0 seconds"
    assert format_fulltext_duration(60 + 17) == "1 minutes, 17 seconds"
    assert format_fulltext_duration(60 + 59) == "1 minutes, 59 seconds"
    assert format_fulltext_duration(2*60) == "2 minutes, 0 seconds"
    assert format_fulltext_duration(10*60 + 25) == "10 minutes"
    assert format_fulltext_duration(10*60 + 35) == "11 minutes"
    assert format_fulltext_duration(59*60 + 59) == "60 minutes"

    # Hours
    assert format_fulltext_duration(3600) == "1 hours, 0 minutes"
    assert format_fulltext_duration(3600 + 60) == "1 hours, 1 minutes"
    assert format_fulltext_duration(3600 + 60 + 10) == "1 hours, 1 minutes"
    assert format_fulltext_duration(2*3600 + 11*60 + 10) == "2 hours, 11 minutes"
    assert format_fulltext_duration(3*3600 + 11*60 + 10) == "3 hours"
    assert format_fulltext_duration(11*3600 + 11*60 + 10) == "11 hours"


def test_format_size():
    # Bytes
    assert format_size(0) == "0.00 bytes"
    assert format_size(1) == "1.00 bytes"
    assert format_size(2) == "2.00 bytes"
    assert format_size(534) == "534.00 bytes"
    assert format_size(1023) == "1023.00 bytes"

    # Kilobytes
    assert format_size(1024) == "1.00 kB"
    assert format_size(2.25*1024) == "2.25 kB"
    assert format_size(1023*1024) == "1023.00 kB"

    # Megabytes
    assert format_size(1024*1024) == "1.00 MB"
    assert format_size(2.25*1024*1024) == "2.25 MB"
    assert format_size(1023*1024*1024) == "1023.00 MB"

    # Gigabytes
    assert format_size(1024*1024*1024) == "1.00 GB"
    assert format_size(2.25*1024*1024*1024) == "2.25 GB"
    assert format_size(1023*1024*1024*1024) == "1023.00 GB"

    # More
    assert format_size(1024*1024*1024*1024) == "1024.00 GB"
    assert format_size(2*1024*1024*1024*1024) == "2048.00 GB"
