#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Android SMS call history plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import android_calls as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import android_calls

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class AndroidCallSQLitePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Android Call History database plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['contacts2.db'])
  def testProcess(self):
    """Test the Process function on an Android contacts2.db file."""
    plugin = android_calls.AndroidCallPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['contacts2.db'], plugin)

    # The contacts2 database file contains 5 events (MISSED/OUTGOING/INCOMING).
    self.assertEqual(storage_writer.number_of_events, 5)

    events = list(storage_writer.GetEvents())

    # Check the first event.
    event = events[0]

    self.assertEqual(event.timestamp_desc, 'Call Started')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-11-06 21:17:16.690')
    self.assertEqual(event.timestamp, expected_timestamp)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-11-06 21:17:16.690')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_number = '5404561685'
    self.assertEqual(event.number, expected_number)

    expected_type = 'MISSED'
    self.assertEqual(event.call_type, expected_type)

    expected_message = (
        'MISSED '
        'Number: 5404561685 '
        'Name: Barney '
        'Duration: 0 seconds')
    expected_short_message = 'MISSED Call'
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Run some tests on the last 2 events.
    event_3 = events[3]
    event_4 = events[4]

    # Check the timestamp_desc of the last event.
    self.assertEqual(event_4.timestamp_desc, 'Call Ended')

    expected_timestamp3 = timelib.Timestamp.CopyFromString(
        '2013-11-07 00:03:36.690')
    self.assertEqual(event_3.timestamp, expected_timestamp3)

    expected_timestamp4 = timelib.Timestamp.CopyFromString(
        '2013-11-07 00:14:15.690')
    self.assertEqual(event_4.timestamp, expected_timestamp4)

    # Ensure the difference in btw. events 3 and 4 equals the duration.
    expected_duration, _ = divmod(
        expected_timestamp4 - expected_timestamp3, 1000000)
    self.assertEqual(event_4.duration, expected_duration)


if __name__ == '__main__':
  unittest.main()
