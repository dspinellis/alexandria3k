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
"""Link author affiliation with lowest-level research organization"""

import ahocorasick

# pylint: disable-next=import-error
import apsw

from alexandria3k.common import (
    ensure_table_exists,
    get_string_resource,
    log_sql,
    set_fast_writing,
)
from alexandria3k import debug
from alexandria3k import perf
from alexandria3k.db_schema import ColumnMeta, TableMeta

tables = [
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
    database.execute(log_sql(tables[0].table_schema()))
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


def process(database_path):
    """
    Process the specified database creating a table that links Crossref work
    authors to their corresponding research organization as codified in the
    Research Orgnization Registry (ROR).
    The link is made to the lowest identifiable organizational level,
    e.g. an author's clinic, school, or institute.

    :param database_path: The path specifying the SQLite database
        to process and populate.
        The database shall already contain the ROR dataset and the Crossref
        `author_affiliations` table.
    :type database_path: str
    """

    link_author_affiliations(database_path, link_to_top=False)
