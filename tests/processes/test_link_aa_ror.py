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
import sys
import unittest

import ahocorasick
import apsw

from ..test_dir import add_src_dir, td
add_src_dir()

from alexandria3k.common import ensure_unlinked, query_result
from alexandria3k.data_sources import ror, crossref
from alexandria3k.processes.link_aa_base_ror import (
    add_words,
    keep_unique_entries,
    link_author_affiliations,
)

DATABASE_PATH = td("tmp/ror.db")


class TestRorLink(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(DATABASE_PATH):
            os.unlink(DATABASE_PATH)

        cls.ror = ror.Ror(td("data/ror.zip"))
        cls.ror.populate(DATABASE_PATH)

        # Needed to test author-ror linking
        cls.crossref = crossref.Crossref(td("data/crossref-sample"))
        cls.crossref.populate(DATABASE_PATH)

        cls.con = apsw.Connection(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

        result = cls.cursor.execute(
            "SELECT Max(author_id) FROM author_affiliations"
        )
        (cls.author_id,) = result.fetchone()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.ror.close()
        cls.crossref.close()

    def get_ror_id_by_name(self, name):
        """Return the ROR id associated with the given name"""
        result = TestRorLink.cursor.execute(
            "SELECT id FROM research_organizations WHERE name = ?", [name]
        )
        return list(result)[0][0]

    def test_same(self):
        result = TestRorLink.cursor.execute(
            """DELETE FROM author_affiliations;
            INSERT INTO author_affiliations VALUES (?, ?, ?)""",
            (self.author_id, 1, "Swinburne University of Technology"),
        )
        link_author_affiliations(DATABASE_PATH, link_to_top=False)
        rows = list(
            TestRorLink.cursor.execute(
                "SELECT ror_id, work_author_id FROM work_authors_rors"
            )
        )
        self.assertEqual(len(rows), 1)
        sut_id = self.get_ror_id_by_name("Swinburne University of Technology")
        self.assertEqual(rows[0], (sut_id, self.author_id))

    def test_similar(self):
        result = TestRorLink.cursor.execute(
            """DELETE FROM author_affiliations;
            INSERT INTO author_affiliations VALUES (?, ?, ?)""",
            (
                self.author_id,
                1,
                "Department of Computing, Swinburne University of Technology, Australia",
            ),
        )
        link_author_affiliations(DATABASE_PATH, link_to_top=False)
        rows = list(
            TestRorLink.cursor.execute(
                "SELECT ror_id, work_author_id FROM work_authors_rors"
            )
        )
        self.assertEqual(len(rows), 1)
        sut_id = self.get_ror_id_by_name("Swinburne University of Technology")
        self.assertEqual(rows[0], (sut_id, self.author_id))

    def test_longest(self):
        result = TestRorLink.cursor.execute(
            """DELETE FROM author_affiliations;
            INSERT INTO author_affiliations VALUES (?, ?, ?)""",
            (
                self.author_id,
                1,
                "VU Lab, Swinburne University of Technology, Australia",
            ),
        )
        link_author_affiliations(DATABASE_PATH, link_to_top=False)
        rows = list(
            TestRorLink.cursor.execute(
                "SELECT ror_id, work_author_id FROM work_authors_rors"
            )
        )
        self.assertEqual(len(rows), 1)
        sut_id = self.get_ror_id_by_name("Swinburne University of Technology")
        self.assertEqual(rows[0], (sut_id, self.author_id))

    def test_base_link(self):
        result = TestRorLink.cursor.execute(
            """DELETE FROM author_affiliations;
            INSERT INTO author_affiliations VALUES (?, ?, ?)""",
            (self.author_id, 1, "Mount Stromlo Observatory"),
        )
        link_author_affiliations(DATABASE_PATH, link_to_top=False)
        rows = list(
            TestRorLink.cursor.execute(
                "SELECT ror_id, work_author_id FROM work_authors_rors"
            )
        )
        self.assertEqual(len(rows), 1)
        mso_id = self.get_ror_id_by_name("Mount Stromlo Observatory")
        self.assertEqual(rows[0], (mso_id, self.author_id))

    def test_top_link(self):
        result = TestRorLink.cursor.execute(
            """DELETE FROM author_affiliations;
            INSERT INTO author_affiliations VALUES (?, ?, ?)""",
            (self.author_id, 1, "Mount Stromlo Observatory"),
        )
        link_author_affiliations(DATABASE_PATH, link_to_top=True)
        rows = list(
            TestRorLink.cursor.execute(
                "SELECT ror_id, work_author_id FROM work_authors_rors"
            )
        )
        self.assertEqual(len(rows), 1)
        anu_id = self.get_ror_id_by_name("Australian National University")
        self.assertEqual(rows[0], (anu_id, self.author_id))


class TestUniqueEntries(unittest.TestCase):
    def test_unique_entries(self):
        def automaton_matches(automaton, name):
            """Return True if the automaton matches the specified name"""
            for i in automaton.iter(name):
                return True
            return False

        automaton = ahocorasick.Automaton()
        add_words(
            automaton,
            [
                (1, "ai"),
                (2, "Ministry of Foreign Affairs"),
                (3, "Ministry of Health"),
            ],
        )
        automaton.make_automaton()

        # Before unique
        self.assertTrue(automaton_matches(automaton, "The ai Institute"))
        self.assertTrue(
            automaton_matches(automaton, "Ministry of Foreign Affairs")
        )

        keep_unique_entries(automaton)
        automaton.make_automaton()

        # After unique
        self.assertFalse(automaton_matches(automaton, "The ai Institute"))
        self.assertTrue(
            automaton_matches(automaton, "Ministry of Foreign Affairs")
        )
