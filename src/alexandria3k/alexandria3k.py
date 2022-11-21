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
"""Main package module"""

import argparse
import csv
import os
import random
import sqlite3
import sys

import apsw

import crossref
import csv_sources
from file_cache import FileCache
import orcid
from perf import Perf
from tsort import tsort

random.seed("alexandria3k")


def fail(message):
    """Fail the program execution with the specified error message"""
    print(message, file=sys.stderr)
    sys.exit(1)


class CrossrefMetaData:
    """Create a Crossref meta-data object that support queries over its
    (virtual) table and the population of an SQLite database with its
    data"""

    def __init__(self, args):
        self.args = args
        # A named in-memory database; it can be attached by name to others
        self.vdb = apsw.Connection(
            "file:virtual?mode=memory&cache=shared",
            apsw.SQLITE_OPEN_URI | apsw.SQLITE_OPEN_READWRITE,
        )
        self.cursor = self.vdb.cursor()
        # Register the module as filesource
        self.data_source = crossref.Source(
            crossref.table_dict, args.crossref_directory, args.sample
        )
        self.vdb.createmodule("filesource", self.data_source)

        # Dictionaries of tables containing a set of columns required
        # for querying or populating the database
        self.query_columns = {}
        self.population_columns = {}

        for table in crossref.tables:
            self.vdb.execute(
                self.log_sql(
                    f"CREATE VIRTUAL TABLE {table.get_name()} USING filesource()"
                )
            )

    def log_sql(self, statement):
        """Return the specified SQL statement. If "log-sql" is set,
        output a copy of the statement on the standard output"""
        if "log-sql" in self.args.debug:
            print(statement)
        return statement

    def get_virtual_db(self):
        """Return the virtual table database as an apsw object"""
        return self.vdb

    @staticmethod
    def add_column(dictionary, table, column):
        """Add a column required for executing a query to the
        specified dictionary"""
        if table in dictionary:
            dictionary[table].add(column)
        else:
            dictionary[table] = {column}

    def set_query_columns(self, query):
        """Set the columns a query requires to run as a set in
        self.query_columns by invoking the tracer"""

        def trace_query_columns(query):
            """Set the columns a query requires to run as a set in
            self.query_columns.
            See https://rogerbinns.github.io/apsw/tips.html#parsing-sql"""

            def authorizer(op_code, table, column, _database, _trigger):
                """Query authorizer to monitor used columns"""
                if op_code == apsw.SQLITE_READ and column:
                    # print(f"AUTH: adding {table}.{column}")
                    CrossrefMetaData.add_column(
                        self.query_columns, table, column
                    )
                return apsw.SQLITE_OK

            def tracer(_cursor, _query, _bindings):
                """An execution tracer that denies the query's operation"""
                # Abort the query's evaluation with an exception.  Returning
                # apsw.SQLITE_DENY seems to be doing something that takes
                # minutes to finish
                return None

            # Add the columns required by the actual query
            self.cursor.setexectrace(tracer)
            self.vdb.setauthorizer(authorizer)
            self.cursor.execute(self.log_sql(query), can_cache=False)
            # NOTREACHED

        try:
            trace_query_columns(query)
        except apsw.ExecTraceAbort:
            pass
        self.vdb.setauthorizer(None)
        self.cursor.setexectrace(None)

    def query(self, query, partition=False):
        """Run the specified query on the virtual database.
        Returns an iterable over the query's results.
        Queries involving table joins will run substantially faster
        if access to each table's records is restricted with
        an expression `table_name.container_id = CONTAINER_ID`, and
        the `partition` argument is set to true.
        In such a case the query is repeatedly run over each database
        partition (compressed JSON file) with `CONTAINER_ID` iterating
        sequentially to cover all partitions.
        The query's result is the concatenation of the individal partition
        results.
        Running queries with joins without partitioning will often result
        in quadratic (or worse) algorithmic complexity."""

        # Easy case
        if not partition:
            for row in self.vdb.execute(self.log_sql(query)):
                yield row
            return

        # Even when restricting multiple JOINs with container_id
        # SQLite seems to scan all containers for each JOIN making the
        # performance intolerably slow. Address this by creating non-virtual
        # tables with the required columns for each partition, as follows.
        #
        # Identify required tables and columns
        # Create an in-memory database
        # Attach database partition to in-memory database
        # For each partition:
        #   Copy tables to in-memory database
        #   Run query on in-memory database
        #   drop tables
        self.set_query_columns(query)
        partition = apsw.Connection(
            "file:partition?mode=memory&cache=shared",
            apsw.SQLITE_OPEN_URI | apsw.SQLITE_OPEN_READWRITE,
        )
        partition.createmodule("filesource", self.data_source)
        partition.execute(
            self.log_sql(
                "ATTACH DATABASE 'file:virtual?mode=memory&cache=shared' AS virtual"
            )
        )
        for i in self.data_source.get_file_id_iterator():
            if "progress" in self.args.debug:
                print(
                    f"Container {i} {self.data_source.get_file_name_by_id(i)}",
                    flush=True,
                )
            for table_name in self.query_columns.keys():
                columns = ", ".join(self.query_columns[table_name])
                partition.execute(
                    self.log_sql(
                        f"""CREATE TABLE {table_name}
                  AS SELECT {columns} FROM virtual.{table_name}
                    WHERE virtual.{table_name}.container_id={i}"""
                    )
                )
            for row in partition.execute(self.log_sql(query)):
                yield row
            for table_name in self.query_columns.keys():
                partition.execute(self.log_sql(f"DROP TABLE {table_name}"))

    def populate_database(self, database_path, columns, condition, _indexes):
        """Populate the specified SQLite database.
        The database is created if it does not exist.
        If it exists, the populated tables are dropped
        (if they exist) and recreated anew as specified.

        columns is an array containing strings of
        table_name.column_name or table_name.*

        conditions is a dictionary of table_name to condition

        The condition is an
        [SQL expression](https://www.sqlite.org/syntax/expr.html)
        containing references to the table's columns.
        It can also contain references to populated tables, by prefixing
        the column name with `populated.`.
        Implicitly, if a main table is populated, its detail tables
        will only get populated with the records associated with the
        correspoing main table.

        indexes is an array of table_name(indexed_column...)  strings,
        that specifies indexes to be created before populating the tables.
        The indexes can be used to speed up the evaluation of the population
        conditions.
        Note that foreign key indexes will always be created and need
        not be specified.
        """

        def set_join_columns():
            """Add columns required for joins"""
            to_add = []
            for table_name in population_and_query_tables():
                while table_name:
                    table = crossref.get_table_meta_by_name(table_name)
                    parent_table_name = table.get_parent_name()
                    primary_key = table.get_primary_key()
                    foreign_key = table.get_foreign_key()
                    if foreign_key:
                        to_add.append((table_name, foreign_key))
                    if parent_table_name and primary_key:
                        to_add.append((parent_table_name, primary_key))
                    table_name = parent_table_name
            # print("ADD COLUMNS ", to_add)
            for (table, column) in to_add:
                CrossrefMetaData.add_column(self.query_columns, table, column)

        def population_and_query_tables():
            """Return a sequence consisting of the tables required
            for populating and querying the data"""
            return set.union(
                set(self.population_columns.keys()),
                set(self.query_columns.keys()),
            )

        def joined_tables():
            """Return JOIN statements for all tables to be populated."""
            result = ""
            sorted_tables = tsort(population_and_query_tables())
            # print("SORTED", sorted_tables)
            for table_name in sorted_tables:
                if table_name == "works":
                    continue
                table = crossref.get_table_meta_by_name(table_name)
                parent_table_name = table.get_parent_name()
                primary_key = table.get_primary_key()
                foreign_key = table.get_foreign_key()
                result += f""" LEFT JOIN temp_{table_name} AS {table_name} ON
                    {parent_table_name}.{primary_key}
                      = {table_name}.{foreign_key}"""
            return result

        def populate_table(table, partition_index, condition):
            """Populate the specified table"""

            columns = ", ".join(
                [f"{table}.{col}" for col in self.population_columns[table]]
            )

            if condition:
                self.vdb.execute(
                    self.log_sql("DROP INDEX IF EXISTS temp_matched_idx")
                )
                self.vdb.execute(
                    self.log_sql(
                        f"""CREATE INDEX temp_matched_idx
                          ON temp_matched({table}_rowid)"""
                    )
                )
                exists = f"""AND EXISTS (SELECT 1 FROM temp_matched
                  WHERE {table}.rowid = temp_matched.{table}_rowid)"""
            else:
                exists = ""

            statement = f"""
                INSERT INTO populated.{table}
                    SELECT {columns} FROM {table}
                    WHERE {table}.container_id = {partition_index} {exists}
                """
            self.vdb.execute(self.log_sql(statement))

        # Create the populated database, if needed
        if not os.path.exists(database_path):
            pdb = sqlite3.connect(database_path)
            pdb.close()

        self.vdb.execute(
            self.log_sql(f"ATTACH DATABASE '{database_path}' AS populated")
        )

        # By default include all tables and columns
        if not columns:
            columns = []
            for table in crossref.tables:
                # table_name.* will get expanded by the SQL SELECT statement
                columns.append(f"{table.get_name()}.*")

        # A dictionary of columns to be populated for each table
        for col in columns:
            (table, column) = col.split(".")
            if not table or not column:
                fail(f"Invalid column specification: {col}")
            CrossrefMetaData.add_column(self.population_columns, table, column)

        # Setup the columns required for executing the query
        if condition:
            tables = ", ".join(crossref.table_dict.keys())
            query = f"""SELECT DISTINCT 1 FROM {tables} WHERE {condition}"""
            self.set_query_columns(query)
            set_join_columns()
            self.args.perf.print("Condition parsing")

        # Create empty tables
        for (table_name, table_columns) in self.population_columns.items():
            table = crossref.get_table_meta_by_name(table_name)
            self.vdb.execute(
                self.log_sql(f"DROP TABLE IF EXISTS populated.{table_name}")
            )
            self.vdb.execute(
                self.log_sql(table.table_schema("populated.", table_columns))
            )
        self.args.perf.print("Table creation")

        # Populate all tables from the records of each file in sequence.
        # This improves the locality of reference and through the constraint
        # indexing and the file cache avoids opening, reading, decompressing,
        # and parsing each file multiple times.
        for i in self.data_source.get_file_id_iterator():
            if "progress" in self.args.debug:
                print(
                    f"Container {i} {self.data_source.get_file_name_by_id(i)}",
                    flush=True,
                )
            # Sampling:
            #           WHERE abs(random() % 100000) = 0"""
            #           WHERE update_count is not null

            if condition:
                # Create copies of the virtual tables for fast access
                for table in population_and_query_tables():
                    columns = self.query_columns.get(table)
                    if columns:
                        columns = set.union(columns, {"rowid"})
                    else:
                        columns = {"rowid"}
                    column_list = ", ".join(columns)
                    self.vdb.execute(
                        self.log_sql(f"""DROP TABLE IF EXISTS temp_{table}""")
                    )
                    create = f"""CREATE TEMP TABLE temp_{table} AS
                        SELECT {column_list} FROM {table}
                        WHERE container_id = {i}"""
                    self.vdb.execute(self.log_sql(create))
                self.args.perf.print("Virtual table copies")

                # Create the statement for the combined records
                create = (
                    "CREATE TEMP TABLE temp_matched AS SELECT "
                    + ", ".join(
                        [
                            f"{table}.rowid AS {table}_rowid"
                            for table in population_and_query_tables()
                        ]
                    )
                    + " FROM temp_works AS works "
                    + joined_tables()
                    + f" WHERE ({condition})"
                )
                self.vdb.execute(
                    self.log_sql("DROP TABLE IF EXISTS temp_matched")
                )
                self.vdb.execute(self.log_sql(create))
                self.args.perf.print("Combined table creation")

            for table in self.population_columns:
                populate_table(table, i, condition)
        self.args.perf.print("Table population")

        self.vdb.execute(self.log_sql("DETACH populated"))

    @staticmethod
    def normalize_affiliations(pdb):
        """Create affiliation_names id-name table and authors_affiliations,
        affiliations_works many-to-many tables"""

        pdb.execute("DROP TABLE IF EXISTS affiliation_names")
        pdb.execute(
            """CREATE TABLE affiliation_names AS
          SELECT row_number() OVER (ORDER BY '') AS id, name
          FROM (SELECT DISTINCT name FROM author_affiliations)"""
        )

        pdb.execute("DROP TABLE IF EXISTS authors_affiliations")
        pdb.execute(
            """CREATE TABLE authors_affiliations AS
          SELECT affiliation_names.id AS affiliation_id,
            author_affiliations.author_id
            FROM affiliation_names INNER JOIN author_affiliations
              ON affiliation_names.name = author_affiliations.name"""
        )

        pdb.execute("DROP TABLE IF EXISTS affiliations_works")
        pdb.execute(
            """CREATE TABLE affiliations_works AS
          SELECT DISTINCT affiliation_id, work_authors.work_doi
            FROM authors_affiliations
            LEFT JOIN work_authors
              ON authors_affiliations.author_id = work_authors.id"""
        )

    @staticmethod
    def normalize_subjects(pdb):
        """Create subject_names id-name table and works_subjects many-to-many
        table"""

        pdb.execute("DROP TABLE IF EXISTS subject_names")
        pdb.execute(
            """CREATE TABLE subject_names AS
                SELECT row_number() OVER (ORDER BY '') AS id, name
                    FROM (SELECT DISTINCT name FROM work_subjects)
            """
        )

        pdb.execute("DROP TABLE IF EXISTS works_subjects")
        pdb.execute(
            """CREATE TABLE works_subjects AS
                SELECT subject_names.id AS subject_id, work_doi
                  FROM subject_names
                  INNER JOIN work_subjects ON subject_names.name
                    = work_subjects.name
            """
        )


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
        "SELECT count(*) FROM (SELECT DISTINCT work_doi FROM work_authors)",
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
        action="store_true",
        help="Only add ORCID records that link to existing ones",
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

    if args.list_schema:
        schema_list()
        sys.exit(0)

    # pylint: disable=W0123
    args.sample = eval(f"lambda path: {args.sample}")

    crossref = CrossrefMetaData(args) if args.crossref_directory else None

    # Setup performance monitoring
    if "perf" in args.debug:
        args.perf = Perf(True)
        args.perf.print("Start")
    else:
        args.perf = Perf(False)

    if "virtual-counts" in args.debug:
        # Streaming interface
        database_counts(crossref.get_virtual_db())
        if "files-read" in args.debug:
            print(f"{FileCache.file_reads} files read")

    if "virtual-data" in args.debug:
        # Streaming interface
        database_dump(crossref.get_virtual_db())
        if "files-read" in args.debug:
            print(f"{FileCache.file_reads} files read")

    if crossref and args.populate_db_path:
        if args.index:
            indexes = [x.split(":", 1) for x in args.index]
        else:
            indexes = []

        crossref.populate_database(
            args.populate_db_path, args.columns, args.row_selection, indexes
        )
        if "files-read" in args.debug:
            print(f"{FileCache.file_reads} files read")
        args.perf.print("Crossref table population")

    if args.orcid_data:
        if not args.populate_db_path:
            fail("Database path must be specified")
        orcid.populate(
            args.orcid_data,
            args.populate_db_path,
            args.columns,
            args.linked_records,
        )
        args.perf.print("ORCID table population")

    if args.query_file:
        args.query = ""
        with open(args.query_file) as query_input:
            for line in query_input:
                args.query += line

    if args.query:
        if not crossref:
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
        for rec in crossref.query(args.query, args.partition):
            csv_writer.writerow(rec)
        if "files-read" in args.debug:
            print(f"{FileCache.file_reads} files read")

    if args.normalize:
        if not args.populate_db_path:
            fail("Database path must be specified")
        populated_db = sqlite3.connect(args.populate_db_path)
        CrossrefMetaData.normalize_affiliations(populated_db)
        CrossrefMetaData.normalize_subjects(populated_db)
        args.perf.print("Data normalization")

    if args.journal_data:
        if not args.populate_db_path:
            fail("Database path must be specified")
        csv_sources.load_csv_data(
            args.populate_db_path,
            csv_sources.journals_table,
            args.journal_data,
        )

    if args.funder_data:
        if not args.populate_db_path:
            fail("Database path must be specified")
        csv_sources.load_csv_data(
            args.populate_db_path,
            csv_sources.funders_table,
            args.funder_data,
        )

    if args.open_access_data:
        if not args.populate_db_path:
            fail("Database path must be specified")
        csv_sources.load_csv_data(
            args.populate_db_path,
            csv_sources.open_access_table,
            args.open_access_data,
        )

    if "populated-counts" in args.debug:
        populated_db = sqlite3.connect(args.populate_db_path)
        database_counts(populated_db)

    if "populated-data" in args.debug:
        populated_db = sqlite3.connect(args.populate_db_path)
        database_dump(populated_db)

    if "populated-reports" in args.debug:
        populated_db = sqlite3.connect(args.populate_db_path)
        populated_reports(populated_db)

    if "files-read" in args.debug:
        print(f"{FileCache.file_reads} files read")


if __name__ == "__main__":
    main()
