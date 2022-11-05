#!/usr/bin/env python3
#
# Alexandria2k Crossref bibliographic metadata processing
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
import sqlite3
import sys

import apsw

import crossref
from file_cache import FileCache


class CrossrefMetaData:
    """Create a Crossref meta-data object that support queries over its
    (virtual) table and the population of an SQLite database with its
    data"""

    def __init__(
        self,
        container_directory,
        _sample_container=lambda name: True,
        _source=None,
        _cached_files=1,
        _cached_size=None,
    ):
        self.vdb = apsw.Connection(":memory:")
        # Register the module as filesource
        self.data_source = crossref.Source(container_directory)
        self.vdb.createmodule("filesource", self.data_source)

        for table in crossref.tables:
            self.vdb.execute(
                f"CREATE VIRTUAL TABLE {table.get_name()} USING filesource()"
            )

    def get_virtual_db(self):
        """Return the virtual table database as an apsw object"""
        return self.vdb

    def create_index(self, table, column):
        """Create a database index for the specified table column"""
        self.vdb.execute(
            f"CREATE INDEX populated.{table}_{column}_idx ON {table}({column})"
        )

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

        if not partition:
            for row in self.vdb.execute(query):
                yield row
        else:
            for i in self.data_source.get_file_id_iterator():
                container_query = query.replace("CONTAINER_ID", str(i))
                query_results = self.vdb.execute(container_query)
                for row in query_results:
                    yield row

    def populate_database(
        self, database_path, _columns, _conditions, _indexes
    ):
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

        # Create the populated database, if needed
        if not os.path.exists(database_path):
            pdb = sqlite3.connect(database_path)
            pdb.close()

        self.vdb.execute(f"ATTACH DATABASE '{database_path}' AS populated")

        # Create empty tables
        for table in crossref.tables:
            self.vdb.execute(
                f"DROP TABLE IF EXISTS populated.{table.get_name()}"
            )
            self.vdb.execute(table.table_schema("populated."))

        self.create_index("works", "doi")
        self.create_index("work_authors", "id")
        self.create_index("work_authors", "work_doi")
        self.create_index("author_affiliations", "author_id")
        self.create_index("work_references", "work_doi")
        self.create_index("work_updates", "work_doi")
        self.create_index("work_subjects", "work_doi")
        self.create_index("work_funders", "work_doi")

        # Populate all tables from the records of each file in sequence.
        # This improves the locality of reference and through the constraint
        # indexing and the file cache avoids opening, reading, decompressing,
        # and parsing each file multiple times.
        for i in self.data_source.get_file_id_iterator():
            # Sampling:
            #           WHERE abs(random() % 100000) = 0"""
            #           WHERE update_count is not null
            self.vdb.execute(
                f"""
                INSERT INTO populated.works SELECT * FROM works
                    WHERE container_id = {i}
                """
            )

            self.vdb.execute(
                f"""
                INSERT INTO populated.work_authors
                    SELECT work_authors.* FROM work_authors
                    INNER JOIN populated.works
                        ON work_authors.work_doi = populated.works.doi
                    WHERE work_authors.container_id = {i}
                """
            )

            self.vdb.execute(
                f"""
                INSERT INTO populated.author_affiliations
                    SELECT author_affiliations.* FROM author_affiliations
                    INNER JOIN populated.work_authors
                      ON author_affiliations.author_id
                        = populated.work_authors.id
                    WHERE author_affiliations.container_id = {i}
                """
            )

            self.vdb.execute(
                f"""
                INSERT INTO populated.work_references
                    SELECT work_references.* FROM work_references
                    INNER JOIN populated.works
                        ON work_references.work_doi = populated.works.doi
                    WHERE work_references.container_id = {i}
                """
            )

            self.vdb.execute(
                f"""
                INSERT INTO populated.work_updates
                    SELECT work_updates.* FROM work_updates
                        INNER JOIN populated.works
                            ON work_updates.work_doi = populated.works.doi
                    WHERE work_updates.container_id = {i}
                """
            )

            self.vdb.execute(
                f"""
                INSERT INTO populated.work_subjects
                    SELECT work_subjects.* FROM work_subjects
                        INNER JOIN populated.works
                            ON work_subjects.work_doi = populated.works.doi
                    WHERE work_subjects.container_id = {i}
                """
            )

            self.vdb.execute(
                f"""
                INSERT INTO populated.work_funders
                    SELECT work_funders.* FROM work_funders
                        INNER JOIN populated.works
                            ON work_funders.work_doi = populated.works.doi
                    WHERE work_funders.container_id = {i}
                """
            )

        self.vdb.execute("DETACH populated")

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


def database_dump(database):
    """Print the passed database data"""

    for table in crossref.tables:
        name = table.get_name()
        print(f"TABLE {name}")
        for rec in database.execute(f"SELECT * FROM {name}"):
            print("\t".join(rec))


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

    print(f"{FileCache.file_reads} files read")


def parse_cli_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="a3k: Publication metadata interface"
    )

    parser.add_argument(
        "-B", "--cached-bytes", type=str, help="Size of data cache"
    )
    parser.add_argument(
        "-c",
        "--columns",
        nargs="*",
        type=str,
        help="Columns to populate using table.column or table.*",
    )
    parser.add_argument(
        "-D",
        "--dump",
        action="store_true",
        help="Dump the data of the virtual and populated databases",
    )
    parser.add_argument(
        "-d",
        "--directory",
        required=True,
        type=str,
        help="Directory storing the downloaded data",
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
        "-L",
        "--list-schema",
        action="store_true",
        help="List the schema of the scanned database",
    )
    parser.add_argument(
        "-M",
        "--metrics",
        action="store_true",
        help="Output metrics regarding files read",
    )
    parser.add_argument(
        "-n",
        "--normalize",
        action="store_true",
        help="Normalize relations in the populated database",
    )
    parser.add_argument(
        "-N",
        "--cached-file-number",
        type=int,
        help="Number of files to cache in memory",
    )
    parser.add_argument(
        "-P",
        "--partition",
        action="store_true",
        help="Run the query over partitioned data slices",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file for query results",
    )
    parser.add_argument(
        "-p",
        "--populate",
        type=str,
        help="Populate the SQLite database in the specified path",
    )
    parser.add_argument(
        "-q", "--query", type=str, help="Query to run on the virtual tables"
    )
    parser.add_argument(
        "-r",
        "--row-selection",
        nargs="*",
        type=str,
        help="SQL expressions that select the populated rows",
    )
    parser.add_argument(
        "-s",
        "--sample",
        default="True",
        type=str,
        help="Python expression to sample the Crossref tables",
    )
    return parser.parse_args()


def main():
    """Program entry point"""
    args = parse_cli_arguments()

    # pylint: disable=W0123
    sample = eval(f"lambda word: {args.sample}")
    crmd = CrossrefMetaData(
        args.directory,
        sample,
        None,
        args.cached_file_number,
        args.cached_bytes,
    )

    if args.dump:
        # Streaming interface
        database_counts(crmd.get_virtual_db())
        database_dump(crmd.get_virtual_db())
        # Before population
        print(f"{FileCache.file_reads} files read")

    if args.populate:
        if args.index:
            indexes = [x.split(":", 1) for x in args.index]
        else:
            indexes = []
        crmd.populate_database(
            args.populate, args.columns, args.row_selection, indexes
        )

    if args.query:
        if args.output:
            # pylint: disable=R1732
            csv_file = open(
                args.output, "w", newline="", encoding=args.output_encoding
            )
        else:
            sys.stdout.reconfigure(encoding=args.output_encoding)
            csv_file = sys.stdout
        csv_writer = csv.writer(csv_file, delimiter=args.field_separator)
        for rec in crmd.query(args.query, args.partition):
            csv_writer.writerow(rec)

    if args.normalize:
        populated_db = sqlite3.connect("populated.db")
        CrossrefMetaData.normalize_affiliations(populated_db)
        CrossrefMetaData.normalize_subjects(populated_db)

    if args.dump:
        # Populated database
        populated_db = sqlite3.connect(args.populate)
        database_counts(populated_db)
        database_dump(populated_db)
        populated_reports(populated_db)

    if args.metrics:
        print(f"{FileCache.file_reads} files read")


if __name__ == "__main__":
    main()
