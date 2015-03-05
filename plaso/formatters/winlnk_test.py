#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows Shortcut (LNK) event formatter."""

import unittest

from plaso.formatters import winlnk


class WinLnkLinkFormatterTest(unittest.TestCase):
  """Tests for the Windows Shortcut (LNK) event formatter."""

  def testInitialization(self):
    """Test the initialization."""
    event_formatter = winlnk.WinLnkLinkFormatter()
    self.assertNotEquals(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = winlnk.WinLnkLinkFormatter()

    expected_attribute_names = sorted([
        u'description', u'file_size', u'file_attribute_flags', u'drive_type',
        u'drive_serial_number', u'volume_label', u'local_path',
        u'network_path', u'command_line_arguments', u'env_var_location',
        u'relative_path', u'working_directory', u'icon_location',
        u'link_target'])

    attribute_names = event_formatter.GetFormatStringAttributeNames()
    self.assertEqual(sorted(attribute_names), expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()