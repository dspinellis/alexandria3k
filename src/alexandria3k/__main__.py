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
import random
import sqlite3
import sys

from . import crossref
from . import csv_sources
from . import debug
from .file_cache import FileCache
from . import orcid
from . import ror
from . import perf

# Default values for diverse data sources
DOAJ_DEFAULT = "https://doaj.org/csv"
FUNDER_NAMES_DEFAULT = "https://doi.crossref.org/funderNames?mode=list"
JOURNAL_NAMES_DEFAULT = "http://ftp.crossref.org/titlelist/titleFile.csv"
ASJC_DEFAULT = "resource:data/asjc.csv"

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


def schema_list(parser, arg):
    """Print the specified database schema"""

    def tables_list(tables):
        """List the schema of the specified tables"""
        for table in tables:
            print(table.table_schema())

    name = arg.lower()
    if name == "all":
        tables_list(
            crossref.tables + csv_sources.tables + orcid.tables + ror.tables
        )
    elif name == "crossref":
        tables_list(crossref.tables)
    elif name == "orcid":
        tables_list(orcid.tables)
    elif name == "ror":
        # Exclude table we generate
        ror_tables = [
            x for x in ror.tables if x.get_name() != "work_authors_rors"
        ]
        tables_list(ror_tables)
    elif name == "other":
        # Include table we generate
        work_authors_rors = [
            x for x in ror.tables if x.get_name() == "work_authors_rors"
        ]
        tables_list(csv_sources.tables + work_authors_rors)
    else:
        parser.error(f"Unknown source name {arg}")


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


def parse_cli_arguments(parser, args=None):
    """Parse command line arguments (or args e.g. when testing)"""

    parser.add_argument(
        "-a",
        "--attach-databases",
        nargs="+",
        type=str,
        help="Databases to attach for the row selection query",
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
    link: Record linking operations;
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
        "-d",
        "--data-source",
        nargs="+",
        type=str,
        help=f"""Specify data set to be processed and its source.
    The following data sets are supported:
    ASJC [<CSV-file> | <URL>] (defaults to internal table);
    Crossref <container-directory>;
    DOAJ [<CSV-file> | <URL>] (defaults to {DOAJ_DEFAULT});
    funder-names [<CSV-file> | <URL>] (defaults to {FUNDER_NAMES_DEFAULT});
    journal-names [<CSV-file> | <URL>] (defaults to {JOURNAL_NAMES_DEFAULT});
    ORCID <summaries.tar.gz-file>
    ROR <zip-file>;
    """,
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
        "-L",
        "--list-schema",
        type=str,
        help="""List the schema of the specified database.  The following
    names are supported: Crossref, ORCID, ROR, other, all""",
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
        "-o",
        "--output",
        type=str,
        help="Output file for query results",
    )
    parser.add_argument(
        "-P",
        "--partition",
        action="store_true",
        # pylint: disable-next=line-too-long
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
        "-x",
        "--execute",
        type=str,
        help="""Operation to execute on the data. This can be one of:
link-aa-base-ror (link author affiliations to base-level research
organizations);
link-aa-top-ror (link author affiliations to top-level research organizations);
link-works-asjcs (link works with Scopus All Science Journal Classification Codes — ASJCs).
        """,
    )

    return expand_data_source(parser, parser.parse_args(args))


def expand_data_source(parser, args):
    # pylint: disable=too-many-branches
    """Return the args, expanding the data_source argument by setting an
    entry in args named after the source and containing where the data
    are to come from.
    """

    def required_value(error_message):
        """Return the second data_source element or fail with the specified
        error message."""
        if len(args.data_source) != 2:
            parser.error(error_message)
        return args.data_source[1]

    def optional_value(default):
        """Return the second data_source element or the specified default"""
        if len(args.data_source) > 2:
            parser.error("Too many arguments in data source specification")
        return args.data_source[1] if len(args.data_source) == 2 else default

    args.crossref = None
    args.asjc = None
    args.doaj = None
    args.funder_names = None
    args.journal_names = None
    args.orcid = None
    args.ror = None

    if not args.data_source:
        return args

    source_name = args.data_source[0].lower()

    if source_name == "crossref":
        if not (args.populate_db_path or args.query or args.query_file):
            parser.error("Database path or query must be specified")
    else:
        if not args.populate_db_path:
            parser.error("Database path must be specified")

    if source_name == "asjc":
        args.asjc = optional_value(ASJC_DEFAULT)
    elif source_name == "crossref":
        args.crossref = required_value("Missing Crossref data directory value")
    elif source_name == "doaj":
        args.doaj = optional_value(DOAJ_DEFAULT)
    elif source_name == "funder-names":
        args.funder_names = optional_value(FUNDER_NAMES_DEFAULT)
    elif source_name == "journal-names":
        args.journal_names = optional_value(JOURNAL_NAMES_DEFAULT)
    elif source_name == "orcid":
        args.orcid = required_value("Missing ORCID data file value")
    elif source_name == "ror":
        args.ror = required_value("Missing ROR zip file value")
    else:
        parser.error(f"Unknown source name {args.data_source[0]}")

    if args.query and not args.crossref:
        parser.error("Missing Crossref data directory value")

    return args


def main():
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    """Program entry point"""
    parser = argparse.ArgumentParser(
        description="alexandria3k: Publication metadata interface"
    )
    args = parse_cli_arguments(parser)

    # Setup debug logging and performance monitoring
    debug.set_flags(args.debug)
    if debug.enabled("stderr"):
        debug.set_output(sys.stderr)
    perf.log("Start")

    if args.list_schema:
        schema_list(parser, args.list_schema)
        sys.exit(0)

    crossref_instance = None
    if args.crossref:
        # pylint: disable-next=W0123
        sample = eval(f"lambda path: {args.sample}")
        crossref_instance = crossref.Crossref(args.crossref, sample)

    if debug.enabled("virtual-counts"):
        # Streaming interface
        database_counts(crossref_instance.get_virtual_db())
        debug.log("files-read", f"{FileCache.file_reads} files read")

    if debug.enabled("virtual-data"):
        # Streaming interface
        database_dump(crossref_instance.get_virtual_db())
        debug.log("files-read", f"{FileCache.file_reads} files read")

    if args.row_selection_file:
        args.row_selection = ""
        with open(args.row_selection_file, encoding="utf-8") as query_input:
            for line in query_input:
                args.row_selection += line

    if crossref_instance and args.populate_db_path:
        crossref_instance.populate(
            args.populate_db_path,
            args.columns,
            args.row_selection,
            args.attach_databases,
        )
        debug.log("files-read", f"{FileCache.file_reads} files read")
        perf.log("Crossref table population")

    if args.orcid:
        orcid.populate(
            args.orcid,
            args.populate_db_path,
            args.columns,
            args.linked_records == "persons",
            args.linked_records == "works",
        )
        perf.log("ORCID table population")

    if args.ror:
        ror.populate(args.ror, args.populate_db_path)
        perf.log("ROR table population")

    if args.query_file:
        args.query = ""
        with open(args.query_file, encoding="utf-8") as query_input:
            for line in query_input:
                args.query += line

    if args.query:
        if args.output:
            # pylint: disable-next=R1732
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
        csv_file.close()
        debug.log("files-read", f"{FileCache.file_reads} files read")

    if args.asjc:
        csv_sources.populate_asjc(args.populate_db_path, args.asjc)
    if args.doaj:
        csv_sources.populate_open_access_journals(
            args.populate_db_path, args.doaj
        )
    if args.funder_names:
        csv_sources.populate_funder_names(
            args.populate_db_path, args.funder_names
        )
    if args.journal_names:
        csv_sources.populate_journal_names(
            args.populate_db_path, args.journal_names
        )

    if args.execute == "link-aa-base-ror":
        ror.link_author_affiliations(args.populate_db_path, link_to_top=False)
    elif args.execute == "link-aa-top-ror":
        ror.link_author_affiliations(args.populate_db_path, link_to_top=True)
    elif args.execute == "link-works-asjcs":
        csv_sources.link_works_asjcs(args.populate_db_path)
    elif args.execute:
        parser.error(f"Unknown execution argument: {args.execute}")

    if debug.enabled("populated-counts"):
        populated_db = sqlite3.connect(args.populate_db_path)
        database_counts(populated_db)

    if debug.enabled("populated-data"):
        populated_db = sqlite3.connect(args.populate_db_path)
        database_dump(populated_db)

    if debug.enabled("populated-reports"):
        populated_db = sqlite3.connect(args.populate_db_path)
        populated_reports(populated_db)

    debug.log("files-read", f"{FileCache.file_reads} files read")


if __name__ == "__main__":
    main()
