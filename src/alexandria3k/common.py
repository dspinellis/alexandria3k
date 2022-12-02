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


def set_fast_writing(db):
    """
    Very fast inserts at the risk of possible data corruption in case of a
    crash.
    We don't really care, because we assume the databased is
    populated in one go from empty, and if it gets corrupted
    the process can be repeated.
    This increases speed in ORCID works population by 50:
    from 845291 / 2 records in 16980 s (40 ms / record) to
    3225659 / 2 records in 1292 s (800 μs / record).
    It also reduces the time required to run the Crossref tests from 994 ms
    to 372 ms.
    See https://stackoverflow.com/a/58547438/20520 for measurements behind this
    approach.
    """
    db.execute("PRAGMA synchronous = OFF")
    db.execute("PRAGMA journal_mode = OFF")
    db.execute("PRAGMA locking_mode = EXCLuSIVE")
