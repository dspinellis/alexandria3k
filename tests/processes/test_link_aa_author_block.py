#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2026  Diomidis Spinellis
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
"""Tests for author blocking"""
from alexandria3k.processes.link_aa_author_block import (
    make_blocking_key,
    blocking,
)
import os
import unittest
import apsw

from ..test_dir import add_src_dir, td
add_src_dir()



DATABASE_PATH = td("tmp/author_blocks.db")


class TestMakeBlockingKey(unittest.TestCase):
    # No database needed here
    # Each test calls make_blocking_key() directly with known inputs
    # and asserts the output matches what we expect

    def test_normal(self):
        # Input: normal first name and family name
        # Expected output: first initial + normalized family name
        self.assertEqual(make_blocking_key("John", "Smith"), "j.smith")

    def test_diacritics(self):
        # Input: name with accented characters
        # Expected output: diacritics stripped, normalized key
        self.assertEqual(make_blocking_key("José", "Müller"), "j.muller")

    def test_hyphenated_family(self):
        # Input: hyphenated family name
        # Expected output: hyphen replaced with space
        self.assertEqual(
            make_blocking_key("Mary", "Smith-Jones"), "m.smith jones"
        )

    def test_none_given(self):
        # Input: given name is None
        # Expected output: family name alone used as key
        self.assertEqual(make_blocking_key(None, "Smith"), "smith")

    def test_none_family(self):
        # Input: family name is None
        # Expected output: None, record should be skipped
        self.assertIsNone(make_blocking_key("John", None))

    def test_empty_family(self):
        # Input: family name is empty string
        # Expected output: None, record should be skipped
        self.assertIsNone(make_blocking_key("John", ""))

    def test_given_no_alpha(self):
        # Input: given name has no alphabetic characters e.g. "123"
        # Expected output: family name alone used as key
        self.assertEqual(make_blocking_key("123", "Smith"), "smith")


class TestBlocking(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # setUpClass runs once before all tests in this class
        # Input: nothing
        # Output: a fresh database at DATABASE_PATH with work_authors table

        if os.path.exists(DATABASE_PATH):
            os.unlink(DATABASE_PATH)
        # apsw.Connection creates a new SQLite database at the given path
        # Input: file path string
        # Output: database connection object
        cls.con = apsw.Connection(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

        # Create work_authors table manually
        # We only need the columns our blocking function queries
        # Input: SQL string
        # Output: table created in database
        cls.cursor.execute("""
            CREATE TABLE work_authors (
                id INTEGER,
                work_id INTEGER,
                given TEXT,
                family TEXT
            )
        """)

        # Insert test rows
        # Each row is one paper-level mention: (author_id, work_id, given, family)
        cls.cursor.execute("""
            INSERT INTO work_authors VALUES
            (1, 101, 'John', 'Smith'),
            (2, 102, 'James', 'Smith'),
            (3, 103, 'John', 'Doe'),
            (4, 104, NULL, 'Brown'),
            (5, 105, 'José', 'Müller')
        """)

    @classmethod
    def tearDownClass(cls):
        # tearDownClass runs once after all tests in this class
        # Closes connection and deletes the temp database
        cls.con.close()
        os.unlink(DATABASE_PATH)

    def test_block_count(self):
        # Input: database path
        # Output: dictionary of blocks
        # Assert: correct number of unique blocking keys created
        blocks = blocking(DATABASE_PATH)
        # j.smith, j.doe, brown, j.muller = 4 blocks
        self.assertEqual(len(blocks), 4)

    def test_smith_block(self):
        # Input: database path
        # Output: dictionary of blocks
        # Assert: both John Smith and James Smith land in same block
        blocks = blocking(DATABASE_PATH)
        self.assertIn("j.smith", blocks)
        self.assertEqual(len(blocks["j.smith"]), 2)

    def test_mention_tuples(self):
        # Assert: each mention is stored as (author_id, work_id) tuple
        blocks = blocking(DATABASE_PATH)
        self.assertIn((1, 101), blocks["j.smith"])
        self.assertIn((2, 102), blocks["j.smith"])

    def test_null_given_name(self):
        # Assert: author with NULL given name uses family name as key
        blocks = blocking(DATABASE_PATH)
        self.assertIn("brown", blocks)

    def test_diacritics_normalized(self):
        # Assert: José Müller normalized correctly to j.muller
        blocks = blocking(DATABASE_PATH)
        self.assertIn("j.muller", blocks)


if __name__ == "__main__":
    unittest.main()
