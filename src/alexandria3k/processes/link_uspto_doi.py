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
"""Link USPTO non-patent literature citations with their DOI"""

import re

# pylint: disable-next=import-error
import apsw

from alexandria3k.common import (
    ensure_table_exists,
    log_sql,
    set_fast_writing,
)
from alexandria3k import perf
from alexandria3k.db_schema import ColumnMeta, TableMeta

tables = [
    TableMeta(
        "usp_nplcit_dois",
        columns=[
            ColumnMeta("patent_id"),
            ColumnMeta("nplcit_num"),
            ColumnMeta("doi"),
        ],
    ),
]


def link_uspto_doi(database_path):
    """
    Process the specified database creating a table that links US patent
    non-patent citations with their DOIs extracted from the citation
    free text.

    :param database_path: The path specifying the SQLite database
        to process and populate.
        The database shall already contain the usp_citations table
        of the USPTO dataset with the patent_id, nplcit_num, and
        nplcit_othercit fields.
    :type database_path: str
    """
    database = apsw.Connection(database_path)
    database.execute(log_sql("DROP TABLE IF EXISTS usp_nplcit_dois"))
    database.execute(log_sql(tables[0].table_schema()))
    set_fast_writing(database)
    ensure_table_exists(database, "usp_citations")

    select_cursor = database.cursor()
    insert_cursor = database.cursor()

    dois_added = 0
    doi_matcher = re.compile(r"((doi: *)|(doi\.org/))([^,; )>]+)", re.I)
    valid_doi = re.compile(r"^10\.\d{4,9}/..")
    perf.log("link_uspto_doi SELECT")
    for patent_id, nplcit_num, text in select_cursor.execute(
        """
        SELECT patent_id, nplcit_num, nplcit_othercit FROM
          usp_citations WHERE
          nplcit_othercit LIKE '%DOI:%' OR nplcit_othercit LIKE '%doi.org/%'
      """
    ):
        match = doi_matcher.search(text)
        if not match:
            continue
        doi = match.group(4)

        # Sometimes the doi: is followed by a DOI URL
        match2 = doi_matcher.search(doi)
        if match2:
            doi = match2.group(4)

        # Remove trailing ., which is typically part of the citation sentence
        if doi.endswith("."):
            doi = doi[:-1]

        # Homogenize
        doi = doi.lower()

        # Verify that the prefix follows the DOI standard
        if not valid_doi.match(doi):
            continue

        insert_cursor.execute(
            "INSERT INTO usp_nplcit_dois VALUES(?, ?, ?)",
            (patent_id, nplcit_num, doi),
            prepare_flags=apsw.SQLITE_PREPARE_PERSISTENT,
        )
        dois_added += 1
    select_cursor.close()
    insert_cursor.close()
    perf.log(f"link_uspto_doi added {dois_added} DOIs")


def process(database_path):
    """
    Process the specified database creating a table that links US patent
    non-patent citations with their DOIs extracted from the citation
    free text.

    :param database_path: The path specifying the SQLite database
        to process and populate.
        The database shall already contain the usp_citations table
        of the USPTO dataset with the patent_id, nplcit_num, and
        nplcit_othercit fields.
    :type database_path: str
    """

    link_uspto_doi(database_path)
