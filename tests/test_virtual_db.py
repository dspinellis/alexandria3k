#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2023  Diomidis Spinellis
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
"""Virtual database module test"""

import sys
import unittest

from .test_dir import add_src_dir
add_src_dir()

from alexandria3k.db_schema import ColumnMeta, TableMeta

def extractor():
    return 42

class TestTableMeta(unittest.TestCase):
    def test_constructor_getters(self):
        table = TableMeta(
            "tname",
            columns=[
                ColumnMeta("id", rowid=True),
                ColumnMeta("cname1"),
                ColumnMeta("cname2", extractor),
                ColumnMeta("cname3", data_type="INTEGER"),
            ],
            primary_key="cname1",
            foreign_key="cname2",
            parent_name="parent",
            post_population_script="pscript",
        )
        self.assertEqual(table.get_name(), "tname")
        self.assertEqual(table.get_primary_key(), "cname1")
        self.assertEqual(table.get_foreign_key(), "cname2")
        self.assertEqual(table.get_parent_name(), "parent")
        self.assertEqual(table.get_post_population_script(), "pscript")

        self.assertEqual(table.get_value_extractor_by_ordinal(1), None)
        self.assertEqual(table.get_value_extractor_by_ordinal(2), extractor)

        self.assertEqual(table.get_value_extractor_by_name("cname1"), None)
        self.assertEqual(table.get_value_extractor_by_name("cname2"), extractor)

        self.assertEqual(table.table_schema(), "CREATE TABLE tname(\n  id INTEGER PRIMARY KEY,\n  cname1,\n  cname2,\n  cname3 INTEGER\n);\n")
        self.assertEqual(table.insert_statement(), "INSERT INTO tname(id, cname1, cname2, cname3) VALUES (?, ?, ?, ?);")
        self.assertEqual(table.get_column_definition_by_name("cname2"), "cname2")
        self.assertEqual(table.get_column_definition_by_name("id"), "id INTEGER PRIMARY KEY")
        self.assertEqual(table.get_column_definition_by_name("cname3"), "cname3 INTEGER")
