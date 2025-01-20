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

from .test_dir import add_src_dir, td
add_src_dir()

from alexandria3k import common
from alexandria3k.data_sources import ror

DATABASE_PATH = td("tmp/ror.db")

class TestCommon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(DATABASE_PATH):
            os.unlink(DATABASE_PATH)

        cls.ror = ror.Ror(td("data/ror.zip"))
        cls.ror.populate(DATABASE_PATH)

        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.ror.close()

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
        line = common.data_from_uri_provider("resource:data/asjc.csv").readline()

        self.assertTrue(common.table_exists(self.cursor, "ror_links"))
        self.assertEqual(line, b"Code;Field;Subject area;General field id\n")

    def test_remove_sqlite_comments_plain(self):
        s = "a"
        self.assertEqual(common.remove_sqlite_comments(s), "a")

    def test_remove_sqlite_comments_sql(self):
        s = """CREATE
-- SQL comment
select"""
        self.assertEqual(common.remove_sqlite_comments(s), "CREATE\nselect")
    def test_remove_sqlite_comments_c(self):
        s = """CREATE
/*
A C comment
last line
*/
select"""
        self.assertEqual(common.remove_sqlite_comments(s), "CREATE\n\nselect")
