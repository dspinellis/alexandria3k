#
# Alexandria3k Datacite bibliographic metadata processing
# Copyright (C) 2023-2024  Evgenia Pampidi
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
"""DataCite import integration tests"""

import os
import unittest
import sqlite3

from ..test_dir import add_src_dir, td
add_src_dir()

from ..common import PopulateQueries, record_count
from alexandria3k.common import ensure_unlinked, query_result
from alexandria3k.data_sources import datacite
from alexandria3k.file_cache import FileCache


DATABASE_PATH = td("tmp/datacite.db")

class TestDatacitePopulateVanilla(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        # debug.set_flags(["sql", "dump-matched"])

        cls.datacite = datacite.Datacite(td("data/datacite.tar.gz"))
        cls.datacite.populate(DATABASE_PATH)
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.datacite.close()

    def test_count_dc_works(self):
        self.assertEqual(self.record_count("dc_works"), 10)

    def test_count_dc_work_creators(self):
        self.assertEqual(self.record_count("dc_work_creators"), 30)

    def test_count_dc_creator_name_identifiers(self):
        self.assertEqual(self.record_count("dc_creator_name_identifiers"), 9)

    def test_count_dc_creator_affiliations(self):
        self.assertEqual(self.record_count("dc_creator_affiliations"), 18)

    def test_count_dc_work_titles(self):
        self.assertEqual(self.record_count("dc_work_titles"), 10)

    def test_count_dc_work_subjects(self):
        self.assertEqual(self.record_count("dc_work_subjects"), 31)

    def test_count_dc_work_contributors(self):
        self.assertEqual(self.record_count("dc_work_contributors"), 2)

    def test_count_dc_contributor_name_identifiers(self):
        self.assertEqual(self.record_count("dc_contributor_name_identifiers"), 0)

    def test_count_dc_contributor_affiliations(self):
        self.assertEqual(self.record_count("dc_contributor_affiliations"), 2)

    def test_count_dc_work_dates(self):
        self.assertEqual(self.record_count("dc_work_dates"), 8)

    def test_count_dc_work_related_identifiers(self):
        self.assertEqual(self.record_count("dc_work_related_identifiers"), 20)

    def test_count_dc_work_descriptions(self):
        self.assertEqual(self.record_count("dc_work_descriptions"), 13)

    def test_count_dc_work_geo_locations(self):
        self.assertEqual(self.record_count("dc_work_geo_locations"), 2)

    def test_count_dc_work_funding_references(self):
        self.assertEqual(self.record_count("dc_work_funding_references"), 2)

    def test_count_distinct_name_identifiers(self):
        self.assertEqual(
            self.record_count(
                """(SELECT DISTINCT name_identifier
          FROM dc_creator_name_identifiers)"""
            ),
            9,
        )

    def test_count_distinct_work_creators(self):
        self.assertEqual(
            self.record_count(
                """(SELECT DISTINCT work_id
          FROM dc_work_creators)"""
            ),
            10,
        )

    def test_count_distinct_works(self):
        self.assertEqual(self.record_count(
                """(SELECT DISTINCT container_id FROM dc_works)"""
            ),
            5,
        )

    def test_work_contents(self):
        self.assertEqual(
            self.cond_field(
                "dc_works", "publisher", "doi = '10.5281/zenodo.8404'"
            ),
            "Zenodo",
        )
        self.assertEqual(
            self.cond_field(
                "dc_works", "publication_year", "doi = '10.5281/zenodo.8404'"
            ),
            2014,
        )
        self.assertEqual(
            self.cond_field(
                "dc_works", "resource_type", "doi = '10.5281/zenodo.8404'"
            ),
            "Conference paper",
        )
        self.assertEqual(
            self.cond_field(
                "dc_works",
                "resource_type_general",
                "doi = '10.5281/zenodo.8404'",
            ),
            "Text",
        )
        self.assertEqual(
            self.cond_field(
                "dc_works",
                "url",
                "doi = '10.5281/zenodo.8404'",
            ),
            "https://zenodo.org/record/8404",
        )
        self.assertEqual(
            self.cond_field(
                "dc_works",
                "created",
                "doi = '10.5281/zenodo.8404'",
            ),
            "2014-02-19T22:15:04Z",
        )
        self.assertEqual(
            self.cond_field(
                "dc_works",
                "registered",
                "doi = '10.5281/zenodo.8404'",
            ),
            "2014-02-19T22:15:05Z",
        )
        self.assertEqual(
            self.cond_field(
                "dc_works",
                "published",
                "doi = '10.5281/zenodo.8404'",
            ),
            "2014-05-13",
        )
        self.assertEqual(
            self.cond_field(
                "dc_work_rights",
                "rights",
                "rights_uri = 'info:eu-repo/semantics/openAccess'",
            ),
            "Open Access",
        )


class TestDatacitePopulateMasterCondition(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        # debug.set_flags(["sql", "dump-matched"])

        cls.datacite = datacite.Datacite(td("data/datacite.tar.gz"))
        cls.datacite.populate(DATABASE_PATH, None, "doi = '10.5281/zenodo.8402'")
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.datacite.close()

    def test_counts(self):
        self.assertEqual(self.record_count("dc_works"), 1)
        self.assertEqual(self.record_count("dc_work_creators"), 7)
        self.assertEqual(self.record_count("dc_work_subjects"), 5)
        self.assertEqual(self.record_count(
                """(SELECT DISTINCT container_id FROM dc_works)"""
            ),
            1,
        )


class TestDatacitePopulateDetailCondition(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0
        # debug.set_flags(["sql", "dump-matched"])

        cls.datacite = datacite.Datacite(td("data/datacite.tar.gz"))
        cls.datacite.populate(
            DATABASE_PATH, None, "dc_creator_name_identifiers.name_identifier like '%0000-0003-3428-5019%'"
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.datacite.close()

    def test_counts(self):
        self.assertEqual(self.record_count("dc_works"), 1)
        self.assertEqual(self.record_count("dc_work_creators"), 3)
        self.assertEqual(self.record_count("dc_creator_affiliations"), 3)


class TestDatacitePopulateMasterColumnNoCondition(PopulateQueries):
    """Verify column specification and population of root table"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0

        # debug.set_flags(["sql"])
        cls.datacite = datacite.Datacite(td("data/datacite.tar.gz"))
        cls.datacite.populate( DATABASE_PATH, ["dc_works.doi"])
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.datacite.close()

    def test_counts(self):
        self.assertEqual(self.record_count("dc_works"), 10)

    def test_no_extra_fields(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("dc_works", "publisher", "true")

    def test_no_extra_tables(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("dc_work_creators", "name", "true")

class TestDatacitePopulateMasterColumnCondition(PopulateQueries):
    """Verify column specification and population of single table"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)

        # debug.set_flags(["sql"])
        cls.datacite = datacite.Datacite(td("data/datacite.tar.gz"))
        cls.datacite.populate(
            DATABASE_PATH,
            ["dc_works.doi"],
            "dc_works.publication_year >= 2015",
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.datacite.close()

    def test_counts(self):
        self.assertEqual(self.record_count("dc_works"), 7)

    def test_no_extra_fields(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("dc_works", "publisher", "true")

    def test_no_extra_tables(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("dc_work_creators", "name", "true")


class TestDatacitePopulateDetailConditionColumns(PopulateQueries):
    """Verify column specification and population of sibling tables"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)

        # debug.set_flags(["sql"])
        cls.datacite = datacite.Datacite(td("data/datacite.tar.gz"))
        cls.datacite.populate(
            DATABASE_PATH,
            ["dc_works.doi", "dc_work_rights.*"],
            "dc_work_creators.family_name = 'Calabrese'",
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.datacite.close()

    def test_counts(self):
        self.assertEqual(self.record_count("dc_works"), 1)
        self.assertEqual(self.record_count("dc_work_rights"), 2)
        self.assertEqual(
            self.cond_count("dc_work_rights", "rights_uri = 'info:eu-repo/semantics/openAccess'"), 1
        )

    def test_no_extra_fields(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("dc_works", "publisher", "true")

    def test_no_extra_tables(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("dc_work_creators", "name", "true")


class TestDatacitePopulateMultipleConditionColumns(PopulateQueries):
    """Verify non-works column specification and multiple conditions"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)

        cls.datacite = datacite.Datacite(td("data/datacite.tar.gz"))
        cls.datacite.populate(
            DATABASE_PATH,
            ["dc_work_titles.title"],
            "dc_works.doi = '10.14278/rodare.1950' AND dc_work_creators.given_name ='Abhishek' AND dc_work_subjects.subject = 'Disease outbreak'",
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.datacite.close()

    def test_counts(self):
        self.assertEqual(self.record_count("dc_work_titles"), 1)
        self.assertEqual(
            self.cond_count("dc_work_titles", "title='Software publication: Estimating cross-border mobility from the difference in peak-timing: A case study in Poland-Germany border regions'"), 1
        )

    def test_no_extra_fields(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("dc_works", "publisher", "true")

    def test_no_extra_tables(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("dc_work_creators", "name", "true")


class TestDataciteTransitiveClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # debug.set_flags(["sql"])
        cls.datacite = datacite.Datacite(
            td("data/datacite.tar.gz")
        )

    @classmethod
    def tearDownClass(cls):
        del cls.datacite

    def test_single(self):
        self.assertEqual(
            self.datacite.tables_transitive_closure(["dc_works"], "dc_works"),
            set(["dc_works"]),
        )

    def test_child(self):
        self.assertEqual(
            self.datacite.tables_transitive_closure(["dc_work_creators"], "dc_works"),
            set(["dc_works", "dc_work_creators"]),
        )

    def test_grandchild(self):
        self.assertEqual(
            self.datacite.tables_transitive_closure(
                ["dc_creator_affiliations"], "dc_works"
            ),
            set(["dc_works", "dc_work_creators", "dc_creator_affiliations"]),
        )

    def test_siblings(self):
        self.assertEqual(
            self.datacite.tables_transitive_closure(
                ["dc_work_creators", "dc_work_subjects"], "dc_works"
            ),
            set(["dc_works", "dc_work_creators", "dc_work_subjects"]),
        )
