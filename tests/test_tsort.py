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
"""Topological sort of database tables unit tests"""

import unittest
import sys

sys.path.append("src")

from alexandria3k.tsort import tsort
from alexandria3k.crossref import get_table_meta_by_name


def tsort_add_meta(table_names):
    """Add Crossref metadata and call tsort"""
    tables_meta = [get_table_meta_by_name(t) for t in table_names]
    return tsort(tables_meta, table_names)


class TestTsort(unittest.TestCase):
    def test_top(self):
        self.assertEqual(
            tsort_add_meta(["works"]),
            ["works"],
        )

    def test_single_other(self):
        self.assertEqual(
            tsort_add_meta(["author_affiliations"]),
            ["author_affiliations"],
        )

    def test_two_sorted(self):
        self.assertEqual(
            tsort_add_meta(
                [
                    "works",
                    "work_authors",
                ]
            ),
            [
                "works",
                "work_authors",
            ],
        )

    def test_two_unsorted(self):
        self.assertEqual(
            tsort_add_meta(
                [
                    "work_authors",
                    "works",
                ]
            ),
            [
                "works",
                "work_authors",
            ],
        )

    def test_three_unsorted(self):
        self.assertEqual(
            tsort_add_meta(
                [
                    "author_affiliations",
                    "work_authors",
                    "works",
                ]
            ),
            [
                "works",
                "work_authors",
                "author_affiliations",
            ],
        )

    def test_no_top(self):
        self.assertEqual(
            tsort_add_meta(
                [
                    "author_affiliations",
                    "work_authors",
                ]
            ),
            [
                "work_authors",
                "author_affiliations",
            ],
        )

    def test_orphan_siblings(self):
        # Order not guaranteed; compare sets
        self.assertEqual(
            set(
                tsort_add_meta(
                    [
                        "work_subjects",
                        "work_authors",
                    ]
                )
            ),
            {
                "work_authors",
                "work_subjects",
            },
        )

    def test_two_siblings_of_same_parent(self):
        # Order not guaranteed
        result = tsort_add_meta(
            [
                "work_subjects",
                "works",
                "work_authors",
            ]
        )
        self.assertEqual(
            len(result),
            3,
        )
        self.assertEqual(
            result[0],
            "works",
        )
        # Order not guaranteed; compare sets
        self.assertEqual(
            set(result[1:]),
            {
                "work_authors",
                "work_subjects",
            },
        )
