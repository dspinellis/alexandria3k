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
"""Test of decompressing/extracting Zip files of US patent office"""

import os
import unittest

from .test_dir import add_src_dir, td

add_src_dir()

from alexandria3k.uspto_zip_cache import UsptoZipCache

FILE_PATH = td("data/April 2023 Patent Grant Bibliographic Data")


class TestUsptoZipCache(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.file_path = []
        self.file_cache = UsptoZipCache()

        # Read through the directory
        for file_name in os.listdir(FILE_PATH):
            path = os.path.join(FILE_PATH, file_name)
            if not os.path.isfile(path):
                continue

            self.file_path.append(path)

    def test_read_cached_data(self):
        # Read the first zip file
        data_1 = self.file_cache.read(self.file_path[0])
        self.assertEqual(UsptoZipCache.file_reads, 1)

        # Read the same zip file again, data should be cached
        data_1_cached = self.file_cache.read(self.file_path[0])
        self.assertEqual(UsptoZipCache.file_reads, 1)
        self.assertEqual(data_1, data_1_cached)

    def test_read_new_data(self):
        # Read the first zip file
        data_2 = self.file_cache.read(self.file_path[0])
        self.assertEqual(UsptoZipCache.file_reads, 1)

        # Read the same zip file again, data should be cached
        data_2_cached = self.file_cache.read(self.file_path[1])
        self.assertEqual(UsptoZipCache.file_reads, 2)
        self.assertNotEqual(data_2, data_2_cached)

    def test_extracted_data(self):
        """Verify if the splitting of the contents inside the Zip
        is equal to the patents inside."""

        # Read the first zip file
        data_1 = self.file_cache.read(self.file_path[0])
        self.assertEqual(UsptoZipCache.file_reads, 1)
        self.assertEqual(len(data_1), 11)

        # Read the second zip file
        data_2 = self.file_cache.read(self.file_path[1])
        self.assertEqual(UsptoZipCache.file_reads, 2)
        self.assertEqual(len(data_2), 3)

        UsptoZipCache.file_reads = 0
