#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Windows Registry plugin to parse the Application Compatibility Cache key."""

import construct
import logging

from plaso.events import time_events
from plaso.lib import binary
from plaso.lib import eventdata
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class AppCompatCacheEvent(time_events.FiletimeEvent):
  """Class that contains the event object for AppCompatCache entries."""

  DATA_TYPE = 'windows:registry:appcompatcache'

  def __init__(
      self, filetime, usage, key, entry_index, path, offset):
    """Initializes a Windows Registry event.

    Args:
      filetime: The FILETIME timestamp value.
      usage: The description of the usage of the time value.
      key: Name of the Registry key being parsed.
      entry_index: The cache entry index number for the record.
      path: The full path to the executable.
      offset: The (data) offset of the Registry key or value.
    """
    super(AppCompatCacheEvent, self).__init__(filetime, usage)

    self.keyname = key
    self.offset = offset
    self.entry_index = entry_index
    self.path = path


class AppCompatCacheHeader(object):
  """Class that contains the Application Compatibility Cache header."""

  def __init__(self):
    """Initializes the header object."""
    super(AppCompatCacheHeader, self).__init__()
    self.number_of_cached_entries = 0
    self.header_size = 0


class AppCompatCacheCachedEntry(object):
  """Class that contains the Application Compatibility Cache cached entry."""

  def __init__(self):
    """Initializes the cached entry object."""
    super(AppCompatCacheCachedEntry, self).__init__()
    self.cached_entry_size = 0
    self.data = None
    self.file_size = None
    self.insertion_flags = None
    self.last_modification_time = None
    self.last_update_time = None
    self.shim_flags = None
    self.path = None


class AppCompatCachePlugin(interface.KeyPlugin):
  """Class that parses the Application Compatibility Cache Registry key."""

  NAME = 'winreg_appcompatcache'

  REG_KEYS = [
      u'\\{current_control_set}\\Control\\Session Manager\\AppCompatibility',
      u'\\{current_control_set}\\Control\\Session Manager\\AppCompatCache']
  REG_TYPE = 'SYSTEM'
  DESCRIPTION = 'Application Compatibility Cache Registry key'
  URL = [
      (u'https://code.google.com/p/winreg-kb/wiki/'
       u'ApplicationCompatibilityCacheKey')]

  _FORMAT_TYPE_2000 = 1
  _FORMAT_TYPE_XP = 2
  _FORMAT_TYPE_2003 = 3
  _FORMAT_TYPE_VISTA = 4
  _FORMAT_TYPE_7 = 5
  _FORMAT_TYPE_8 = 6

  # AppCompatCache format signature used in Windows XP.
  _HEADER_SIGNATURE_XP = 0xdeadbeef

  # AppCompatCache format used in Windows XP.
  _HEADER_XP_32BIT_STRUCT = construct.Struct(
      'appcompatcache_header_xp',
      construct.ULInt32('signature'),
      construct.ULInt32('number_of_cached_entries'),
      construct.ULInt32('unknown1'),
      construct.ULInt32('unknown2'),
      construct.Padding(384))

  _CACHED_ENTRY_XP_32BIT_STRUCT = construct.Struct(
      'appcompatcache_cached_entry_xp_32bit',
      construct.Array(528, construct.Byte('path')),
      construct.ULInt64('last_modification_time'),
      construct.ULInt64('file_size'),
      construct.ULInt64('last_update_time'))

  # AppCompatCache format signature used in Windows 2003, Vista and 2008.
  _HEADER_SIGNATURE_2003 = 0xbadc0ffe

  # AppCompatCache format used in Windows 2003.
  _HEADER_2003_STRUCT = construct.Struct(
      'appcompatcache_header_2003',
      construct.ULInt32('signature'),
      construct.ULInt32('number_of_cached_entries'))

  _CACHED_ENTRY_2003_32BIT_STRUCT = construct.Struct(
      'appcompatcache_cached_entry_2003_32bit',
      construct.ULInt16('path_size'),
      construct.ULInt16('maximum_path_size'),
      construct.ULInt32('path_offset'),
      construct.ULInt64('last_modification_time'),
      construct.ULInt64('file_size'))

  _CACHED_ENTRY_2003_64BIT_STRUCT = construct.Struct(
      'appcompatcache_cached_entry_2003_64bit',
      construct.ULInt16('path_size'),
      construct.ULInt16('maximum_path_size'),
      construct.ULInt32('unknown1'),
      construct.ULInt64('path_offset'),
      construct.ULInt64('last_modification_time'),
      construct.ULInt64('file_size'))

  # AppCompatCache format used in Windows Vista and 2008.
  _CACHED_ENTRY_VISTA_32BIT_STRUCT = construct.Struct(
      'appcompatcache_cached_entry_vista_32bit',
      construct.ULInt16('path_size'),
      construct.ULInt16('maximum_path_size'),
      construct.ULInt32('path_offset'),
      construct.ULInt64('last_modification_time'),
      construct.ULInt32('insertion_flags'),
      construct.ULInt32('shim_flags'))

  _CACHED_ENTRY_VISTA_64BIT_STRUCT = construct.Struct(
      'appcompatcache_cached_entry_vista_64bit',
      construct.ULInt16('path_size'),
      construct.ULInt16('maximum_path_size'),
      construct.ULInt32('unknown1'),
      construct.ULInt64('path_offset'),
      construct.ULInt64('last_modification_time'),
      construct.ULInt32('insertion_flags'),
      construct.ULInt32('shim_flags'))

  # AppCompatCache format signature used in Windows 7 and 2008 R2.
  _HEADER_SIGNATURE_7 = 0xbadc0fee

  # AppCompatCache format used in Windows 7 and 2008 R2.
  _HEADER_7_STRUCT = construct.Struct(
      'appcompatcache_header_7',
      construct.ULInt32('signature'),
      construct.ULInt32('number_of_cached_entries'),
      construct.Padding(120))

  _CACHED_ENTRY_7_32BIT_STRUCT = construct.Struct(
      'appcompatcache_cached_entry_7_32bit',
      construct.ULInt16('path_size'),
      construct.ULInt16('maximum_path_size'),
      construct.ULInt32('path_offset'),
      construct.ULInt64('last_modification_time'),
      construct.ULInt32('insertion_flags'),
      construct.ULInt32('shim_flags'),
      construct.ULInt32('data_size'),
      construct.ULInt32('data_offset'))

  _CACHED_ENTRY_7_64BIT_STRUCT = construct.Struct(
      'appcompatcache_cached_entry_7_64bit',
      construct.ULInt16('path_size'),
      construct.ULInt16('maximum_path_size'),
      construct.ULInt32('unknown1'),
      construct.ULInt64('path_offset'),
      construct.ULInt64('last_modification_time'),
      construct.ULInt32('insertion_flags'),
      construct.ULInt32('shim_flags'),
      construct.ULInt64('data_size'),
      construct.ULInt64('data_offset'))

  # AppCompatCache format used in Windows 8.0 and 8.1.
  _HEADER_SIGNATURE_8 = 0x00000080

  _HEADER_8_STRUCT = construct.Struct(
      'appcompatcache_header_8',
      construct.ULInt32('signature'),
      construct.Padding(124))

  _CACHED_ENTRY_HEADER_8_STRUCT = construct.Struct(
      'appcompatcache_cached_entry_header_8',
      construct.ULInt32('signature'),
      construct.ULInt32('unknown1'),
      construct.ULInt32('cached_entry_data_size'),
      construct.ULInt16('path_size'))

  # AppCompatCache format used in Windows 8.0.
  _CACHED_ENTRY_SIGNATURE_8_0 = '00ts'

  # AppCompatCache format used in Windows 8.1.
  _CACHED_ENTRY_SIGNATURE_8_1 = '10ts'

  def _CheckSignature(self, value_data):
    """Parses and validates the signature.

    Args:
      value_data: a binary string containing the value data.

    Returns:
      The format type if successful or None otherwise.
    """
    signature = construct.ULInt32('signature').parse(value_data)
    if signature == self._HEADER_SIGNATURE_XP:
      return self._FORMAT_TYPE_XP

    elif signature == self._HEADER_SIGNATURE_2003:
      # TODO: determine which format version is used (2003 or Vista).
      return self._FORMAT_TYPE_2003

    elif signature == self._HEADER_SIGNATURE_7:
      return self._FORMAT_TYPE_7

    elif signature == self._HEADER_SIGNATURE_8:
      if value_data[signature:signature + 4] in [
          self._CACHED_ENTRY_SIGNATURE_8_0, self._CACHED_ENTRY_SIGNATURE_8_1]:
        return self._FORMAT_TYPE_8

  def _DetermineCacheEntrySize(
      self, format_type, value_data, cached_entry_offset):
    """Determines the size of a cached entry.

    Args:
      format_type: integer value that contains the format type.
      value_data: a binary string containing the value data.
      cached_entry_offset: integer value that contains the offset of
                           the first cached entry data relative to the start of
                           the value data.

    Returns:
      The cached entry size if successful or None otherwise.

    Raises:
      RuntimeError: if the format type is not supported.
    """
    if format_type not in [
        self._FORMAT_TYPE_XP, self._FORMAT_TYPE_2003, self._FORMAT_TYPE_VISTA,
        self._FORMAT_TYPE_7, self._FORMAT_TYPE_8]:
      raise RuntimeError(
          u'[{0:s}] Unsupported format type: {1:d}'.format(
              self.NAME, format_type))

    cached_entry_data = value_data[cached_entry_offset:]
    cached_entry_size = 0

    if format_type == self._FORMAT_TYPE_XP:
      cached_entry_size = self._CACHED_ENTRY_XP_32BIT_STRUCT.sizeof()

    elif format_type in [
        self._FORMAT_TYPE_2003, self._FORMAT_TYPE_VISTA, self._FORMAT_TYPE_7]:
      path_size = construct.ULInt16('path_size').parse(cached_entry_data[0:2])
      maximum_path_size = construct.ULInt16('maximum_path_size').parse(
          cached_entry_data[2:4])
      path_offset_32bit = construct.ULInt32('path_offset').parse(
          cached_entry_data[4:8])
      path_offset_64bit = construct.ULInt32('path_offset').parse(
          cached_entry_data[8:16])

      if maximum_path_size < path_size:
        logging.error(
            u'[{0:s}] Path size value out of bounds.'.format(self.NAME))
        return

      path_end_of_string_size = maximum_path_size - path_size
      if path_size == 0 or path_end_of_string_size != 2:
        logging.error(
            u'[{0:s}] Unsupported path size values.'.format(self.NAME))
        return

      # Assume the entry is 64-bit if the 32-bit path offset is 0 and
      # the 64-bit path offset is set.
      if path_offset_32bit == 0 and path_offset_64bit != 0:
        if format_type == self._FORMAT_TYPE_2003:
          cached_entry_size = self._CACHED_ENTRY_2003_64BIT_STRUCT.sizeof()
        elif format_type == self._FORMAT_TYPE_VISTA:
          cached_entry_size = self._CACHED_ENTRY_VISTA_64BIT_STRUCT.sizeof()
        elif format_type == self._FORMAT_TYPE_7:
          cached_entry_size = self._CACHED_ENTRY_7_64BIT_STRUCT.sizeof()

      else:
        if format_type == self._FORMAT_TYPE_2003:
          cached_entry_size = self._CACHED_ENTRY_2003_32BIT_STRUCT.sizeof()
        elif format_type == self._FORMAT_TYPE_VISTA:
          cached_entry_size = self._CACHED_ENTRY_VISTA_32BIT_STRUCT.sizeof()
        elif format_type == self._FORMAT_TYPE_7:
          cached_entry_size = self._CACHED_ENTRY_7_32BIT_STRUCT.sizeof()

    elif format_type == self._FORMAT_TYPE_8:
      cached_entry_size = self._CACHED_ENTRY_HEADER_8_STRUCT.sizeof()

    return cached_entry_size

  def _ParseHeader(self, format_type, value_data):
    """Parses the header.

    Args:
      format_type: integer value that contains the format type.
      value_data: a binary string containing the value data.

    Returns:
      A header object (instance of AppCompatCacheHeader).

    Raises:
      RuntimeError: if the format type is not supported.
    """
    if format_type not in [
        self._FORMAT_TYPE_XP, self._FORMAT_TYPE_2003, self._FORMAT_TYPE_VISTA,
        self._FORMAT_TYPE_7, self._FORMAT_TYPE_8]:
      raise RuntimeError(
          u'[{0:s}] Unsupported format type: {1:d}'.format(
              self.NAME, format_type))

    # TODO: change to collections.namedtuple or use __slots__ if the overhead
    # of a regular object becomes a problem.
    header_object = AppCompatCacheHeader()

    if format_type == self._FORMAT_TYPE_XP:
      header_object.header_size = self._HEADER_XP_32BIT_STRUCT.sizeof()
      header_struct = self._HEADER_XP_32BIT_STRUCT.parse(value_data)

    elif format_type == self._FORMAT_TYPE_2003:
      header_object.header_size = self._HEADER_2003_STRUCT.sizeof()
      header_struct = self._HEADER_2003_STRUCT.parse(value_data)

    elif format_type == self._FORMAT_TYPE_VISTA:
      header_object.header_size = self._HEADER_VISTA_STRUCT.sizeof()
      header_struct = self._HEADER_VISTA_STRUCT.parse(value_data)

    elif format_type == self._FORMAT_TYPE_7:
      header_object.header_size = self._HEADER_7_STRUCT.sizeof()
      header_struct = self._HEADER_7_STRUCT.parse(value_data)

    elif format_type == self._FORMAT_TYPE_8:
      header_object.header_size = self._HEADER_8_STRUCT.sizeof()
      header_struct = self._HEADER_8_STRUCT.parse(value_data)

    if format_type in [
        self._FORMAT_TYPE_XP, self._FORMAT_TYPE_2003, self._FORMAT_TYPE_VISTA,
        self._FORMAT_TYPE_7]:
      header_object.number_of_cached_entries = header_struct.get(
          'number_of_cached_entries')

    return header_object

  def _ParseCachedEntry(
      self, format_type, value_data, cached_entry_offset, cached_entry_size):
    """Parses a cached entry.

    Args:
      format_type: integer value that contains the format type.
      value_data: a binary string containing the value data.
      cached_entry_offset: integer value that contains the offset of
                           the cached entry data relative to the start of
                           the value data.
      cached_entry_size: integer value that contains the cached entry data size.

    Returns:
      A cached entry object (instance of AppCompatCacheCachedEntry).

    Raises:
      RuntimeError: if the format type is not supported.
    """
    if format_type not in [
        self._FORMAT_TYPE_XP, self._FORMAT_TYPE_2003, self._FORMAT_TYPE_VISTA,
        self._FORMAT_TYPE_7, self._FORMAT_TYPE_8]:
      raise RuntimeError(
          u'[{0:s}] Unsupported format type: {1:d}'.format(
              self.NAME, format_type))

    cached_entry_data = value_data[
        cached_entry_offset:cached_entry_offset + cached_entry_size]

    cached_entry_struct = None

    if format_type == self._FORMAT_TYPE_XP:
      if cached_entry_size == self._CACHED_ENTRY_XP_32BIT_STRUCT.sizeof():
        cached_entry_struct = self._CACHED_ENTRY_XP_32BIT_STRUCT.parse(
            cached_entry_data)

    elif format_type == self._FORMAT_TYPE_2003:
      if cached_entry_size == self._CACHED_ENTRY_2003_32BIT_STRUCT.sizeof():
        cached_entry_struct = self._CACHED_ENTRY_2003_32BIT_STRUCT.parse(
          cached_entry_data)

      elif cached_entry_size == self._CACHED_ENTRY_2003_64BIT_STRUCT.sizeof():
        cached_entry_struct = self._CACHED_ENTRY_2003_64BIT_STRUCT.parse(
            cached_entry_data)

    elif format_type == self._FORMAT_TYPE_VISTA:
      if cached_entry_size == self._CACHED_ENTRY_VISTA_32BIT_STRUCT.sizeof():
        cached_entry_struct = self._CACHED_ENTRY_VISTA_32BIT_STRUCT.parse(
          cached_entry_data)

      elif cached_entry_size == self._CACHED_ENTRY_VISTA_64BIT_STRUCT.sizeof():
        cached_entry_struct = self._CACHED_ENTRY_VISTA_64BIT_STRUCT.parse(
            cached_entry_data)

    elif format_type == self._FORMAT_TYPE_7:
      if cached_entry_size == self._CACHED_ENTRY_7_32BIT_STRUCT.sizeof():
        cached_entry_struct = self._CACHED_ENTRY_7_32BIT_STRUCT.parse(
            cached_entry_data)

      elif cached_entry_size == self._CACHED_ENTRY_7_64BIT_STRUCT.sizeof():
        cached_entry_struct = self._CACHED_ENTRY_7_64BIT_STRUCT.parse(
            cached_entry_data)

    elif format_type == self._FORMAT_TYPE_8:
      if cached_entry_data[0:4] not in [
          self._CACHED_ENTRY_SIGNATURE_8_0, self._CACHED_ENTRY_SIGNATURE_8_1]:
        raise RuntimeError(
            u'[{0:s}] Unsupported cache entry signature'.format(self.NAME))

      if cached_entry_size == self._CACHED_ENTRY_HEADER_8_STRUCT.sizeof():
        cached_entry_struct = self._CACHED_ENTRY_HEADER_8_STRUCT.parse(
            cached_entry_data)

        cached_entry_data_size = cached_entry_struct.get(
            'cached_entry_data_size')
        cached_entry_size = 12 + cached_entry_data_size

        cached_entry_data = value_data[
            cached_entry_offset:cached_entry_offset + cached_entry_size]

    if not cached_entry_struct:
      raise RuntimeError(
          u'[{0:s}] Unsupported cache entry size: {1:d}'.format(
              self.NAME, cached_entry_size))

    cached_entry_object = AppCompatCacheCachedEntry()
    cached_entry_object.cached_entry_size = cached_entry_size

    path_offset = 0
    data_size = 0

    if format_type == self._FORMAT_TYPE_XP:
      string_size = 0
      for string_index in xrange(0, 528, 2):
        if (ord(cached_entry_data[string_index]) == 0 and
            ord(cached_entry_data[string_index + 1]) == 0):
          break
        string_size += 2

      cached_entry_object.path = binary.Ut16StreamCopyToString(
          cached_entry_data[0:string_size])

    elif format_type in [
        self._FORMAT_TYPE_2003, self._FORMAT_TYPE_VISTA, self._FORMAT_TYPE_7]:
      path_size = cached_entry_struct.get('path_size')
      path_offset = cached_entry_struct.get('path_offset')

    elif format_type == self._FORMAT_TYPE_8:
      path_size = cached_entry_struct.get('path_size')

      cached_entry_data_offset = 14 + path_size
      cached_entry_object.path = binary.Ut16StreamCopyToString(
          cached_entry_data[14:cached_entry_data_offset])

      remaining_data = cached_entry_data[cached_entry_data_offset:]

      cached_entry_object.insertion_flags = construct.ULInt32(
          'insertion_flags').parse(remaining_data[0:4])
      cached_entry_object.shim_flags = construct.ULInt32(
          'shim_flags').parse(remaining_data[4:8])

      if cached_entry_data[0:4] == self._CACHED_ENTRY_SIGNATURE_8_0:
        cached_entry_data_offset += 8

      elif cached_entry_data[0:4] == self._CACHED_ENTRY_SIGNATURE_8_1:
        cached_entry_data_offset += 10

      remaining_data = cached_entry_data[cached_entry_data_offset:]

    if format_type in [
        self._FORMAT_TYPE_XP, self._FORMAT_TYPE_2003, self._FORMAT_TYPE_VISTA,
        self._FORMAT_TYPE_7]:
      cached_entry_object.last_modification_time = cached_entry_struct.get(
          'last_modification_time')

    elif format_type == self._FORMAT_TYPE_8:
      cached_entry_object.last_modification_time = construct.ULInt64(
         'last_modification_time').parse(remaining_data[0:8])

    if format_type in [self._FORMAT_TYPE_XP, self._FORMAT_TYPE_2003]:
      cached_entry_object.file_size = cached_entry_struct.get('file_size')

    elif format_type in [self._FORMAT_TYPE_VISTA, self._FORMAT_TYPE_7]:
      cached_entry_object.insertion_flags = cached_entry_struct.get(
          'insertion_flags')
      cached_entry_object.shim_flags = cached_entry_struct.get('shim_flags')

    if format_type == self._FORMAT_TYPE_XP:
      cached_entry_object.last_update_time = cached_entry_struct.get(
          'last_update_time')

    if format_type == self._FORMAT_TYPE_7:
      data_offset = cached_entry_struct.get('data_offset')
      data_size = cached_entry_struct.get('data_size')

    elif format_type == self._FORMAT_TYPE_8:
      data_offset = cached_entry_offset + cached_entry_data_offset + 12
      data_size = construct.ULInt32('data_size').parse(remaining_data[8:12])

    if path_offset > 0 and path_size > 0:
      path_size += path_offset

      cached_entry_object.path = binary.Ut16StreamCopyToString(
          value_data[path_offset:path_size])

    if data_size > 0:
      data_size += data_offset

      cached_entry_object.data = value_data[data_offset:data_size]

    return cached_entry_object

  def GetEntries(self, parser_context, key=None, **unused_kwargs):
    """Extracts event objects from a Application Compatibility Cache key.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
    """
    value = key.GetValue('AppCompatCache')
    if not value:
      return

    value_data = value.data
    value_data_size = len(value.data)

    format_type = self._CheckSignature(value_data)
    if not format_type:
      # TODO: Instead of logging emit a parser error object that once that
      # mechanism is implemented.
      logging.error(
          u'AppCompatCache format error: [{0:s}] Unsupported signature'.format(
              key.path))
      return

    header_object = self._ParseHeader(format_type, value_data)

    # On Windows Vista and 2008 when the cache is empty it will
    # only consist of the header.
    if value_data_size <= header_object.header_size:
      return

    cached_entry_offset = header_object.header_size
    cached_entry_size = self._DetermineCacheEntrySize(
        format_type, value_data, cached_entry_offset)

    if not cached_entry_size:
      # TODO: Instead of logging emit a parser error object that once that
      # mechanism is implemented.
      logging.error(
          u'AppCompatCache format error: [{0:s}] Unsupported cached entry '
          u'size.'.format(key.path))
      return

    cached_entry_index = 0
    while cached_entry_offset < value_data_size:
      cached_entry_object = self._ParseCachedEntry(
          format_type, value_data, cached_entry_offset, cached_entry_size)

      if cached_entry_object.last_modification_time is not None:
        # TODO: refactor to file modification event.
        event_object = AppCompatCacheEvent(
            cached_entry_object.last_modification_time,
            u'File Last Modification Time', key.path,
            cached_entry_index + 1, cached_entry_object.path,
            cached_entry_offset)
        parser_context.ProduceEvent(event_object, plugin_name=self.NAME)

      if cached_entry_object.last_update_time is not None:
        # TODO: refactor to process run event.
        event_object = AppCompatCacheEvent(
            cached_entry_object.last_update_time,
            eventdata.EventTimestamp.LAST_RUNTIME, key.path,
            cached_entry_index + 1, cached_entry_object.path,
            cached_entry_offset)
        parser_context.ProduceEvent(event_object, plugin_name=self.NAME)

      cached_entry_offset += cached_entry_object.cached_entry_size
      cached_entry_index += 1

      if (header_object.number_of_cached_entries != 0 and
          cached_entry_index >= header_object.number_of_cached_entries):
        break


winreg.WinRegistryParser.RegisterPlugin(AppCompatCachePlugin)
