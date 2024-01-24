#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2023-2024  Dibyendu Gupta
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
"""This process is to link authors with their affiliations (matched to their ror_id)."""
import time

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
        "distinct_author_affiliations",
        columns=[
            ColumnMeta("author_id"),
            ColumnMeta("affiliation_name"),
            ColumnMeta("gpt_name"),
            ColumnMeta("ror_id"),
        ],
    ),
    TableMeta(
        "valid_distinct_affiliations",
        columns=[
            ColumnMeta("id"),
            ColumnMeta("mentioned_name"),
            ColumnMeta("gpt_name"),
            ColumnMeta("city"),
            ColumnMeta("ror_id"),
        ],
    ),
]

# Note: whenever an organization is empty (""), distinguish_affiliations process assigns
# it to ror_id = 20233. The reason is ror_id (20233) is a research organization named "2B".
# So, Levenshtein distance assigns it 20233 as it is the shortest distance.
INVALID_ROR_ID = 20233


def process(database_path):
    """
    Process the specified database creating a table that links Crossref work authors to their
    corresponding research organization as codified in the Research Organization Registry (ROR)
    using distinguished affiliations by a LLM.

    The link is made to the lowest identifiable organizational level,
    e.g. an author's clinic, school, or institute.

    :param database_path: The path to the database
    """
    database = apsw.Connection(database_path)
    database.execute(
        log_sql("DROP TABLE IF EXISTS distinct_author_affiliations")
    )
    database.execute(
        log_sql("DROP TABLE IF EXISTS valid_distinct_affiliations")
    )
    database.execute(log_sql(tables[0].table_schema()))
    database.execute(log_sql(tables[1].table_schema()))
    set_fast_writing(database)
    ensure_table_exists(database, "author_affiliations")
    ensure_table_exists(database, "research_organizations")
    ensure_table_exists(database, "distinct_affiliations")

    insert_cursor = database.cursor()
    select_cursor = database.cursor()
    time_start = time.time()

    # Create a table of valid distinct affiliations (where gpt-4 generated name is not empty)
    for (
        valid_id,
        mentioned_name,
        gpt_name,
        city,
        ror_id,
    ) in select_cursor.execute(
        """
        SELECT id, mentioned_name, gpt_name, city, ror_id FROM distinct_affiliations
        WHERE ror_id != ?
        """,
        (INVALID_ROR_ID,),
    ):
        insert_cursor.execute(
            "INSERT INTO valid_distinct_affiliations VALUES (?, ?, ?, ?, ?)",
            (valid_id, mentioned_name, gpt_name, city, ror_id),
        )

    # Based on affiliation mentioned in crossref, link the author to their affiliations
    for (
        author_id,
        author_affiliation_name,
        gpt_name,
        ror_id,
    ) in select_cursor.execute(
        """
        SELECT aa.author_id, aa.name, vda.gpt_name, vda.ror_id  FROM author_affiliations aa
        JOIN valid_distinct_affiliations vda ON aa.name = vda.mentioned_name
        """
    ):
        insert_cursor.execute(
            "INSERT INTO distinct_author_affiliations VALUES (?, ?, ?, ?)",
            (author_id, author_affiliation_name, gpt_name, ror_id),
        )

    select_cursor.close()
    insert_cursor.close()
    time_end = time.time()
    print(f"link-aa-llm took {time_end - time_start} seconds")
    perf.log(
        "link-aa-llm has completed linking authors to gpt identified affiliations"
    )
