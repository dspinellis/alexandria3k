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
"""main module test"""

import argparse
import sys
import unittest

sys.path.append("src")

from alexandria3k.__main__ import parse_cli_arguments, DOAJ_DEFAULT


class TestMain(unittest.TestCase):
    def test_expand_orcid_ok(self):
        args = parse_cli_arguments(
            argparse.ArgumentParser(),
            ["-d", "orcid", "od.tar.gz", "-p" "x.db"],
        )
        self.assertEqual(args.orcid, "od.tar.gz")

    def test_expand_doaj_ok(self):
        args = parse_cli_arguments(
            argparse.ArgumentParser(), ["-d", "doaj", "doaj.csv", "-p" "x.db"]
        )
        self.assertEqual(args.doaj, "doaj.csv")

    def test_expand_doaj_defalt(self):
        args = parse_cli_arguments(
            argparse.ArgumentParser(), ["-d", "doaj", "-p" "x.db"]
        )
        self.assertEqual(args.doaj, DOAJ_DEFAULT)
