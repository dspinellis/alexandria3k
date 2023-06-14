#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2022-2023  Diomidis Spinellis
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
"""Link works with their ASJC subject codes"""

import sqlite3

from alexandria3k.common import (
    ensure_table_exists,
    get_string_resource,
)
from alexandria3k import perf
from alexandria3k.db_schema import ColumnMeta, TableMeta


tables = [
    TableMeta(
        "works_asjcs",
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("asjc_id"),
        ],
    )
]


def process(database_path):
    """
    Create a many to many table linking Crossref works with Scopus
    All Science Journal Classification Codes — ASJCs.

    :param database_path: The path specifying the SQLite database
        to process and populate.
        The database shall already contain the ASJC dataset and the Crossref
        `work_subjects` table.
    :type database_path: str
    """
    connection = sqlite3.connect(database_path)
    ensure_table_exists(connection, "work_subjects")
    ensure_table_exists(connection, "asjcs")
    script = get_string_resource("sql/link-works-asjcs.sql")
    cursor = connection.cursor()
    cursor.executescript(script)
    perf.log("link_works_asjcs")
