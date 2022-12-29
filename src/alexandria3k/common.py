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

try:
    from importlib import metadata
except ImportError:  # for Python<3.8
    import importlib_metadata as metadata
from io import BytesIO
import os
import pkgutil
import re
import sqlite3
import subprocess
import sys
import urllib.request

# pylint: disable-next=import-error
import apsw

from . import debug


RE_URL = re.compile(r"\w+://")


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


def table_exists(cursor, table_name):
    """Return True if the specified table exists"""
    try:
        cursor.execute(f"SELECT Count(*) FROM {table_name}")
        return True
    except (sqlite3.OperationalError, apsw.SQLError):
        return False


def ensure_table_exists(connection, table_name):
    """Terminate the program with an error message if the specified table
    does not exist"""
    cursor = connection.cursor()
    if not table_exists(cursor, table_name):
        fail(f"The required table '{table_name}' is not populated.")


def set_fast_writing(database):
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
    database.execute("PRAGMA synchronous = OFF")
    database.execute("PRAGMA journal_mode = OFF")
    database.execute("PRAGMA locking_mode = EXCLuSIVE")


def log_sql(statement):
    """Return the specified SQL statement. If "log-sql" is set,
    output a copy of the statement on the standard output"""
    debug.log("log-sql", statement)
    return statement


def add_columns(columns, tables, add_column):
    """Call add column for each specified column or for all tables if columns
    is not defined"""

    # By default include all tables and columns
    if not columns:
        columns = []
        for table in tables:
            columns.append(f"{table.get_name()}.*")

    # A dictionary of columns to be populated for each table
    for col in columns:
        try:
            (table, column) = col.split(".")
        except ValueError:
            fail(
                f"Invalid column specification: '{col}'; expected table.column or table.*."
            )
        add_column(table, column)


def program_version():
    """Return a string identifying the program's version"""
    try:
        # Installed version
        return metadata.version("alexandria3k")
    except metadata.PackageNotFoundError:
        # Obtain development version through Git
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            stdout=subprocess.PIPE,
            check=True,
        )
        return res.stdout.decode("utf-8").strip()


def is_url(url):
    """Return true if url looks like a URL"""
    return RE_URL.match(url)


def data_source(source):
    """Given a file path, a URL, or this package's resource path
    return a readable source for its contents"""
    if source.startswith("resource:"):
        (_, file_path) = source.split(":")
        return BytesIO(pkgutil.get_data(__name__, file_path))
    try:
        if is_url(source):
            req = urllib.request.Request(
                source,
                headers={"User-Agent": f"alexandria3k {program_version()}"},
            )
            return urllib.request.urlopen(req)
        return open(source, "rb")
    # pylint: disable-next=broad-except
    except Exception as exception:
        fail(f"Unable to read data from '{source}': {exception}.")
        # NOTREACHED
        return None


def get_string_resource(file_path):
    """Return the contents of the named file relative to the package's
    source code directory"""
    return str(pkgutil.get_data(__name__, file_path), "utf-8")
