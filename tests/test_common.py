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
"""common module test"""

import re
import sys
import unittest

sys.path.append("src")

from alexandria3k import common


class TestCommon(unittest.TestCase):
    def test_program_version(self):
        version = common.program_version()
        expected_regex = re.compile(r"(([0-9a-f]{6,})|(\d+\.\d+\.\d+))")
        self.assertTrue(expected_regex.fullmatch(version), f"Invalid version string [{version}]")

    def test_is_url(self):
        self.assertTrue(common.is_url("https://www.example.com/foo"))
        self.assertFalse(common.is_url("foo.csv"))

