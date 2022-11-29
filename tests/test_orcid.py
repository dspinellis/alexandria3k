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
"""ORCID import integration tests"""

import os
import unittest
import sqlite3
import sys

sys.path.append("src/alexandria3k")

import orcid

DATABASE_PATH = "tests/tmp/orcid.db"


class TestOrcid(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(DATABASE_PATH):
            os.unlink(DATABASE_PATH)

        orcid.populate(
            "tests/data/ORCID_2022_10_summaries.tar.gz",
            DATABASE_PATH,
            None,  # All columns
            False,  # No linked records
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
        result = TestOrcid.cursor.execute(f"SELECT Count(*) from persons")
        (count,) = result.fetchone()
        # ORCID_2022_10_summaries/000/0000-0001-5078-5000.xml is an error
        # record, so 7 records remain
        self.assertEqual(count, 7)

    def test_person(
        self,
    ):
        result = TestOrcid.cursor.execute(
            f"""SELECT given_names FROM persons
            WHERE orcid='0000-0003-4231-1897'"""
        )
        (name,) = result.fetchone()
        self.assertEqual(name, "Diomidis")

    def test_external_identifiers(
        self,
    ):
        result = TestOrcid.cursor.execute(
            f"""SELECT type, value
                                  FROM person_external_identifiers
                                  WHERE orcid='0000-0003-4231-1897'"""
        )
        rows = result.fetchmany(100)
        self.assertEqual(len(rows), 4)
        self.assertTrue(("Researcher ID", "E-3600-2010") in rows)
        self.assertTrue(("Scopus Author ID", "35566637400") in rows)

    def test_urls(
        self,
    ):
        result = TestOrcid.cursor.execute(
            f"""SELECT name, url FROM researcher_urls
                                  WHERE orcid='0000-0003-4231-1897'"""
        )
        rows = result.fetchmany(99)
        self.assertEqual(len(rows), 2)
        self.assertTrue(
            ("Personal web site", "http://www.dmst.aueb.gr/dds") in rows
        )
        self.assertTrue(
            (
                "Delft University of Technology profile page",
                "https://research.tudelft.nl/en/persons/b5e90008-e110-4d96-a64b-e06462d750cc",
            )
            in rows
        )

    def test_person_works(
        self,
    ):
        result = TestOrcid.cursor.execute(
            f"""SELECT orcid, doi FROM person_works
                                  WHERE orcid='0000-0003-4231-1897'"""
        )
        rows = result.fetchmany(999)
        self.assertEqual(len(rows), 128)
        self.assertTrue(
            ("0000-0003-4231-1897", "10.1109/TSE.2003.1245303") in rows
        )
