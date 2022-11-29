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
"""Crossref import integration tests"""

import os
import unittest
import sqlite3
import sys

sys.path.append("src/alexandria3k")

from common import ensure_unlinked, query_result
import crossref
import debug
from file_cache import FileCache

DATABASE_PATH = "tests/tmp/crossref.db"


class TestCrossrefPopulate(unittest.TestCase):
    """Common utility methods"""

    def record_count(self, table):
        """Return the number of records in the specified table"""
        return query_result(self.cursor, f"SELECT Count(*) FROM {table}")

    def cond_field(self, table, field, condition):
        """Return the specified field in the specified table matching
        the specified condition"""
        return query_result(
            self.cursor, f"SELECT {field} FROM {table} WHERE {condition}"
        )

    def cond_count(self, table, condition):
        """Return the number of records in the specified table matching
        the specified condition"""
        return query_result(
            self.cursor, f"SELECT Count(*) FROM {table} WHERE {condition}"
        )


class TestCrossrefPopulateVanilla(TestCrossrefPopulate):
    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0
        # debug.set_flags(["log-sql", "dump-matched"])

        cls.crossref = crossref.Crossref("tests/data/sample")
        cls.crossref.populate(DATABASE_PATH)
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)

    def test_counts(self):
        self.assertEqual(self.record_count("works"), 11)
        self.assertEqual(self.record_count("work_authors"), 68)
        self.assertEqual(self.record_count("author_affiliations"), 13)
        self.assertEqual(self.record_count("work_references"), 269)
        self.assertEqual(self.record_count("work_updates"), 1)
        self.assertEqual(self.record_count("work_subjects"), 16)
        self.assertEqual(self.record_count("work_funders"), 4)
        self.assertEqual(self.record_count("funder_awards"), 4)

        self.assertEqual(
            self.record_count(
                """(SELECT DISTINCT orcid
          FROM work_authors WHERE orcid is not null)"""
            ),
            8,
        )

        self.assertEqual(
            self.record_count(
                """(SELECT DISTINCT work_id
          FROM work_authors)"""
            ),
            10,
        )

        self.assertEqual(
            self.cond_count("work_references", "doi is not null"), 204
        )
        self.assertEqual(FileCache.file_reads, 7)

    def test_work_countents(self):
        self.assertEqual(
            self.cond_field(
                "works", "publisher", "doi = '10.1016/j.bjps.2022.04.046'"
            ),
            "Elsevier BV",
        )
        self.assertEqual(
            self.cond_field(
                "works", "type", "doi = '10.1016/j.bjps.2022.04.046'"
            ),
            "journal-article",
        )
        self.assertEqual(
            self.cond_field(
                "works", "issn_print", "doi = '10.1016/j.bjps.2022.04.046'"
            ),
            "17486815",
        )
        self.assertEqual(
            self.cond_field(
                "works",
                "published_day",
                "doi = '10.35609/gcbssproceeding.2022.1(2)'",
            ),
            16,
        )


class TestCrossrefPopulateCondition(TestCrossrefPopulate):
    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0
        # debug.set_flags(["log-sql", "dump-matched"])

        cls.crossref = crossref.Crossref("tests/data/sample")
        cls.crossref.populate(
            DATABASE_PATH, None, "work_authors.orcid = '0000-0002-5878-603X'"
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)

    def test_counts(self):
        self.assertEqual(self.record_count("works"), 2)
        self.assertEqual(self.record_count("work_authors"), 5)
        self.assertEqual(self.record_count("author_affiliations"), 5)
        self.assertEqual(FileCache.file_reads, 7)


class TestCrossrefPopulateConditionColumns(TestCrossrefPopulate):
    """Verify column specification and population of sibling tables"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0

        cls.crossref = crossref.Crossref("tests/data/sample")
        cls.crossref.populate(
            DATABASE_PATH,
            ["works.doi", "work_funders.*"],
            "work_authors.family = 'Costa-Urrutia'",
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)

    def test_counts(self):
        self.assertEqual(self.record_count("works"), 1)
        self.assertEqual(self.record_count("work_funders"), 2)
        self.assertEqual(
            self.cond_count("work_funders", "doi='10.13039/501100003593'"), 1
        )
        self.assertEqual(FileCache.file_reads, 7)

    def test_no_extra_fields(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("works", "title", "true")

    def test_no_extra_tables(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("work_authors", "family", "true")


class TestCrossrefPopulateMultipleConditionColumns(TestCrossrefPopulate):
    """Verify non-works column specification and multiple conditions"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0

        cls.crossref = crossref.Crossref("tests/data/sample")
        cls.crossref.populate(
            DATABASE_PATH,
            ["work_updates.label"],
            "works.doi = '10.1007/s00417-022-05677-8' AND work_authors.given='Hoang Mai' AND work_subjects.name = 'Ophthalmology'",
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)

    def test_counts(self):
        self.assertEqual(self.record_count("work_updates"), 1)
        self.assertEqual(
            self.cond_count("work_updates", "label='Correction'"), 1
        )
        self.assertEqual(FileCache.file_reads, 7)

    def test_no_extra_fields(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("work_updates", "doi", "true")

    def test_no_extra_tables(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("works", "doi", "true")


class TestCrossrefTransitiveClosure(unittest.TestCase):
    def test_single(self):
        self.assertEqual(
            crossref.tables_transitive_closure(["works"], "works"),
            set(["works"]),
        )

    def test_child(self):
        self.assertEqual(
            crossref.tables_transitive_closure(["work_authors"], "works"),
            set(["works", "work_authors"]),
        )

    def test_grandchild(self):
        self.assertEqual(
            crossref.tables_transitive_closure(
                ["author_affiliations"], "works"
            ),
            set(["works", "work_authors", "author_affiliations"]),
        )

    def test_siblings(self):
        self.assertEqual(
            crossref.tables_transitive_closure(
                ["work_authors", "work_subjects"], "works"
            ),
            set(["works", "work_authors", "work_subjects"]),
        )


def record_count(g):
    """Return the elements (e.g. records) in generator g"""
    return sum(1 for _ in g)


class TestCrossrefQuery(unittest.TestCase):
    """Verify non-works column specification and multiple conditions"""

    def setUp(self):
        FileCache.file_reads = 0
        self.crossref = crossref.Crossref("tests/data/sample")

    def test_works(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.crossref.query("SELECT * FROM works", partition)
                ),
                11,
            )

    def test_work_authors(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.crossref.query(
                        "SELECT * FROM work_authors", partition
                    )
                ),
                68,
            )

    def test_work_condition(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.crossref.query(
                        "SELECT work_authors.* FROM works LEFT JOIN work_authors ON work_authors.work_id = works.id WHERE works.doi = '10.1016/j.bjps.2022.04.046'",
                        partition,
                    )
                ),
                5,
            )

    def test_work_column_subset_condition(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.crossref.query(
                        "SELECT works.doi, work_authors.family FROM works LEFT JOIN work_authors ON work_authors.work_id = works.id WHERE works.doi = '10.1016/j.bjps.2022.04.046'",
                        partition,
                    )
                ),
                5,
            )


class TestCrossrefPopulateNormalize(TestCrossrefPopulate):
    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0
        # debug.set_flags(["log-sql", "dump-matched"])

        cls.crossref = crossref.Crossref("tests/data/sample")
        cls.crossref.populate(DATABASE_PATH)
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)

    def test_normalized_affiliations(self):
        crossref.normalize_affiliations(self.cursor)
        self.assertEqual(self.record_count("affiliation_names"), 5)
        self.assertEqual(self.record_count("authors_affiliations"), 13)
        self.assertEqual(self.record_count("affiliations_works"), 6)

    def test_normalized_subjects(self):
        crossref.normalize_subjects(self.cursor)
        self.assertEqual(self.record_count("subject_names"), 16)
        self.assertEqual(self.record_count("works_subjects"), 16)
