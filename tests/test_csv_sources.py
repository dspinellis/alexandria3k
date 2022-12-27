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
"""csv_sources module test"""

import codecs
import csv
import re
import sys
import unittest

sys.path.append("src")

from alexandria3k import csv_sources


class TestCsvSources(unittest.TestCase):
    def test_record_source(self):
        gen = csv_sources.record_source('tests/data/titleFile.csv', ",")
        row = next(gen)
        self.assertTrue("18435912" in row)
        self.assertTrue("10.36801/apme" in row)
