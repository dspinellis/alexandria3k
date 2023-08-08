#
# Alexandria3k Patent grant bibliographic metadata processing
# Copyright (C) 2023  Aggelos Margkas
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
"""Test of caching read and parsed XML files"""

import unittest
from xml.etree import ElementTree as ET

from .test_dir import add_src_dir

add_src_dir()

from alexandria3k.file_xml_cache import FileCache


class TestFileCache(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Create a new FileCache instance before each test
        self.file_cache = FileCache()
        FileCache.parse_counter = 0

    def test_read_cached_data(self):
        # Test reading cached data
        xml_chunk = "<patent><title>Test Patent</title></patent>"
        container_id = 1

        # Set the cache data manually
        self.file_cache.cached_data = ET.fromstring(xml_chunk)
        self.file_cache.cached_patent_xml_id = container_id
        self.file_cache.parse_counter = 1

        # Call the read method with the same container_id
        result = self.file_cache.read(xml_chunk, container_id)

        # Assert that the returned data is the cached data
        self.assertEqual(result, self.file_cache.cached_data)
        # Assert that no parsing took place
        self.assertEqual(self.file_cache.parse_counter, 1)

        self.file_cache.parse_counter = 0


class TestFileCache(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Create a new FileCache instance before each test
        self.file_cache = FileCache()
        FileCache.parse_counter = 0

    def test_read_new_data(self):
        # Test reading and parsing new data
        xml_chunk_old = "<patent><title>Test Patent Old</title></patent>"
        container_id_old = 1

        xml_chunk_new = "<patent><title>Test Patent New</title></patent>"
        container_id_new = 2

        # Call the read method for the first patent and container_id
        result = self.file_cache.read(xml_chunk_old, container_id_old)

        # Call the read method with the second patent and container_id
        result = self.file_cache.read(xml_chunk_new, container_id_new)

        # Assert that the returned data is the parsed data from xml_chunk_new
        # Asserts strings, because object obtain different id in memory.
        self.assertEqual(
            ET.tostring(result, encoding="unicode"),
            xml_chunk_new,
        )

        # Assert that parsing took place
        self.assertEqual(FileCache.parse_counter, 2)

        self.file_cache.parse_counter = 0


class TestFileCache(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Create a new FileCache instance before each test
        self.file_cache = FileCache()
        FileCache.parse_counter = 0

    def test_cached_data(self):
        # Test that parse_counter increments when new data is read
        xml_chunk = "<patent><title>Test Patent</title></patent>"
        container_id = 1

        # Call the read method with a new patent and container_id
        self.file_cache.read(xml_chunk, container_id)

        # Assert that parse_counter is incremented after parsing
        self.assertEqual(self.file_cache.parse_counter, 1)

        # Call the read method with the same patent and container_id
        self.file_cache.read(xml_chunk, container_id)

        # Assert that parse_counter remains the same
        self.assertEqual(self.file_cache.parse_counter, 1)

        self.file_cache.parse_counter = 0
