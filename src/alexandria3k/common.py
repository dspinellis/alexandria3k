#!/usr/bin/env python3
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
"""Functions common to multiple modules"""

import os
import sys


def fail(message):
    """Fail the program execution with the specified error message"""
    print(message, file=sys.stderr)
    sys.exit(1)


def ensure_unlinked(file_path):
    """Ensure that the file at the specified path does not exist"""
    if os.path.exists(file_path):
        os.unlink(file_path)


def query_result(cursor, query):
    """Return the result of executing the specified query"""
    result_set = cursor.execute(query)
    (result,) = result_set.fetchone()
    return result
