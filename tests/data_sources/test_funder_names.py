#
# Alexandria3k FunderNames bibliographic metadata processing
# Copyright (C) 2022-2023  Diomidis Spinellis
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
"""funder_names module test. This tests the common functionality of all
csv_source data sources."""

import csv
import os
import random
import re
import sys
import sqlite3
import unittest

from ..test_dir import add_src_dir, td
add_src_dir()

from ..common import PopulateQueries, record_count
from alexandria3k.common import ensure_unlinked, query_result
from alexandria3k.data_sources import funder_names

DATABASE_PATH = td("tmp/funder_names.db")
ATTACHED_DATABASE_PATH = td("tmp/attached.db")


def populate_attached():
    """Create and populate an attached database"""
    ensure_unlinked(ATTACHED_DATABASE_PATH)
    attached = sqlite3.connect(ATTACHED_DATABASE_PATH)
    attached.execute("CREATE TABLE s_funder_urls(url)")
    attached.execute("INSERT INTO s_funder_urls VALUES('http://dx.doi.org/10.13039/100014856')")
    attached.commit()
    attached.close()


class TestFunderNamesPopulateVanilla(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        # ensure_unlinked(DATABASE_PATH)
        # debug.set_flags(["sql", "dump-matched"])

        cls.funder_names = funder_names.FunderNames(td("data/funderNames.csv"))
        cls.funder_names.populate(DATABASE_PATH)
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.funder_names.close()

    def test_counts(self):
        self.assertEqual(self.record_count("funder_names"), 11)

        self.assertEqual(
            self.record_count(
                """(SELECT DISTINCT url
          FROM funder_names WHERE name like '%A%')"""
            ),
            6,
        )

        self.assertEqual(
            self.record_count(
                "(SELECT DISTINCT name FROM funder_names)"
            ),
            11,
        )

        self.assertEqual(
            self.cond_count("funder_names", "replaced is not null"), 1
        )

    def test_contents(self):
        self.assertEqual(
            self.cond_field(
                "funder_names", "name", "url = 'http://dx.doi.org/10.13039/100019312'"
            ),
            "'Ahahui Koa Ānuenue",
        )
        self.assertEqual(
            self.cond_field(
                "funder_names", "replaced", "url = 'http://dx.doi.org/10.13039/501100008163'"
            ),
            "R",
        )


class TestFunderNamesPopulateSample(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        # ensure_unlinked(DATABASE_PATH)
        # debug.set_flags(["sql", "dump-matched"])

        random.seed(42)
        cls.funder_names = funder_names.FunderNames(td("data/funderNames.csv"), lambda _x: random.random() < 0.5)
        cls.funder_names.populate(DATABASE_PATH)
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.funder_names.close()

    def test_counts(self):
        self.assertEqual(self.record_count("funder_names"), 7)


class TestFunderNamesPopulateMasterCondition(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        # debug.set_flags(["sql", "dump-matched"])

        cls.funder_names = funder_names.FunderNames(td("data/funderNames.csv"))
        cls.funder_names.populate(DATABASE_PATH, None, "replaced = 'R'")
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.funder_names.close()

    def test_counts(self):
        self.assertEqual(self.record_count("funder_names"), 1)


class TestFunderNamesPopulateMasterColumnNoCondition(PopulateQueries):
    """Verify column specification and population of root table"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)

        # debug.set_flags(["sql"])
        cls.funder_names = funder_names.FunderNames(td("data/funderNames.csv"))
        cls.funder_names.populate( DATABASE_PATH, ["funder_names.url"])
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.funder_names.close()

    def test_counts(self):
        self.assertEqual(self.record_count("funder_names"), 11)

    def test_no_extra_fields(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("funder_names", "name", "true")


class TestFunderNamesPopulateMasterColumnCondition(PopulateQueries):
    """Verify column specification and population of single table"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)

        # debug.set_flags(["sql"])
        cls.funder_names = funder_names.FunderNames(td("data/funderNames.csv"))
        cls.funder_names.populate(
            DATABASE_PATH,
            ["funder_names.url"],
            "funder_names.replaced = 'R'",
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.funder_names.close()

    def test_counts(self):
        self.assertEqual(self.record_count("funder_names"), 1)

    def test_no_extra_fields(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("funder_names", "name", "true")


class TestFunderNamesQuery(unittest.TestCase):
    """Verify non-works column specification and multiple conditions"""

    @classmethod
    def setUpClass(cls):
        # debug.set_flags(["sql"])
        populate_attached()
        cls.funder_names = funder_names.FunderNames(
            td("data/funderNames.csv"),
            attach_databases=[f"attached:{ATTACHED_DATABASE_PATH}"]
        )

    @classmethod
    def tearDownClass(cls):
        del cls.funder_names
        os.unlink(ATTACHED_DATABASE_PATH)

    def test_works(self):
        self.assertEqual(
            record_count(
                self.funder_names.query("""SELECT * FROM funder_names
                    WHERE url like '%/5%'""")
            ),
            4,
        )

    def test_funder_names_attached(self):
        self.assertEqual(
            record_count(
                self.funder_names.query(
        """SELECT * FROM funder_names WHERE EXISTS (
            SELECT 1 FROM attached.s_funder_urls WHERE funder_names.url = s_funder_urls.url)
        """
                )
            ),
            1,
        )
