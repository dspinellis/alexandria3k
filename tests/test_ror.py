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

sys.path.append("src")

from alexandria3k.common import ensure_unlinked, query_result
from alexandria3k import ror, crossref

DATABASE_PATH = "tests/tmp/ror.db"


class TestRorPopulate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(DATABASE_PATH):
            os.unlink(DATABASE_PATH)

        ror.populate("tests/data/ror.zip", DATABASE_PATH)

        cls.con = apsw.Connection(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)

    def test_import(self):
        result = TestRorPopulate.cursor.execute(
            "SELECT Count(*) from research_organizations"
        )
        (count,) = result.fetchone()
        self.assertEqual(count, 28)

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
            country_code,
        ) = result.fetchone()
        self.assertEqual(id, 1)
        self.assertEqual(ror_path, "019wvm592")
        self.assertEqual(name, "Australian National University")
        self.assertEqual(status, "active")
        self.assertEqual(established, 1946)
        self.assertEqual(country_code, "AU")

    def test_funder_ids(self):
        result = TestRorPopulate.cursor.execute(
            "SELECT funder_id FROM ror_funder_ids WHERE ror_id=2"
        )
        rows = list(result)
        self.assertEqual(len(rows), 6)
        self.assertTrue(("501100001779",) in rows)
        self.assertTrue(("501100006532",) in rows)

    def test_ror_types(self):
        result = TestRorPopulate.cursor.execute(
            "SELECT type FROM ror_types WHERE ror_id=2"
        )
        rows = list(result)
        self.assertEqual(len(rows), 1)
        self.assertTrue(("Education",) in rows)

    def test_ror_links(self):
        result = TestRorPopulate.cursor.execute(
            "SELECT link FROM ror_links WHERE ror_id=2"
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
            "SELECT type, ror_path FROM ror_relationships WHERE ror_id=2"
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

    def test_ror_addresses(self):
        result = TestRorPopulate.cursor.execute(
            "SELECT * FROM ror_addresses WHERE ror_id=2"
        )
        rows = list(result)
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
        result = TestRorPopulate.cursor.execute(
            "SELECT wikidata_id FROM ror_wikidata_ids WHERE ror_id=2"
        )
        rows = list(result)
        self.assertEqual(len(rows), 1)
        self.assertTrue(("Q598841",) in rows)

    def test_ror_isnis(self):
        result = TestRorPopulate.cursor.execute(
            "SELECT isni FROM ror_isnis WHERE ror_id=2"
        )
        rows = list(result)
        self.assertEqual(len(rows), 1)
        self.assertTrue(("0000 0004 1936 7857",) in rows)


class TestRorLink(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(DATABASE_PATH):
            os.unlink(DATABASE_PATH)

        ror.populate("tests/data/ror.zip", DATABASE_PATH)

        # Needed to test author-ror linking
        cls.crossref = crossref.Crossref("tests/data/sample")
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
        ror.link_author_affiliations(DATABASE_PATH, link_to_top=False)
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
        ror.link_author_affiliations(DATABASE_PATH, link_to_top=False)
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
        ror.link_author_affiliations(DATABASE_PATH, link_to_top=False)
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
        ror.link_author_affiliations(DATABASE_PATH, link_to_top=False)
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
        ror.link_author_affiliations(DATABASE_PATH, link_to_top=True)
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
        ror.add_words(
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

        ror.keep_unique_entries(automaton)
        automaton.make_automaton()

        # After unique
        self.assertFalse(automaton_matches(automaton, "The ai Institute"))
        self.assertTrue(
            automaton_matches(automaton, "Ministry of Foreign Affairs")
        )
