#
# Alexandria3k Pubmed bibliographic metadata processing
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
"""Pubmed import integration tests"""

import os
import sqlite3

from ..test_dir import add_src_dir, td

add_src_dir()

from alexandria3k import debug
from alexandria3k.common import ensure_unlinked
from alexandria3k.data_sources import pubmed
from alexandria3k.file_cache import FileCache

from ..common import PopulateQueries, record_count

DATABASE_PATH = td("tmp/pubmed.db")


class TestPubmedPopulateVanilla(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0
        # debug.set_flags(["sql", "dump-matched"])

        cls.pubmed = pubmed.Pubmed(td("data/pubmed-sample"))
        cls.pubmed.populate(DATABASE_PATH)
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)

    def test_counts(self):
        self.assertEqual(self.record_count("pubmed_articles"), 13)

        self.assertEqual(
            self.record_count(
                """(SELECT DISTINCT publisher_item_identifier_article_id
          FROM pubmed_articles WHERE publisher_item_identifier_article_id is not null)"""
            ),
            12,
        )

    def test_articles_contents(self):
        self.assertEqual(
            self.cond_field("pubmed_articles", "journal_title", "id = '36464820'"),
            "Clinical endoscopy",
        )
        self.assertEqual(
            self.cond_field("pubmed_articles", "doi", "id = '36464820'"),
            "10.5946/ce.2022.114",
        )


class TestPubmedPopulateMasterColumnCondition(PopulateQueries):
    """Verify column specification and population of single table"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.file_reads = 0

        # debug.set_flags(["sql"])
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

    def test_counts(self):
        self.assertEqual(self.record_count("pubmed_articles"), 2)
