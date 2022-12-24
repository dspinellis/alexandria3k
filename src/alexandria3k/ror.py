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
"""Populate ROR (Research Organization Registry) data tables"""

import json
import zipfile

# pylint: disable-next=import-error
import apsw

from .common import log_sql, set_fast_writing
from . import perf
from .virtual_db import ColumnMeta, TableFiller, TableMeta


def external_ids_all(id_name, row):
    """Return all ids or an empty list if not specified"""
    external_ids = row.get("external_ids")
    if not external_ids:
        return []
    ids = external_ids.get(id_name)
    if ids:
        return ids["all"]
    return []


def external_ids_getter(id_name):
    """Return a function that can be applied to a row and return the
    external ids associated with the specified id type residing under the
    "all" branch."""
    return lambda row: external_ids_all(id_name, row)


tables = [
    TableMeta(
        "research_organizations",
        columns=[
            ColumnMeta("id", rowid=True),
            ColumnMeta("ror_path", lambda row: row["id"][16:]),
            ColumnMeta("name", lambda row: row["name"]),
            ColumnMeta("status", lambda row: row["status"]),
            ColumnMeta("established", lambda row: row["established"]),
            ColumnMeta(
                "country_code", lambda row: row["country"]["country_code"]
            ),
        ],
    ),
    TableMeta(
        "ror_types",
        extract_multiple=lambda row: row["types"],
        columns=[
            ColumnMeta("ror_id"),
            ColumnMeta("type", lambda value: value),
        ],
    ),
    TableMeta(
        "ror_links",
        extract_multiple=lambda row: row["links"],
        columns=[
            ColumnMeta("ror_id"),
            ColumnMeta("link", lambda value: value),
        ],
    ),
    TableMeta(
        "ror_aliases",
        extract_multiple=lambda row: row["aliases"],
        columns=[
            ColumnMeta("ror_id"),
            ColumnMeta("alias", lambda value: value),
        ],
    ),
    TableMeta(
        "ror_acronyms",
        extract_multiple=lambda row: row["acronyms"],
        columns=[
            ColumnMeta("ror_id"),
            ColumnMeta("acronym", lambda value: value),
        ],
    ),
    TableMeta(
        "ror_relationships",
        extract_multiple=lambda row: row["relationships"],
        columns=[
            ColumnMeta("ror_id"),
            ColumnMeta("type", lambda row: row["type"]),
            ColumnMeta("ror_path", lambda row: row["id"][16:]),
        ],
    ),
    TableMeta(
        "ror_addresses",
        extract_multiple=lambda row: row["addresses"],
        columns=[
            ColumnMeta("ror_id"),
            # ROR will simplify the current address schema.
            # Add more fields when ROR settles it.
            ColumnMeta("lat", lambda row: row["lat"]),
            ColumnMeta("lng", lambda row: row["lng"]),
            ColumnMeta("city", lambda row: row["city"]),
            ColumnMeta("state", lambda row: row["state"]),
            ColumnMeta("postcode", lambda row: row["postcode"]),
        ],
    ),
    # OrgRef and GRID are deprecated, so we are not supporting these fields
    TableMeta(
        "ror_funder_ids",
        extract_multiple=external_ids_getter("FundRef"),
        columns=[
            ColumnMeta("ror_id"),
            ColumnMeta("funder_id", lambda value: value),
        ],
    ),
    TableMeta(
        "ror_wikidata_ids",
        extract_multiple=external_ids_getter("Wikidata"),
        columns=[
            ColumnMeta("ror_id"),
            ColumnMeta("wikidata_id", lambda value: value),
        ],
    ),
    TableMeta(
        "ror_isnis",
        extract_multiple=external_ids_getter("ISNI"),
        columns=[
            ColumnMeta("ror_id"),
            ColumnMeta("isni", lambda value: value),
        ],
    ),
]

table_dict = {t.get_name(): t for t in tables}


def populate(data_path, database_path):
    """Populate the specified SQLite database.
    The database is created if it does not exist.
    If it exists, the populated tables are dropped
    (if they exist) and recreated anew as specified.
    """

    def add_org_records(data):
        for ror in data:
            ror_id = None
            for filler in table_fillers:
                if filler.get_table_name() == "research_organizations":
                    ror_id = filler.add_records(ror, "ror_id", ror_id)
                else:
                    filler.add_records(ror, "ror_id", ror_id)

    def create_tables():
        """Create empty tables and their TableFiller objects"""
        database = apsw.Connection(database_path)
        set_fast_writing(database)
        cursor = database.cursor()
        fillers = []
        for table_name, table in table_dict.items():
            columns = table.get_columns()
            column_names = [c.get_name() for c in columns]
            cursor.execute(log_sql(f"DROP TABLE IF EXISTS {table_name}"))
            cursor.execute(log_sql(table.table_schema()))
            # Value addition
            is_master = table_name == "research_organizations"
            filler = TableFiller(database, table, column_names, is_master)
            fillers.append(filler)
        return fillers

    table_fillers = create_tables()
    # Read, parse, and populate tables from the compressed file
    with zipfile.ZipFile(data_path, "r") as zip_ref:
        (file_name,) = zip_ref.namelist()
        with zip_ref.open(file_name, "r") as ror_file:
            data = json.load(ror_file)
            perf.log("Parse ROR")
            add_org_records(data)
            perf.log("Add ROR")
