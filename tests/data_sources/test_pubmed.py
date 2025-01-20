#
# Alexandria3k PubMed bibliographic metadata processing
# Copyright (C) 2023 Bas Verlooy
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
"""PubMed import integration tests"""

import os
import sqlite3
import unittest

from ..test_dir import add_src_dir, td

add_src_dir()

from alexandria3k import debug
from alexandria3k.common import ensure_unlinked
from alexandria3k.data_sources import pubmed
from alexandria3k.file_pubmed_cache import FileCache

from ..common import PopulateQueries, record_count

DATABASE_PATH = td("tmp/pubmed.db")
ATTACHED_DATABASE_PATH = td("tmp/attached_pubmed.db")


def populate_attached():
    """Create and populate an attached database"""
    ensure_unlinked(ATTACHED_DATABASE_PATH)
    attached = sqlite3.connect(ATTACHED_DATABASE_PATH)
    attached.execute("CREATE TABLE s_pubmed_articles(pubmed_id)")
    attached.execute("INSERT INTO s_pubmed_articles VALUES('36464820')")
    attached.commit()
    attached.close()


class TestPubmedPopulateVanilla(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0

        cls.pubmed = pubmed.Pubmed(td("data/pubmed-sample"))
        cls.pubmed.populate(DATABASE_PATH)
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.pubmed.close()

    def test_counts(self):
        self.assertEqual(self.record_count("pubmed_articles"), 12)
        self.assertEqual(self.record_count("pubmed_authors"), 49)
        self.assertEqual(self.record_count("pubmed_author_affiliations"), 37)
        self.assertEqual(self.record_count("pubmed_abstracts"), 7)
        self.assertEqual(self.record_count("pubmed_other_abstracts"), 1)
        self.assertEqual(self.record_count("pubmed_other_abstract_texts"), 1)
        self.assertEqual(self.record_count("pubmed_history"), 49)
        self.assertEqual(self.record_count("pubmed_chemicals"), 12)
        self.assertEqual(self.record_count("pubmed_meshs"), 54)
        self.assertEqual(self.record_count("pubmed_comments_corrections"), 2)
        self.assertEqual(self.record_count("pubmed_keywords"), 7)
        self.assertEqual(self.record_count("pubmed_grants"), 2)
        self.assertEqual(self.record_count("pubmed_publication_types"), 22)
        self.assertEqual(self.record_count("pubmed_references"), 51)
        self.assertEqual(self.record_count("pubmed_reference_articles"), 17)
        self.assertEqual(self.record_count("pubmed_supplement_meshs"), 1)
        self.assertEqual(self.record_count("pubmed_data_banks"), 1)
        self.assertEqual(self.record_count("pubmed_data_bank_accessions"), 1)
        self.assertEqual(self.record_count("pubmed_investigators"), 2)
        self.assertEqual(self.record_count("pubmed_investigator_affiliations"), 2)

        self.assertEqual(
            self.record_count(
                """(SELECT DISTINCT publisher_item_identifier_article_id
          FROM pubmed_articles WHERE publisher_item_identifier_article_id is not null)"""
            ),
            9,
        )
        self.assertEqual(FileCache.file_reads, 5)

    def test_articles_contents(self):
        self.assertEqual(
            self.cond_field(
                "pubmed_articles", "journal_title", "pubmed_id = '36464820'"
            ),
            "Clinical endoscopy",
        )
        self.assertEqual(
            self.cond_field("pubmed_articles", "doi", "pubmed_id = '36464820'"),
            "10.5946/ce.2022.114",
        )
        self.assertEqual(
            self.cond_field(
                "pubmed_articles", "journal_year", "pubmed_id = '36464820'"
            ),
            2022,
        )
        self.assertEqual(
            self.cond_field(
                "pubmed_articles", "publication_status", "pubmed_id = '36464820'"
            ),
            "ppublish",
        )
        self.assertEqual(
            self.cond_field("pubmed_articles", "pagination", "pubmed_id = '36464829'"),
            "819-823",
        )
        self.assertEqual(
            self.cond_field("pubmed_articles", "doi", "pubmed_id = '36464829'"),
            "10.5946/ce.2021.278",
        )
        self.assertEqual(
            self.cond_field("pubmed_authors", "family", "given = 'David R'"), "Elwood"
        )

    def test_author_orcid(self):
        """Test that both ORCID with and without URL prefix are accepted"""
        self.assertEqual(
            self.cond_field(
                "pubmed_authors", "identifier", "given = 'A' AND family = 'Flach'"
            ),
            "0000-0002-4314-996X",
        )
        self.assertEqual(
            self.cond_field(
                "pubmed_authors", "identifier", "given = 'I' AND family = 'Wood'"
            ),
            "0000-0001-4314-996X",
        )


class TestPubmedPopulateMasterCondition(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(DATABASE_PATH):
            os.unlink(DATABASE_PATH)

        FileCache.file_reads = 0
        cls.pubmed = pubmed.Pubmed(td("data/pubmed-sample"))
        cls.pubmed.populate(
            DATABASE_PATH, None, "pubmed_articles.pubmed_id = '36464820'"
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.pubmed.close()

    def test_counts(self):
        self.assertEqual(self.record_count("pubmed_articles"), 1)
        self.assertEqual(self.record_count("pubmed_authors"), 7)
        self.assertEqual(self.record_count("pubmed_abstracts"), 1)
        self.assertEqual(FileCache.file_reads, 5)


class TestPubmedPopulateMasterColumnNoCondition(PopulateQueries):
    """Verify column specification and population of root table"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0

        cls.pubmed = pubmed.Pubmed(td("data/pubmed-sample"))
        cls.pubmed.populate(DATABASE_PATH, ["pubmed_articles.pubmed_id"])
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.pubmed.close()

    def test_counts(self):
        self.assertEqual(self.record_count("pubmed_articles"), 12)
        self.assertEqual(FileCache.file_reads, 5)

    def test_no_extra_fields(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("pubmed_articles", "doi", "true")

    def test_no_extra_tables(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("pubmed_titles", "class_level", "true")


class TestPubmedPopulateMasterColumnCondition(PopulateQueries):
    """Verify column specification and population of single table"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0

        cls.pubmed = pubmed.Pubmed(td("data/pubmed-sample"))
        cls.pubmed.populate(
            DATABASE_PATH,
            ["pubmed_articles.doi"],
            "pubmed_articles.revised_year BETWEEN 2018 AND 2020",
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.pubmed.close()

    def test_counts(self):
        self.assertEqual(self.record_count("pubmed_articles"), 5)

    def test_no_extra_fields(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("pubmed_articles", "country", "true")

    def test_no_extra_tables(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("pubmed_keywords", "owner", "true")


class TestPubmedPopulateDetailConditionColumn(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0

        cls.pubmed = pubmed.Pubmed(td("data/pubmed-sample"))
        cls.pubmed.populate(
            DATABASE_PATH,
            ["pubmed_articles.id", "pubmed_authors.*"],
            "pubmed_authors.given == 'Dehuan'",
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.pubmed.close()

    def test_pubmed_counts(self):
        self.assertEqual(self.record_count("pubmed_articles"), 1)
        self.assertEqual(self.record_count("pubmed_authors"), 9)
        self.assertEqual(FileCache.file_reads, 5)

    def test_no_extra_fields(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("pubmed_articles", "country", "true")

    def test_no_extra_tables(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("pubmed_keywords", "owner", "true")


class TestPubmedPopulateMultipleConditionColumn(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0

        cls.pubmed = pubmed.Pubmed(td("data/pubmed-sample"))
        cls.pubmed.populate(
            DATABASE_PATH,
            ["pubmed_articles.id", "pubmed_authors.*"],
            "pubmed_articles.journal_year = 2022 AND pubmed_publication_types.unique_identifier = 'D016422' AND pubmed_investigators.family = 'Bonten'",
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.pubmed.close()

    def test_counts(self):
        self.assertEqual(self.record_count("pubmed_articles"), 1)
        self.assertEqual(self.cond_count("pubmed_authors", "family = 'Jing'"), 1)
        self.assertEqual(FileCache.file_reads, 5)

    def test_no_extra_fields(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("pubmed_articles", "country", "true")

    def test_no_extra_tables(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("pubmed_keywords", "owner", "true")


class TestPubmedQuery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        populate_attached()

        cls.pubmed = pubmed.Pubmed(
            td("data/pubmed-sample"),
            attach_databases=[f"attached:{ATTACHED_DATABASE_PATH}"],
        )

    @classmethod
    def tearDownClass(cls):
        del cls.pubmed
        os.unlink(ATTACHED_DATABASE_PATH)

    def test_articles(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.pubmed.query("SELECT * FROM pubmed_articles", partition)
                ),
                12,
            )

    def test_articles_attached(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.pubmed.query(
                        """SELECT * FROM pubmed_articles WHERE EXISTS (
                        SELECT 1 FROM attached.s_pubmed_articles
                        WHERE pubmed_articles.pubmed_id = s_pubmed_articles.pubmed_id
                        )""",
                        partition,
                    )
                ),
                1,
            )

    def test_authors(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.pubmed.query("SELECT * FROM pubmed_authors", partition)
                ),
                49,
            )

    def test_articles_condition(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.pubmed.query(
                        "SELECT pubmed_authors.* FROM pubmed_articles LEFT JOIN pubmed_authors ON pubmed_authors.article_id = pubmed_articles.id WHERE pubmed_articles.pubmed_id = '36464820'",
                        partition,
                    )
                ),
                7,
            )

    def test_articles_column_subset_condition(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.pubmed.query(
                        "SELECT pubmed_articles.pubmed_id, pubmed_authors.given FROM pubmed_articles LEFT JOIN pubmed_authors ON pubmed_authors.article_id = pubmed_articles.id WHERE pubmed_articles.pubmed_id = '36464820'",
                        partition,
                    )
                ),
                7,
            )


class TestPubmedPopulateAttachedDatabaseCondition(PopulateQueries):
    """Verify column specification and population of single table"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0
        populate_attached()

        cls.pubmed = pubmed.Pubmed(
            td("data/pubmed-sample"),
            attach_databases=[f"attached:{ATTACHED_DATABASE_PATH}"],
        )
        cls.pubmed.populate(
            DATABASE_PATH,
            ["pubmed_articles.pubmed_id"],
            "EXISTS (SELECT 1 FROM attached.s_pubmed_articles WHERE pubmed_articles.pubmed_id = s_pubmed_articles.pubmed_id)",
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        os.unlink(ATTACHED_DATABASE_PATH)
        cls.pubmed.close()

    def test_counts(self):
        self.assertEqual(self.record_count("pubmed_articles"), 1)
        self.assertEqual(FileCache.file_reads, 5)
