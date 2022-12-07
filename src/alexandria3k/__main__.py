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
"""Command-line interface"""

import argparse
import csv
import os
import random
import sqlite3
import sys

import apsw

from .common import fail
from . import crossref
from . import csv_sources
from . import debug
from .file_cache import FileCache
from . import orcid
from . import perf

random.seed("alexandria3k")


def populated_reports(pdb):
    """Populated database reports"""

    print("Authors with most publications")
    for rec in pdb.execute(
        """SELECT count(*), orcid FROM work_authors
             WHERE orcid is not null GROUP BY orcid ORDER BY count(*) DESC
             LIMIT 3"""
    ):
        print(rec)

    print("Author affiliations")
    for rec in pdb.execute(
        """SELECT work_authors.given, work_authors.family,
            author_affiliations.name FROM work_authors
             INNER JOIN author_affiliations
                ON work_authors.id = author_affiliations.author_id"""
    ):
        print(rec)

    print("Organizations with most publications")
    for rec in pdb.execute(
        """SELECT count(*), name FROM affiliations_works
        LEFT JOIN affiliation_names ON affiliation_names.id = affiliation_id
        GROUP BY affiliation_id ORDER BY count(*) DESC
        LIMIT 3"""
    ):
        print(rec)

    print("Most cited references")
    for rec in pdb.execute(
        """SELECT count(*), doi FROM work_references
        GROUP BY doi ORDER BY count(*) DESC
        LIMIT 3"""
    ):
        print(rec)

    print("Most treated subjects")
    for rec in pdb.execute(
        """SELECT count(*), name
                FROM works_subjects INNER JOIN subject_names
                    ON works_subjects.subject_id = subject_names.id
            GROUP BY(works_subjects.subject_id)
            ORDER BY count(*) DESC
            LIMIT 3
        """
    ):
        print(rec)


def schema_list():
    """Print the full database schema"""

    for table in (
        crossref.tables
        + orcid.tables
        + [
            csv_sources.open_access_table,
            csv_sources.funders_table,
            csv_sources.journals_table,
        ]
    ):
        print(table.table_schema())


def database_dump(database):
    """Print the passed database data"""

    for table in crossref.tables:
        name = table.get_name()
        print(f"TABLE {name}")
        csv_writer = csv.writer(sys.stdout, delimiter="\t")
        for rec in database.execute(f"SELECT * FROM {name}"):
            csv_writer.writerow(rec)


def database_counts(database):
    """Print various counts on the passed database"""

    def sql_value(database, statement):
        """Return the first value of the specified SQL statement executed on
        the specified database"""
        (res,) = database.execute(statement).fetchone()
        return res

    for table in crossref.tables:
        count = sql_value(database, f"SELECT count(*) FROM {table.get_name()}")
        print(f"{count} element(s)\tin {table.get_name()}")

    count = sql_value(
        database,
        """SELECT count(*) from (SELECT DISTINCT orcid FROM work_authors
                        WHERE orcid is not null)""",
    )
    print(f"{count} unique author ORCID(s)")

    count = sql_value(
        database,
        "SELECT count(*) FROM (SELECT DISTINCT work_id FROM work_authors)",
    )
    print(f"{count} publication(s) with work_authors")

    count = sql_value(
        database,
        """SELECT count(*) FROM work_references WHERE
                      doi is not null""",
    )
    print(f"{count} references(s) with DOI")


def parse_cli_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="alexandria3k: Publication metadata interface"
    )

    parser.add_argument(
        "-C",
        "--crossref-directory",
        type=str,
        help="Directory storing the downloaded Crossref publication data",
    )
    parser.add_argument(
        "-c",
        "--columns",
        nargs="+",
        type=str,
        help="Columns to populate using table.column or table.*",
    )
    parser.add_argument(
        "-D",
        "--debug",
        nargs="+",
        type=str,
        default=[],
        help="""Output debuggging information as specfied by the arguments.
    files-read: Output counts of data files read;
    log-sql: Output executed SQL statements;
    perf: Output performance timings;
    populated-counts: Dump counts of the populated database;
    populated-data: Dump the data of the populated database;
    populated-reports: Output query results from the populated database;
    progress: Report progress;
    stderr: Log to standard error;
    virtual-counts: Dump counts of the virtual database;
    virtual-data: Dump the data of the virtual database.
""",
    )
    parser.add_argument(
        "-A",
        "--open-access-journals",
        nargs="?",
        const="https://s3.eu-west-2.amazonaws.com/doaj-data-cache/journalcsv__doaj_20221121_0635_utf8.csv",
        type=str,
        help="Populate database with DOAJ open access journal metadata from URL or file",
    )
    parser.add_argument(
        "-E",
        "--output-encoding",
        type=str,
        default="utf-8",
        help="Query output character encoding (use utf-8-sig for Excel)",
    )
    parser.add_argument(
        "-F",
        "--field-separator",
        type=str,
        default=",",
        help="Character to use for separating query output fields",
    )
    parser.add_argument(
        "-H",
        "--header",
        action="store_true",
        help="Include a header in the query output",
    )
    parser.add_argument(
        "-i",
        "--index",
        nargs="*",
        type=str,
        help="SQL expressions that select the populated rows",
    )
    parser.add_argument(
        "-J",
        "--journal-names",
        nargs="?",
        const="http://ftp.crossref.org/titlelist/titleFile.csv",
        type=str,
        help="Populate database with Crossref journal names from URL or file",
    )
    parser.add_argument(
        "-L",
        "--list-schema",
        action="store_true",
        help="List the schema of the scanned database",
    )
    parser.add_argument(
        "-l",
        "--linked-records",
        type=str,
        help="Only add ORCID records that link to existing <persons> or <works>",
    )
    parser.add_argument(
        "-n",
        "--normalize",
        action="store_true",
        help="Normalize relations in the populated Crossref database",
    )
    parser.add_argument(
        "-O",
        "--orcid-data",
        type=str,
        help="URL or file for obtaining ORCID author data",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file for query results",
    )
    parser.add_argument(
        "-P",
        "--partition",
        action="store_true",
        help="Run the query over partitioned data slices. (Warning: arguments are run per partition.)",
    )
    parser.add_argument(
        "-p",
        "--populate-db-path",
        type=str,
        help="Populate the SQLite database in the specified path",
    )
    parser.add_argument(
        "-Q",
        "--query-file",
        type=str,
        help="File containing query to run on the virtual tables",
    )
    parser.add_argument(
        "-q", "--query", type=str, help="Query to run on the virtual tables"
    )
    parser.add_argument(
        "-R",
        "--row-selection-file",
        type=str,
        help="File containing SQL expression that selects the populated rows",
    )
    parser.add_argument(
        "-r",
        "--row-selection",
        type=str,
        help="SQL expression that selects the populated rows",
    )
    parser.add_argument(
        "-s",
        "--sample",
        # By default the function always returns True
        default="True",
        type=str,
        help="Python expression to sample the Crossref tables (e.g. random.random() < 0.0002)",
    )
    parser.add_argument(
        "-U",
        "--funder-names",
        nargs="?",
        const="https://doi.crossref.org/funderNames?mode=list",
        type=str,
        help="Populate database with Crossref funder names from URL or file",
    )
    return parser.parse_args()


def main():
    """Program entry point"""
    args = parse_cli_arguments()

    # Setup debug logging and performance monitoring
    debug.set_flags(args.debug)
    if debug.enabled("stderr"):
        debug.set_output(sys.stderr)
    perf.print("Start")

    if args.list_schema:
        schema_list()
        sys.exit(0)

    crossref_instance = None
    if args.crossref_directory:
        # pylint: disable=W0123
        sample = eval(f"lambda path: {args.sample}")
        crossref_instance = crossref.Crossref(args.crossref_directory, sample)

    if debug.enabled("virtual-counts"):
        # Streaming interface
        database_counts(crossref_instance.get_virtual_db())
        debug.print("files-read", f"{FileCache.file_reads} files read")

    if debug.enabled("virtual-data"):
        # Streaming interface
        database_dump(crossref_instance.get_virtual_db())
        debug.print("files-read", f"{FileCache.file_reads} files read")

    if args.row_selection_file:
        args.row_selection = ""
        with open(args.row_selection_file) as query_input:
            for line in query_input:
                args.row_selection += line

    if crossref_instance and args.populate_db_path:
        crossref_instance.populate(
            args.populate_db_path, args.columns, args.row_selection
        )
        debug.print("files-read", f"{FileCache.file_reads} files read")
        perf.print("Crossref table population")

    if args.orcid_data:
        if not args.populate_db_path:
            fail("Database path must be specified")
        orcid.populate(
            args.orcid_data,
            args.populate_db_path,
            args.columns,
            args.linked_records == "persons",
            args.linked_records == "works",
        )
        perf.print("ORCID table population")

    if args.query_file:
        args.query = ""
        with open(args.query_file) as query_input:
            for line in query_input:
                args.query += line

    if args.query:
        if not crossref_instance:
            fail("Crossref data directory must be specified")

        if args.output:
            # pylint: disable=R1732
            csv_file = open(
                args.output, "w", newline="", encoding=args.output_encoding
            )
        else:
            sys.stdout.reconfigure(encoding=args.output_encoding)
            csv_file = sys.stdout
        csv_writer = csv.writer(csv_file, delimiter=args.field_separator)
        for rec in crossref_instance.query(args.query, args.partition):
            if args.header:
                csv_writer.writerow(crossref_instance.get_query_column_names())
                args.header = False
            csv_writer.writerow(rec)
        debug.print("files-read", f"{FileCache.file_reads} files read")

    if args.normalize:
        if not args.populate_db_path:
            fail("Database path must be specified")
        populated_db = sqlite3.connect(args.populate_db_path)
        crossref.normalize_affiliations(populated_db)
        crossref.normalize_subjects(populated_db)
        perf.print("Data normalization")

    if args.journal_names:
        if not args.populate_db_path:
            fail("Database path must be specified")
        csv_sources.populate_journal_names(
            args.populate_db_path, args.journal_names
        )

    if args.funder_names:
        if not args.populate_db_path:
            fail("Database path must be specified")
        csv_sources.populate_funder_names(
            args.populate_db_path, args.funder_names
        )

    if args.open_access_journals:
        if not args.populate_db_path:
            fail("Database path must be specified")
        csv_sources.populate_open_access_journals(
            args.populate_db_path, args.open_access_journals
        )

    if debug.enabled("populated-counts"):
        populated_db = sqlite3.connect(args.populate_db_path)
        database_counts(populated_db)

    if debug.enabled("populated-data"):
        populated_db = sqlite3.connect(args.populate_db_path)
        database_dump(populated_db)

    if debug.enabled("populated-reports"):
        populated_db = sqlite3.connect(args.populate_db_path)
        populated_reports(populated_db)

    debug.print("files-read", f"{FileCache.file_reads} files read")


if __name__ == "__main__":
    main()
