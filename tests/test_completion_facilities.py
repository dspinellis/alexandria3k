#
# Alexandria3k completion & facilities tests
# SPDX-License-Identifier: GPL-3.0-or-later
#
"""Tests for completion integration and facilities discovery.

These focus on:
- facilities.facility_names / facility_modules returning non-empty for known groups.
- add_completion_support augmenting a parser without raising exceptions.
- Generated parser exposing --print-completion when shtab is installed (best-effort: optional dependency).
"""
import argparse
import importlib
import os
import sys
import unittest

# Place project src on sys.path early (mirrors add_src_dir behavior)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from alexandria3k.facilities import facility_names, facility_modules  # type: ignore
from alexandria3k.completion import add_completion_support  # type: ignore


class TestFacilities(unittest.TestCase):
    def test_facility_modules_non_empty(self):
        # Expect at least one data source and one process module
        ds_mods = facility_modules("data_sources")
        proc_mods = facility_modules("processes")
        self.assertTrue(ds_mods, "data_sources modules list is empty")
        self.assertTrue(proc_mods, "processes modules list is empty")

    def test_facility_names_dash_conversion(self):
        # Names should be derived from modules with _ replaced by -
        mods = facility_modules("data_sources")
        names = facility_names("data_sources")
        self.assertEqual(sorted(n.replace('-', '_') for n in names), sorted(mods))


class TestCompletion(unittest.TestCase):
    def _build_parser(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        # Minimal fake subcommand to ensure subparsers exist
        subparsers.add_parser("dummy", help="dummy subcommand")
        add_completion_support(parser, subparsers)
        return parser

    def test_add_completion_support_no_error(self):
        parser = self._build_parser()
        # Ensure --print-completion option exists or was stubbed
        opts = {a.option_strings[0] for a in parser._actions if a.option_strings}  # pylint: disable=protected-access
        self.assertIn("--print-completion", opts)

    def test_completion_module_importable(self):
        # Import path should not trigger cyclic import errors
        mod = importlib.import_module("alexandria3k.completion")
        self.assertTrue(hasattr(mod, "add_completion_support"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
