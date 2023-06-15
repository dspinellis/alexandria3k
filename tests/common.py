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
"""Functionality common to more than one test"""

import unittest

from alexandria3k.common import query_result


def record_count(g):
    """Return the elements (e.g. records) in generator g"""
    return sum(1 for _ in g)


class PopulateQueries(unittest.TestCase):
    """Common utility methods for testing database population.
    They expect the derived class to instantiate a cursor field."""

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
