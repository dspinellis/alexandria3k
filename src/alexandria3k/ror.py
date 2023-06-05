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
"""Virtual table access of ROR (Research Organization Registry) data"""

import json
import zipfile

import ahocorasick

# pylint: disable-next=import-error
import apsw

from alexandria3k.common import (
    ensure_table_exists,
    get_string_resource,
    log_sql,
    set_fast_writing,
)
from alexandria3k.data_source import (
    DataSource,
    ElementsCursor,
    SINGLE_PARTITION_INDEX,
)
from alexandria3k import debug
from alexandria3k import perf
from alexandria3k.virtual_db import ColumnMeta, TableMeta, StreamingTable

# pylint: disable=R0801


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


class RorCursor:
    """A virtual table cursor over the read ROR main data."""

    def __init__(self, table):
        """Not part of the apsw VTCursor interface.
        The table agument is a StreamingTable object"""
        self.table = table
        # Initialized in Filter()
        self.eof = False
        self.item_index = -1
        # Set in Next
        self.row_value = None
        # Set in Filter
        self.iterator = None

    def Eof(self):
        """Return True when the end of the table's records has been reached."""
        return self.eof

    def Rowid(self):
        """Return a unique id of the row along all records"""
        return self.item_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == -1:
            return self.Rowid()

        if col == 0:  # id
            return self.Rowid()

        extract_function = self.table.get_value_extractor_by_ordinal(col)
        return extract_function(self.row_value)

    def Filter(self, _index_number, _index_name, _constraint_args):
        """Always called first to initialize an iteration to the first row
        of the table according to the index"""
        # print("FILTER", index_number, constraint_args)
        self.eof = False
        self.item_index = -1
        self.iterator = iter(self.table.get_data_source())
        self.Next()  # Move to first row

    def Next(self):
        """Advance to the next item."""
        self.row_value = next(self.iterator, None)
        if not self.row_value:
            self.eof = True
        else:
            self.item_index += 1

    def current_row_value(self):
        """Return the current row. Not part of the apsw API."""
        return self.row_value

    def Close(self):
        """Cursor's destructor, used for cleanup"""


class RorDetailsCursor(ElementsCursor):
    """A cursor over any of the research organization details data."""

    def __init__(self, table, parent_cursor):
        """Not part of the apsw VTCursor interface.
        The table agument is a StreamingTable object"""
        super().__init__(table, parent_cursor)
        self.extract_multiple = table.get_table_meta().get_extract_multiple()

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 16k elements."""
        return (self.parent_cursor.Rowid() << 14) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # id
            return self.record_id()

        if col == 1:  # person_id
            return self.parent_cursor.Rowid()

        return super().Column(col)

    def Next(self):
        """Advance reading to the next available element."""
        while True:
            if self.parent_cursor.Eof():
                self.eof = True
                return
            if not self.elements:
                self.elements = self.extract_multiple(
                    self.parent_cursor.current_row_value()
                )
                self.element_index = -1
            if not self.elements:
                self.parent_cursor.Next()
                self.elements = None
                continue
            if self.element_index + 1 < len(self.elements):
                self.element_index += 1
                self.eof = False
                return
            self.parent_cursor.Next()
            self.elements = None


class RorDetailsTableMeta(TableMeta):
    """Table metadata for ROR details.  Objects of this
    class are injected with properties and columns common to all
    ROR details tables."""

    def __init__(self, name, **kwargs):
        kwargs["foreign_key"] = "ror_id"
        kwargs["parent_name"] = "research_organizations"
        kwargs["primary_key"] = "id"
        kwargs["cursor_class"] = RorDetailsCursor
        kwargs["columns"] = [
            ColumnMeta("id"),
            ColumnMeta("ror_id"),
        ] + kwargs["columns"]
        super().__init__(name, **kwargs)


tables = [
    TableMeta(
        "research_organizations",
        cursor_class=RorCursor,
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
    RorDetailsTableMeta(
        "ror_types",
        extract_multiple=lambda row: row["types"],
        columns=[
            ColumnMeta("type", lambda value: value),
        ],
    ),
    RorDetailsTableMeta(
        "ror_links",
        extract_multiple=lambda row: row["links"],
        columns=[
            ColumnMeta("link", lambda value: value),
        ],
    ),
    RorDetailsTableMeta(
        "ror_aliases",
        extract_multiple=lambda row: row["aliases"],
        columns=[
            ColumnMeta("alias", lambda value: value),
        ],
    ),
    RorDetailsTableMeta(
        "ror_acronyms",
        extract_multiple=lambda row: row["acronyms"],
        columns=[
            ColumnMeta("acronym", lambda value: value),
        ],
    ),
    RorDetailsTableMeta(
        "ror_relationships",
        extract_multiple=lambda row: row["relationships"],
        columns=[
            ColumnMeta("type", lambda row: row["type"]),
            ColumnMeta("ror_path", lambda row: row["id"][16:]),
        ],
    ),
    RorDetailsTableMeta(
        "ror_addresses",
        extract_multiple=lambda row: row["addresses"],
        columns=[
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
    RorDetailsTableMeta(
        "ror_funder_ids",
        extract_multiple=external_ids_getter("FundRef"),
        columns=[
            ColumnMeta("funder_id", lambda value: value),
        ],
    ),
    RorDetailsTableMeta(
        "ror_wikidata_ids",
        extract_multiple=external_ids_getter("Wikidata"),
        columns=[
            ColumnMeta("wikidata_id", lambda value: value),
        ],
    ),
    RorDetailsTableMeta(
        "ror_isnis",
        extract_multiple=external_ids_getter("ISNI"),
        columns=[
            ColumnMeta("isni", lambda value: value),
        ],
    ),
]

link_tables = [
    # No extractors; filled by link_author_affiliations
    TableMeta(
        "work_authors_rors",
        columns=[
            ColumnMeta("ror_id"),
            ColumnMeta("work_author_id"),
        ],
    ),
]


def add_words(automaton, source):
    """Add the words from the specified source to the AC automaton"""
    for ror_id, word in source:
        automaton.add_word(word, (ror_id, len(word), word))


def keep_unique_entries(automaton):
    """Adjust the passed automaton so that is will not contain any entries
    that can match other entries.
    For example, if the input is ["Ministry of Foreign Affairs", "ai"],
    remove the "ai" entry.
    """
    to_remove = []
    for name in automaton:
        for _, (_, _, match) in automaton.iter(name):
            if match != name:
                to_remove.append(match)

    # Remove entries in a separate step to avoid damaging the iterator
    for non_unique in to_remove:
        automaton.remove_word(non_unique)


def unique_entries(table, id_field, name_field, condition=""):
    """Return an SQL statement that will provide the specified
    name and id of entries whose name exists only once in the
    table"""
    return log_sql(
        f"""
        WITH same_count AS (
          SELECT {id_field} AS id, {name_field} AS name,
            Count() OVER (PARTITION BY {name_field}) AS number
          FROM {table}
          {condition}
        )
        SELECT id, name from same_count WHERE number == 1;
    """
    )


def link_author_affiliations(database_path, link_to_top):
    """
    Create a `work_authors_rors` table that links each work author to the
    identified research organization record (ROR).

    :param database_path: The path specifying the SQLite database
        in which to add the table.  The database must be already
        contain the `research_organizations` and `author_affiliations`
        tables.
    :type database_path: str

    :param link_to_top: If `True` then the authors are linked to the
        top-level of the hierarchy associated with their affiliation
        (e.g. the university to which the university hospital they are
        affiliated with belongs).
    :type link_to_top: bool
    """
    database = apsw.Connection(database_path)
    database.execute(log_sql("DROP TABLE IF EXISTS work_authors_rors"))
    database.execute(log_sql(link_tables[0].table_schema()))
    set_fast_writing(database)
    ensure_table_exists(database, "research_organizations")
    ensure_table_exists(database, "author_affiliations")
    ensure_table_exists(database, "work_authors_rors")

    # Create an automaton with all ROR identifying names
    select_cursor = database.cursor()
    automaton = ahocorasick.Automaton()
    add_words(
        automaton,
        # Uniquely identifiable organizations
        # (E.g. avoid the 53 "Ministry of Health" ones)
        select_cursor.execute(
            unique_entries(
                "research_organizations",
                "id",
                "name",
                "WHERE status != 'withdrawn'",
            )
        ),
    )
    perf.log("Automaton add names")
    add_words(
        automaton,
        select_cursor.execute(
            unique_entries("ror_aliases", "ror_id", "alias")
        ),
    )
    perf.log("Automaton add aliases")
    add_words(
        automaton,
        select_cursor.execute(
            unique_entries("ror_acronyms", "ror_id", "acronym")
        ),
    )
    perf.log("Automaton add acronyms")

    automaton.make_automaton()
    size = automaton.get_stats()["total_size"]
    perf.log(f"Automaton build len={len(automaton)} size={size}")
    keep_unique_entries(automaton)
    perf.log("Automaton keep unique entries")
    automaton.make_automaton()
    perf.log(f"Automaton rebuild len={len(automaton)}")

    insert_cursor = database.cursor()
    affiliations_number = 0
    for author_id, affiliation_name in select_cursor.execute(
        "SELECT author_id, name FROM author_affiliations"
    ):
        if not affiliation_name:
            continue
        affiliations_number += 1
        best_ror_id = None
        best_length = 0
        # Find all ROR names in affiliation_name
        for _, (ror_id, length, _) in automaton.iter(affiliation_name):
            if length > best_length:
                best_length = length
                best_ror_id = ror_id
        if best_ror_id:
            debug.log(
                "link", f"Identified {affiliation_name} as {best_ror_id}"
            )
            insert_cursor.execute(
                "INSERT INTO work_authors_rors VALUES(?, ?)",
                (best_ror_id, author_id),
                prepare_flags=apsw.SQLITE_PREPARE_PERSISTENT,
            )
    select_cursor.close()
    insert_cursor.close()
    perf.log(f"Link {affiliations_number} affiliations")
    if not link_to_top:
        return

    # Link each work author to the identified topmost parent Research
    # Organization Record
    statement = get_string_resource("sql/work-authors-top-rors.sql")
    database.execute(log_sql(statement))
    perf.log("Link top-level affiliations")


class VTSource:
    """Virtual table data source for a single moderately-sized JSON file.
    This gets registered with the apsw Connection through createmodule
    in order to instantiate the virtual table."""

    def __init__(self, data_source, sample):
        with zipfile.ZipFile(data_source, "r") as zip_ref:
            (self.file_name,) = zip_ref.namelist()
            with zip_ref.open(self.file_name, "r") as ror_file:
                self.data_source = json.load(ror_file)
                perf.log("Parse ROR")
        self.sample = sample
        self.table_dict = {t.get_name(): t for t in tables}

    def get_container_iterator(self):
        """Return an iterator over the int identifiers of all data files"""
        return [SINGLE_PARTITION_INDEX]

    def get_container_name(self, _fid):
        """Return the name of the file corresponding to the specified fid"""
        return self.file_name

    def Create(self, _db, _module_name, _db_name, table_name):
        """Create the specified virtual table by creating its schema
        and an apsw table (a StramingTable instance) streaming over its data"""
        table = self.table_dict[table_name]
        return table.table_schema(), StreamingTable(
            table, self.table_dict, self.data_source
        )

    Connect = Create


class Ror(DataSource):
    """
    Create an ROR meta-data object that supports queries over its
    (virtual) tables and the population of an SQLite database with its
    data.

    :param ror_file: Path to a zip file containing the research organization
        data, e.g. `"v1.17.1-2022-12-16-ror-data.zip"`
    :type ror_file: str

    :param sample: A callable to control container sampling, defaults
        to `lambda n: True`.
        The population or query method will call this argument
        for each Crossref container file with each container's file
        name as its argument.  When the callable returns `True` the
        container file will get processed, when it returns `False` the
        container will get skipped.
    :type sample: callable, optional

    :param attach_databases: A list of colon-joined tuples specifying
        a database name and its path, defaults to `None`.
        The specified databases are attached and made available to the
        query and the population condition through the specified database
        name.
    :type attach_databases: list, optional

    """

    def __init__(
        self,
        ror_file,
        sample=lambda n: True,
        attach_databases=None,
    ):
        super().__init__(
            VTSource(ror_file, sample),
            tables,
            attach_databases,
        )
