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

import io
import unittest
from unittest.mock import patch

from .test_dir import add_src_dir, td
add_src_dir()

from alexandria3k.__main__ import class_name, main, module_get_attribute
from alexandria3k.data_sources.asjcs import DEFAULT_SOURCE


class TestMain(unittest.TestCase):
    def test_module_get_attribute(self):
        default = module_get_attribute("data_sources.asjcs", "DEFAULT_SOURCE")
        self.assertEqual(DEFAULT_SOURCE, default)

    def test_class_name(self):
        self.assertEqual(class_name("funder-names"), "FunderNames")

    @patch("alexandria3k.__main__.signal.signal")
    @patch("alexandria3k.__main__.error_raising_main")
    def test_main_keyboard_interrupt_exits_without_traceback(
        self, mock_error_raising_main, _mock_signal
    ):
        mock_error_raising_main.side_effect = KeyboardInterrupt
        stderr = io.StringIO()

        with patch("sys.stderr", stderr), self.assertRaises(SystemExit) as cm:
            main()

        self.assertEqual(cm.exception.code, 130)
        self.assertEqual(stderr.getvalue(), "")

    @patch("alexandria3k.__main__.signal.signal")
    @patch("alexandria3k.__main__.error_raising_main")
    def test_main_broken_pipe_exits_without_traceback(
        self, mock_error_raising_main, _mock_signal
    ):
        mock_error_raising_main.side_effect = BrokenPipeError
        stdout = io.StringIO()
        stderr = io.StringIO()

        with (
            patch("sys.stdout", stdout),
            patch("sys.stderr", stderr),
            self.assertRaises(SystemExit) as cm,
        ):
            main()

        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(stderr.getvalue(), "")
