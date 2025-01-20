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
import random
import sys
import unittest

import ahocorasick
import apsw

from ..test_dir import add_src_dir, td

add_src_dir()

from alexandria3k.common import ensure_unlinked, query_result
from alexandria3k.data_sources import ror, crossref

DATABASE_PATH = td("tmp/ror.db")


class TestRorPopulate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(DATABASE_PATH):
            os.unlink(DATABASE_PATH)

        cls.ror = ror.Ror(td("data/ror.zip"))
        cls.ror.populate(DATABASE_PATH)

        cls.con = apsw.Connection(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.ror.close()

    def test_import(self):
        result = TestRorPopulate.cursor.execute(
            "SELECT Count(*) from research_organizations"
        )
        (count,) = result.fetchone()
        self.assertEqual(count, 29)

    def test_organization(self):
        result = TestRorPopulate.cursor.execute(
            "SELECT * FROM research_organizations WHERE ror_path='019wvm592'"
        )
        (
            id,
            ror_path,
            name,
            status,
            established,
            grid,
            city,
            state,
            postcode,
            country_code,
            latitude,
            longitude,
        ) = result.fetchone()
        self.assertEqual(id, 0)
        self.assertEqual(ror_path, "019wvm592")
        self.assertEqual(name, "Australian National University")
        self.assertEqual(status, "active")
        self.assertEqual(established, 1946)
        self.assertEqual(grid, "grid.1001.0")
        self.assertEqual(city, "Canberra")
        self.assertEqual(state, "Australian Capital Territory")
        self.assertEqual(postcode, None)
        self.assertEqual(country_code, "AU")
        self.assertEqual(latitude, -35.2778)
        self.assertEqual(longitude, 149.1205)

    def test_blank_external_ids(self):
        result = TestRorPopulate.cursor.execute(
            "SELECT * from main.research_organizations "
            "WHERE research_organizations.ror_path='02f4ks689'"
        )
        (
            id,
            ror_path,
            name,
            status,
            established,
            grid,
            city,
            state,
            postcode,
            country_code,
            latitude,
            longitude,
        ) = result.fetchone()
        self.assertEqual(id, 28)
        self.assertEqual(ror_path, "02f4ks689")
        self.assertEqual(name, "Axiom Data Science")
        self.assertEqual(status, "active")
        self.assertEqual(established, 2007)
        self.assertEqual(grid, None)
        self.assertEqual(city, "Anchorage")
        self.assertEqual(state, None)
        self.assertEqual(postcode, None)
        self.assertEqual(country_code, "US")
        self.assertEqual(latitude, 61.21806)
        self.assertEqual(longitude, -149.90028)

    def test_funder_ids(self):
        result = TestRorPopulate.cursor.execute(
            """SELECT funder_id FROM ror_funder_ids WHERE ror_id=(
                    SELECT id FROM research_organizations WHERE
                        ror_path='02bfwt286')"""
        )
        rows = list(result)
        self.assertEqual(len(rows), 6)
        self.assertTrue(("501100001779",) in rows)
        self.assertTrue(("501100006532",) in rows)

    def test_ror_types(self):
        result = TestRorPopulate.cursor.execute(
            """SELECT type FROM ror_types WHERE ror_id=(
                    SELECT id FROM research_organizations WHERE
                        ror_path='02bfwt286')"""
        )
        rows = list(result)
        self.assertEqual(len(rows), 1)
        self.assertTrue(("Education",) in rows)

    def test_ror_links(self):
        result = TestRorPopulate.cursor.execute(
            """SELECT link FROM ror_links WHERE ror_id=(
                    SELECT id FROM research_organizations WHERE
                        ror_path='02bfwt286')"""
        )
        rows = list(result)
        self.assertEqual(len(rows), 1)
        self.assertTrue(("http://www.monash.edu/",) in rows)

    def test_ror_aliases(self):
        result = TestRorPopulate.cursor.execute(
            """SELECT alias FROM research_organizations
                INNER JOIN ror_aliases on research_organizations.rowid =
                  ror_aliases.ror_id
                WHERE ror_path='03r8z3t63'"""
        )
        rows = list(result)
        self.assertEqual(len(rows), 1)
        self.assertTrue(("University of New South Wales",) in rows)

    def test_ror_acronyms(self):
        result = TestRorPopulate.cursor.execute(
            """SELECT acronym FROM research_organizations
                INNER JOIN ror_acronyms on research_organizations.rowid =
                  ror_acronyms.ror_id
                WHERE ror_path='03r8z3t63'"""
        )
        rows = list(result)
        self.assertEqual(len(rows), 1)
        self.assertTrue(("UNSW",) in rows)

    def test_ror_relationships(self):
        result = TestRorPopulate.cursor.execute(
            """SELECT type, ror_path FROM ror_relationships WHERE ror_id=(
                    SELECT id FROM research_organizations WHERE
                        ror_path='02bfwt286')"""
        )
        rows = list(result)
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

    def test_ror_wikidata_ids(self):
        result = TestRorPopulate.cursor.execute(
            """SELECT wikidata_id FROM ror_wikidata_ids WHERE ror_id=(
                    SELECT id FROM research_organizations WHERE
                        ror_path='02bfwt286')"""
        )
        rows = list(result)
        self.assertEqual(len(rows), 1)
        self.assertTrue(("Q598841",) in rows)

    def test_ror_isnis(self):
        result = TestRorPopulate.cursor.execute(
            """SELECT isni FROM ror_isnis WHERE ror_id=(
                    SELECT id FROM research_organizations WHERE
                        ror_path='02bfwt286')"""
        )
        rows = list(result)
        self.assertEqual(len(rows), 1)
        self.assertTrue(("0000 0004 1936 7857",) in rows)


class TestRorPopulateSample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(DATABASE_PATH):
            os.unlink(DATABASE_PATH)

        random.seed("alexandria3k")
        cls.ror = ror.Ror(
            td("data/ror.zip"), lambda _name: random.random() < 0.25
        )
        cls.ror.populate(DATABASE_PATH)

        cls.con = apsw.Connection(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.ror.close()

    def test_import(self):
        result = TestRorPopulateSample.cursor.execute(
            "SELECT Count(*) from research_organizations"
        )
        (count,) = result.fetchone()
        self.assertEqual(count, 12)
