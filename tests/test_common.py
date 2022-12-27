#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2022  Diomidis Spinellis
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
"""common module test"""

import os
import re
import sqlite3
import sys
import unittest

sys.path.append("src")

from alexandria3k import common, ror

DATABASE_PATH = "tests/tmp/ror.db"

class TestCommon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(DATABASE_PATH):
            os.unlink(DATABASE_PATH)

        ror.populate("tests/data/ror.zip", DATABASE_PATH)
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)

    def test_program_version(self):
        version = common.program_version()
        expected_regex = re.compile(r"(([0-9a-f]{6,})|(\d+\.\d+\.\d+))")
        self.assertTrue(expected_regex.fullmatch(version), f"Invalid version string [{version}]")

    def test_is_url(self):
        self.assertTrue(common.is_url("https://www.example.com/foo"))
        self.assertFalse(common.is_url("foo.csv"))

    def test_table_exists(self):
        self.assertTrue(common.table_exists(self.cursor, "ror_links"))
        self.assertFalse(common.table_exists(self.cursor, "xyzzy"))

    def test_resource_data_source(self):
        line = common.data_source("resource:data/asjc.csv").readline()

        self.assertTrue(common.table_exists(self.cursor, "ror_links"))
        self.assertEqual(line, b"Code;Field;Subject area;General field id\n")
