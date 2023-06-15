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

from alexandria3k import debug


RE_URL = re.compile(r"\w+://")


def is_unittest():
    """Return True if the routine is executed in a unit test."""
    return any(
        "unittest" in str(cls)
        # pylint: disable-next=protected-access
        for cls in sys._getframe(1).f_globals.values()
    )


def warn(message):
    """
    Output a warning on the standard error stream with the specified message.

    :param message: The message to output.
    :type message: str
    """
    if is_unittest():
        return
    print(f"Warning: {message}", file=sys.stderr)


def fail(message):
    """
    Output an error message on the standard error stream with the specified
    message.
    Terminate the program's execution with an exit code of 1.

    :param message: The message to output.
    :type message: str
    """
    if debug.enabled("exception"):
        # pylint: disable-next=broad-exception-raised
        raise Exception(message)
    print(f"Error: {message}", file=sys.stderr)
    print("Terminating program execution.", file=sys.stderr)
    sys.exit(1)


def ensure_unlinked(file_path):
    """Ensure that the file at the specified path does not exist
    by unlinking it, if needed.

    :param file_path: Path to the file that must not exist.
    :type file_path: str
    """
    if os.path.exists(file_path):
        os.unlink(file_path)


def query_result(cursor, query):
    """
    Return the result of executing the specified query.

    :param cursor: Database cursor to use for executing the query.
    :type cursor: Cursor

    :param query: The query to execute.
    :type query: str
    """
    result_set = cursor.execute(query)
    (result,) = result_set.fetchone()
    return result


def table_exists(cursor, table_name):
    """
    Return True if the specified database table exists.

    :param cursor: Database cursor to use for executing the required query.
    :type cursor: Cursor

    :param table_name: The table to check for existence.
    :type table_name: str
    """
    try:
        cursor.execute(f"SELECT Count(*) FROM {table_name}")
        return True
    except (sqlite3.OperationalError, apsw.SQLError):
        return False


def ensure_table_exists(connection, table_name):
    """
    Terminate the program with an error message if the specified table
    does not exist.

    :param connection: The database connection to use for checking the
        table's existence.
    :type connection: Connection

    :param table_name: The table to check for existence.
    :type table_name: str
    """
    cursor = connection.cursor()
    if not table_exists(cursor, table_name):
        fail(f"The required table '{table_name}' is not populated.")


def set_fast_writing(database):
    """
    Implement very fast database inserts at the risk of possible data
    corruption in case of a crash.
    We don't really care, because we assume the database is
    populated in one go from empty, and if it gets corrupted
    the process can be repeated.
    This increases speed in ORCID works population by 50:
    from 845291 / 2 records in 16980 s (40 ms / record) to
    3225659 / 2 records in 1292 s (800 μs / record).
    It also reduces the time required to run the Crossref tests from 994 ms
    to 372 ms.
    See https://stackoverflow.com/a/58547438/20520 for measurements behind this
    approach.

    :param database: Connection to the database to configure.
    :type database: Connection
    """
    database.execute("PRAGMA synchronous = OFF")
    database.execute("PRAGMA journal_mode = OFF")
    database.execute("PRAGMA locking_mode = EXCLuSIVE")


def log_sql(statement):
    """
    Return the specified SQL statement. If "sql" is set,
    output a copy of the statement on the standard output.

    :param statement: The statement that will ne executed.
    :type statement: str
    """
    debug.log("sql", statement)
    return statement


def program_version():
    """Return a string identifying the program's version."""
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
    """
    Return true if url looks like a URL.

    :param url: The URL to match
    :type url: str
    """
    return RE_URL.match(url)


def data_from_uri_provider(source):
    """
    Given a file path, a URL, or this package's resource path
    return a readable source for its contents.

    :param source: A file path, a URL, or an internal data source starting
        with `resource:`.
    :type source: str
    """
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
    """
    Return the contents of the named file relative to the package's
    source code directory.

    :param file_path: The file's file path relative to the `src/alexandria3k`
        directory.
    :type file_path: str
    """
    return str(pkgutil.get_data(__name__, file_path), "utf-8")


def remove_sqlite_comments(script):
    """Remove SQLite comments (-- and C-style) from the passed script.
    This cannot handle comment characters embedded in strings.

    :param script: An SQL script, possibly multi-line, possibly containing
        C-style block comments (`/* ... */`).
    :type script: str
    """

    # remove C-style comments
    script = re.sub(r"/\*.*?\*/", "", script, flags=re.DOTALL)

    # remove SQL single-line comments
    return re.sub(r"--[^\n]*\n?", "", script).strip()
