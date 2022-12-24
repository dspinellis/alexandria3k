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
"""ROR import integration tests"""

import os
import unittest
import sqlite3
import sys

sys.path.append("src")

from alexandria3k.common import ensure_unlinked, query_result
from alexandria3k import ror

DATABASE_PATH = "tests/tmp/ror.db"


class TestOrcidAll(unittest.TestCase):
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

    def test_import(self):
        result = TestOrcidAll.cursor.execute(
            "SELECT Count(*) from research_organizations"
        )
        (count,) = result.fetchone()
        self.assertEqual(count, 27)

    def test_organization(self):
        result = TestOrcidAll.cursor.execute(
            "SELECT * FROM research_organizations WHERE ror_path='019wvm592'"
        )
        (
            id,
            ror_path,
            name,
            status,
            established,
            country_code,
        ) = result.fetchone()
        self.assertEqual(id, 1)
        self.assertEqual(ror_path, "019wvm592")
        self.assertEqual(name, "Australian National University")
        self.assertEqual(status, "active")
        self.assertEqual(established, 1946)
        self.assertEqual(country_code, "AU")

    def test_funder_ids(self):
        result = TestOrcidAll.cursor.execute(
            "SELECT funder_id FROM ror_funder_ids WHERE ror_id=2"
        )
        rows = result.fetchmany(100)
        self.assertEqual(len(rows), 6)
        self.assertTrue(("501100001779",) in rows)
        self.assertTrue(("501100006532",) in rows)

    def test_ror_types(self):
        result = TestOrcidAll.cursor.execute(
            "SELECT type FROM ror_types WHERE ror_id=2"
        )
        rows = result.fetchmany(100)
        self.assertEqual(len(rows), 1)
        self.assertTrue(("Education",) in rows)

    def test_ror_links(self):
        result = TestOrcidAll.cursor.execute(
            "SELECT link FROM ror_links WHERE ror_id=2"
        )
        rows = result.fetchmany(100)
        self.assertEqual(len(rows), 1)
        self.assertTrue(("http://www.monash.edu/",) in rows)

    def test_ror_aliases(self):
        result = TestOrcidAll.cursor.execute(
            """SELECT alias FROM research_organizations
                INNER JOIN ror_aliases on research_organizations.rowid =
                  ror_aliases.ror_id
                WHERE ror_path='03r8z3t63'"""
        )
        rows = result.fetchmany(100)
        self.assertEqual(len(rows), 1)
        self.assertTrue(("University of New South Wales",) in rows)

    def test_ror_acronyms(self):
        result = TestOrcidAll.cursor.execute(
            """SELECT acronym FROM research_organizations
                INNER JOIN ror_acronyms on research_organizations.rowid =
                  ror_acronyms.ror_id
                WHERE ror_path='03r8z3t63'"""
        )
        rows = result.fetchmany(100)
        self.assertEqual(len(rows), 1)
        self.assertTrue(("UNSW",) in rows)

    def test_ror_relationships(self):
        result = TestOrcidAll.cursor.execute(
            "SELECT type, ror_path FROM ror_relationships WHERE ror_id=2"
        )
        rows = result.fetchmany(100)
        self.assertEqual(len(rows), 13)
        self.assertTrue(
            (
                "Related",
                "0484pjq71",
            )
            in rows
        )
        self.assertTrue(
            (
                "Child",
                "048t93218",
            )
            in rows
        )

    def test_ror_addresses(self):
        result = TestOrcidAll.cursor.execute(
            "SELECT * FROM ror_addresses WHERE ror_id=2"
        )
        rows = result.fetchmany(100)
        self.assertEqual(len(rows), 1)
        self.assertTrue(
            (
                2,
                -37.9083,
                145.138,
                "Melbourne",
                "Victoria",
                None,
            )
            in rows
        )

    def test_ror_wikidata_ids(self):
        result = TestOrcidAll.cursor.execute(
            "SELECT wikidata_id FROM ror_wikidata_ids WHERE ror_id=2"
        )
        rows = result.fetchmany(100)
        self.assertEqual(len(rows), 1)
        self.assertTrue(("Q598841",) in rows)

    def test_ror_isnis(self):
        result = TestOrcidAll.cursor.execute(
            "SELECT isni FROM ror_isnis WHERE ror_id=2"
        )
        rows = result.fetchmany(100)
        self.assertEqual(len(rows), 1)
        self.assertTrue(("0000 0004 1936 7857",) in rows)
