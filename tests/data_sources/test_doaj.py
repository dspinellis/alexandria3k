#
# Alexandria3k FunderNames bibliographic metadata processing
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
"""doaj module test. This tests the basic import functionality and
the post-processing step.  The remaining functionality is tested by
the test_funder_names module."""

import csv
import os
import re
import sys
import sqlite3
import unittest

from ..test_dir import add_src_dir, td
add_src_dir()

from ..common import PopulateQueries, record_count
from alexandria3k.common import ensure_unlinked, query_result
from alexandria3k.data_sources import doaj

DATABASE_PATH = td("tmp/doaj.db")


class TestDoajPopulateVanilla(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        # debug.set_flags(["sql", "dump-matched"])

        cls.doaj = doaj.Doaj(td("data/doaj.csv"))
        cls.doaj.populate(DATABASE_PATH)
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.doaj.close()

    def test_counts(self):
        self.assertEqual(self.record_count("open_access_journals"), 9)

        self.assertEqual(
            self.record_count(
                """(SELECT DISTINCT publisher
          FROM open_access_journals WHERE name like 'A%')"""
            ),
            8,
        )


    def test_contents(self):
        self.assertEqual(
            self.cond_field(
                "open_access_journals", "name", "issn_print = '00016012'"
            ),
            "Acta Médica Costarricense",
        )
        self.assertEqual(
            self.cond_field(
                "open_access_journals", "article_records_number", "issn_print = '00016012'"
            ),
            1207,
        )
        self.assertEqual(
            self.cond_field(
                "open_access_journals", "most_recent_addition", "issn_print = '00016012'"
            ),
            "2015-12-08T15:06:43Z",
        )

class TestDoajPopulateColumns(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        # ensure_unlinked(DATABASE_PATH)
        # debug.set_flags(["sql", "dump-matched"])

        cls.doaj = doaj.Doaj(td("data/doaj.csv"))
        cls.doaj.populate( DATABASE_PATH, [
            "open_access_journals.name",
            "open_access_journals.issn_print"])
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.doaj.close()

    def test_contents(self):
        self.assertEqual(
            self.cond_field(
                "open_access_journals", "name", "issn_print = '00016012'"
            ),
            "Acta Médica Costarricense",
        )
