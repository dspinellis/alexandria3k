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

from ..test_dir import add_src_dir, td
add_src_dir()

from ..common import PopulateQueries, record_count
from alexandria3k.common import ensure_unlinked, query_result
from alexandria3k.data_sources import crossref
from alexandria3k import debug
from alexandria3k.file_cache import FileCache


DATABASE_PATH = td("tmp/crossref.db")
ATTACHED_DATABASE_PATH = td("tmp/attached.db")

def populate_attached():
    """Create and populate an attached database"""
    ensure_unlinked(ATTACHED_DATABASE_PATH)
    attached = sqlite3.connect(ATTACHED_DATABASE_PATH)
    attached.execute("CREATE TABLE s_works(doi)")
    attached.execute("INSERT INTO s_works VALUES('10.1016/j.bjps.2022.04.046')")
    attached.commit()
    attached.close()


class TestDoiNormalize(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(crossref.normalized_doi(None), None)
        self.assertEqual(
            crossref.normalized_doi("10.1207/s15327663jcp1001&2_08"),
            "10.1207/s15327663jcp1001&2_08",
        )
        self.assertEqual(
            crossref.normalized_doi("10.2495/d&n-v1-n1-48-60"),
            "10.2495/d&n-v1-n1-48-60",
        )

    def test_space(self):
        self.assertEqual(
            crossref.normalized_doi("10 .1207/s15327663jcp1001&2_08"),
            "10.1207/s15327663jcp1001&2_08",
        )
        self.assertEqual(
            crossref.normalized_doi("10.2214/am j roentgenol.19.21598"),
            "10.2214/amjroentgenol.19.21598",
        )
        self.assertEqual(
            crossref.normalized_doi(
                "10.1145/2892208.2892226 10.1145/2892208.2892226"
            ),
            "10.1145/2892208.2892226",
        )

    def test_named_escapes(self):
        self.assertEqual(
            crossref.normalized_doi(
                "10.1038/s41596&ndash;019&ndash;0128&ndash;8"
            ),
            "10.1038/s41596-019-0128-8",
        )
        self.assertEqual(
            crossref.normalized_doi(
                "10.1130/0091-7613(2000)28&lt;1067:liiaed&gt;2.0.co;2"
            ),
            "10.1130/0091-7613(2000)28<1067:liiaed>2.0.co;2",
        )

        # Double escape!
        self.assertEqual(
            crossref.normalized_doi(
                "10.1002/1097-4636(200102)54:2&amp;lt;198::aid-jbm6&amp;gt;3.0.co;2-7"
            ),
            "10.1002/1097-4636(200102)54:2<198::aid-jbm6>3.0.co;2-7",
        )

    def test_numbered_escapes(self):
        self.assertEqual(
            crossref.normalized_doi(
                "10.1379/1466-1268(2001)006&#x003c;0225:tefoat&#x003e;2.0.co;2"
            ),
            "10.1379/1466-1268(2001)006<0225:tefoat>2.0.co;2",
        )
        self.assertEqual(
            crossref.normalized_doi(
                "10.1002/(sici)1521-4141(199906)29:06&#60;1785::aid-immu1785&#62;3.0.co;2-u"
            ),
            "10.1002/(sici)1521-4141(199906)29:06<1785::aid-immu1785>3.0.co;2-u",
        )


class TestCrossrefPopulateVanilla(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0
        # debug.set_flags(["sql", "dump-matched"])

        cls.crossref = crossref.Crossref(td("data/crossref-sample"))
        cls.crossref.populate(DATABASE_PATH)
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.crossref.close()

    def test_counts(self):
        self.assertEqual(self.record_count("works"), 12)
        self.assertEqual(self.record_count("work_authors"), 69)
        self.assertEqual(self.record_count("author_affiliations"), 14)
        self.assertEqual(self.record_count("work_references"), 281)
        self.assertEqual(self.record_count("work_updates"), 1)
        self.assertEqual(self.record_count("work_subjects"), 16)
        self.assertEqual(self.record_count("work_funders"), 5)
        self.assertEqual(self.record_count("funder_awards"), 5)
        self.assertEqual(self.record_count("work_links"), 20)
        self.assertEqual(self.record_count("work_licenses"), 16)

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
            11,
        )

        self.assertEqual(
            self.cond_count("work_references", "doi is not null"), 211
        )
        self.assertEqual(FileCache.file_reads, 8)

    def test_work_contents(self):
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
        self.assertEqual(
            self.cond_field(
                "work_licenses",
                "delay_in_days",
                "url = 'http://creativecommons.org/licenses/by-nc-nd/4.0/'",
            ),
            25,
        )
        self.assertEqual(
            self.cond_field(
                "work_licenses",
                "start_timestamp",
                "url = 'http://creativecommons.org/licenses/by-nc-nd/4.0/'",
            ),
            1650931200000,
        )
        self.assertEqual(
            self.cond_field(
                "work_links",
                "content_type",
                "url = 'https://api.elsevier.com/content/article/PII:S2352847822000557?httpAccept=text/plain'",
            ),
            "text/plain",
        )
        self.assertEqual(
            self.cond_field(
                "works",
                "references_count",
                "doi = '10.1007/s10270-017-0613-x'",
            ),
            42,
        )
        self.assertEqual(
            self.cond_field(
                "works",
                "is_referenced_by_count",
                "doi = '10.1007/s10270-017-0613-x'",
            ),
            5,
        )


class TestCrossrefPopulateMasterCondition(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0
        # debug.set_flags(["sql", "dump-matched", "apsw-logging"])

        cls.crossref = crossref.Crossref(td("data/crossref-sample"))
        cls.crossref.populate(DATABASE_PATH, None, "issn_print = '16191366'")
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.crossref.close()

    def test_counts(self):
        self.assertEqual(self.record_count("works"), 1)
        self.assertEqual(self.record_count("work_authors"), 1)
        self.assertEqual(self.record_count("work_references"), 42)
        self.assertEqual(FileCache.file_reads, 8)


class TestCrossrefPopulateDetailCondition(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0
        # debug.set_flags(["sql", "dump-matched"])

        cls.crossref = crossref.Crossref(td("data/crossref-sample"))
        cls.crossref.populate(
            DATABASE_PATH, None, "work_authors.orcid = '0000-0002-5878-603X'"
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.crossref.close()

    def test_counts(self):
        self.assertEqual(self.record_count("works"), 2)
        self.assertEqual(self.record_count("work_authors"), 5)
        self.assertEqual(self.record_count("author_affiliations"), 5)
        self.assertEqual(FileCache.file_reads, 8)


class TestCrossrefPopulateMasterColumnNoCondition(PopulateQueries):
    """Verify column specification and population of root table"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0

        # debug.set_flags(["sql"])
        cls.crossref = crossref.Crossref(td("data/crossref-sample"))
        cls.crossref.populate( DATABASE_PATH, ["works.doi"])
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.crossref.close()

    def test_counts(self):
        self.assertEqual(self.record_count("works"), 12)
        self.assertEqual(FileCache.file_reads, 8)

    def test_no_extra_fields(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("works", "title", "true")

    def test_no_extra_tables(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("work_authors", "family", "true")

class TestCrossrefPopulateMasterColumnCondition(PopulateQueries):
    """Verify column specification and population of single table"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0

        # debug.set_flags(["sql"])
        cls.crossref = crossref.Crossref(td("data/crossref-sample"))
        cls.crossref.populate(
            DATABASE_PATH,
            ["works.doi"],
            "works.published_year BETWEEN 1970 AND 2020",
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.crossref.close()

    def test_counts(self):
        self.assertEqual(self.record_count("works"), 4)
        self.assertEqual(FileCache.file_reads, 8)

    def test_no_extra_fields(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("works", "title", "true")

    def test_no_extra_tables(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("work_authors", "family", "true")


class TestCrossrefPopulateDetailConditionColumns(PopulateQueries):
    """Verify column specification and population of sibling tables"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0

        # debug.set_flags(["sql"])
        cls.crossref = crossref.Crossref(td("data/crossref-sample"))
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
        cls.crossref.close()

    def test_counts(self):
        self.assertEqual(self.record_count("works"), 1)
        self.assertEqual(self.record_count("work_funders"), 2)
        self.assertEqual(
            self.cond_count("work_funders", "doi='10.13039/501100003593'"), 1
        )
        self.assertEqual(FileCache.file_reads, 8)

    def test_no_extra_fields(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("works", "title", "true")

    def test_no_extra_tables(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("work_authors", "family", "true")


class TestCrossrefPopulateMultipleConditionColumns(PopulateQueries):
    """Verify non-works column specification and multiple conditions"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0

        cls.crossref = crossref.Crossref(td("data/crossref-sample"))
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
        cls.crossref.close()

    def test_counts(self):
        self.assertEqual(self.record_count("work_updates"), 1)
        self.assertEqual(
            self.cond_count("work_updates", "label='Correction'"), 1
        )
        self.assertEqual(FileCache.file_reads, 8)

    def test_no_extra_fields(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("work_updates", "doi", "true")

    def test_no_extra_tables(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("works", "doi", "true")


class TestCrossrefTransitiveClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # debug.set_flags(["sql"])
        FileCache.file_reads = 0
        populate_attached()
        cls.crossref = crossref.Crossref(
            td("data/crossref-sample"),
            attach_databases=[f"attached:{ATTACHED_DATABASE_PATH}"]
        )

    @classmethod
    def tearDownClass(cls):
        del cls.crossref
        os.unlink(ATTACHED_DATABASE_PATH)

    def test_single(self):
        self.assertEqual(
            self.crossref.tables_transitive_closure(["works"], "works"),
            set(["works"]),
        )

    def test_child(self):
        self.assertEqual(
            self.crossref.tables_transitive_closure(["work_authors"], "works"),
            set(["works", "work_authors"]),
        )

    def test_grandchild(self):
        self.assertEqual(
            self.crossref.tables_transitive_closure(
                ["author_affiliations"], "works"
            ),
            set(["works", "work_authors", "author_affiliations"]),
        )

    def test_siblings(self):
        self.assertEqual(
            self.crossref.tables_transitive_closure(
                ["work_authors", "work_subjects"], "works"
            ),
            set(["works", "work_authors", "work_subjects"]),
        )


class TestCrossrefQuery(unittest.TestCase):
    """Verify non-works column specification and multiple conditions"""

    @classmethod
    def setUpClass(cls):
        # debug.set_flags(["sql"])
        FileCache.file_reads = 0
        populate_attached()
        cls.crossref = crossref.Crossref(
            td("data/crossref-sample"),
            attach_databases=[f"attached:{ATTACHED_DATABASE_PATH}"]
        )

    @classmethod
    def tearDownClass(cls):
        del cls.crossref
        os.unlink(ATTACHED_DATABASE_PATH)

    def test_works(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.crossref.query("SELECT * FROM works", partition)
                ),
                12,
            )

    def test_works_attached(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.crossref.query(
            """SELECT * FROM works WHERE EXISTS (
                SELECT 1 FROM attached.s_works WHERE works.doi = s_works.doi)
            """, partition
                    )
                ),
                1,
            )

    def test_work_authors(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.crossref.query(
                        "SELECT * FROM work_authors", partition
                    )
                ),
                69,
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


class TestCrossrefPopulateAttachedDatabaseCondition(PopulateQueries):
    """Verify column specification and population of single table"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0
        populate_attached()

        # debug.set_flags(["sql"])
        cls.crossref = crossref.Crossref(
            td("data/crossref-sample"),
            attach_databases=[f"attached:{ATTACHED_DATABASE_PATH}"]
        )
        cls.crossref.populate(
            DATABASE_PATH,
            ["works.doi"],
            "EXISTS (SELECT 1 FROM attached.s_works WHERE works.doi = s_works.doi)",
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()


    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        os.unlink(ATTACHED_DATABASE_PATH)
        cls.crossref.close()

    def test_counts(self):
        self.assertEqual(self.record_count("works"), 1)
        self.assertEqual(FileCache.file_reads, 8)

class TestContextManager(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)

    def test_counts(self):
        with crossref.Crossref(td("data/crossref-sample")) as c:
            c.populate(DATABASE_PATH)
            self.assertEqual(self.record_count("works"), 12)
