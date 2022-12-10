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
"""Journal names import integration tests"""

import os
import unittest
import sqlite3
import sys

sys.path.append("src")

from alexandria3k import csv_sources

DATABASE_PATH = "tests/tmp/journal_names.db"


class TestOrcid(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(DATABASE_PATH):
            os.unlink(DATABASE_PATH)

        csv_sources.load_csv_data(
            DATABASE_PATH,
            csv_sources.journals_table,
            "tests/data/titleFile.csv",
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)

    def test_import(
        self,
    ):
        result = TestOrcid.cursor.execute(
            f"SELECT Count(*) from journal_names"
        )
        (count,) = result.fetchone()
        self.assertEqual(count, 20)

    def test_issn_name(
        self,
    ):
        result = TestOrcid.cursor.execute(
            """SELECT title FROM journal_names
              WHERE issn_print='26636085'"""
        )
        (title,) = result.fetchone()
        self.assertEqual(title, "Innovate Pedagogy")

    def test_multiple_additional_issn(
        self,
    ):
        result = TestOrcid.cursor.execute(
            """
                SELECT Count(*) from journals_issns
                  WHERE journal_id='50200' AND issn_type = 'A'
            """
        )
        (count,) = result.fetchone()
        self.assertEqual(count, 3)

    def test_issn_id(
        self,
    ):
        for issn in ["00443379", "1420911X", "03010988", "03038408"]:
            result = TestOrcid.cursor.execute(
                f"""SELECT journal_id FROM journals_issns
                WHERE issn='{issn}'"""
            )
            (journal_id,) = result.fetchone()
            self.assertEqual(journal_id, "50200")
