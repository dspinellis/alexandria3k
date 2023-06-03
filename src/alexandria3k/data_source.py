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
"""Virtual database table access of arbitrary data"""

import abc
import csv
import os
import re
import sqlite3

# pylint: disable-next=import-error
import apsw

from alexandria3k.common import (
    add_columns,
    fail,
    get_string_resource,
    log_sql,
    set_fast_writing,
    warn,
)
from alexandria3k import debug
from alexandria3k import perf
from alexandria3k.tsort import tsort
from alexandria3k.virtual_db import CONTAINER_ID_COLUMN

# Set or compare for equality to this reference for an index value
# is used to denote a single partition
SINGLE_PARTITION_INDEX = "SINGLE_PARTITION"


class ElementsCursor:
    """An (abstract) cursor over a collection of data embedded within
    another cursor."""

    __metaclass__ = abc.ABCMeta

    def __init__(self, table, parent_cursor):
        """Not part of the apsw VTCursor interface.
        The table agument is a StreamingTable object"""
        self.table = table
        self.parent_cursor = parent_cursor
        self.elements = None
        self.eof = None
        # Initialized in Filter()
        self.element_index = None

    @abc.abstractmethod
    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return

    # pylint: disable=arguments-differ
    def Filter(self, *args):
        """Always called first to initialize an iteration to the first row
        of the table"""
        self.parent_cursor.Filter(*args)
        self.elements = None
        self.Next()

    def Eof(self):
        """Return True when the end of the table's records has been reached."""
        return self.eof

    @abc.abstractmethod
    def Rowid(self):
        """Return a unique id of the row along all records"""
        return

    def record_id(self):
        """Return the record's identifier. Not part of the apsw API."""
        return self.Rowid()

    def current_row_value(self):
        """Return the current row. Not part of the apsw API."""
        return self.elements[self.element_index]

    def Next(self):
        """Advance reading to the next available element."""
        while True:
            if self.parent_cursor.Eof():
                self.eof = True
                return
            if not self.elements:
                self.elements = self.parent_cursor.current_row_value().get(
                    self.element_name()
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

    def container_id(self):
        """Return the id of the container containing the data being fetched.
        Not part of the apsw API."""
        return self.parent_cursor.container_id()

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == -1:
            return self.Rowid()

        if col == CONTAINER_ID_COLUMN:
            return self.container_id()

        extract_function = self.table.get_value_extractor_by_ordinal(col)
        return extract_function(self.current_row_value())

    def Close(self):
        """Cursor's destructor, used for cleanup"""
        self.parent_cursor.Close()
        self.elements = None


class IndexManager:
    """Create database indexes, avoiding duplication, and allowing
    them to be dropped."""

    def __init__(self, database, root_name):
        self.database = database
        self.root_name = root_name
        self.indexes = set()

    def create_index(self, table, column):
        """Create an index on the specified table and column, if required"""
        if table == f"temp_{self.root_name}":
            table = "temp_matched"
        index = (table, column)
        if index in self.indexes:
            return

        self.database.execute(
            log_sql(
                f"""CREATE INDEX {table}_{column}_idx ON {table}({column})"""
            )
        )
        self.indexes.add((table, column))

    def drop_indexes(self):
        """Drop all created indexes"""
        for table, column in self.indexes:
            self.database.execute(log_sql(f"DROP INDEX {table}_{column}_idx"))
        self.indexes.clear()


class DataSource:
    """
    Create a meta-data object that supports queries over its
    (virtual) tables and the population of an SQLite database with its
    data.

    :param data_source: An object that shall supply the database elements
    :type data_source: DataSource

    :param tables: A list of the table metadata associated with the data source
        The first table in the list shall be the root table of the hierarchy.
    :type tables: TableMeta

    :param attach_databases: A list of colon-joined tuples specifying
        a database name and its path, defaults to `None`.
        The specified databases are attached and made available to the
        query and the population condition through the specified database
        name.
    :type attach_databases: list, optional

    """

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        data_source,
        tables,
        attach_databases=None,
    ):
        # Name of root table
        self.root_name = tables[0].get_name()

        self.tables = tables
        self.table_dict = {t.get_name(): t for t in tables}

        # A named in-memory database; it can be attached by name to others
        self.vdb = apsw.Connection(
            "file:virtual?mode=memory&cache=shared",
            apsw.SQLITE_OPEN_URI | apsw.SQLITE_OPEN_READWRITE,
        )
        self.cursor = self.vdb.cursor()
        # Register the module as filesource
        self.data_source = data_source
        self.vdb.createmodule("filesource", self.data_source)

        # Dictionaries of tables containing a set of columns required
        # for querying or populating the database
        self.query_columns = {}
        self.population_columns = {}
        self.query_and_population_columns = {}
        self.index_manager = None

        # Attach specified databases
        self.attached_databases = []
        self.attach_commands = []
        if attach_databases is None:
            attach_databases = []
        for db_spec in attach_databases:
            try:
                (db_name, db_path) = db_spec.split(":")
            except ValueError:
                fail(
                    f"Invalid database specification: '{db_spec}'; expected name:path"
                )
            attach_command = f"ATTACH DATABASE '{db_path}' AS {db_name}"
            self.vdb.execute(log_sql(attach_command))
            self.attached_databases.append(db_name)
            self.attach_commands.append(attach_command)

        # Create virtual table placeholders
        for table in tables:
            self.vdb.execute(
                log_sql(
                    f"CREATE VIRTUAL TABLE {table.get_name()} USING filesource()"
                )
            )

    def get_table_meta_by_name(self, name):
        """Return the metadata of the specified table"""
        try:
            return self.table_dict[name]
        except KeyError:
            fail(f"Unknown table name: '{name}'.")
            # NOTREACHED
            return None

    def tables_transitive_closure(self, table_list, top):
        """Return the transitive closure of all named tables
        with all the ones required to reach the specified top
        """
        result = set([top])
        for table_name in table_list:
            while table_name not in result:
                result.add(table_name)
                table = self.get_table_meta_by_name(table_name)
                table_name = table.get_parent_name()
        return result

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

            def authorizer(op_code, table, column, database, _trigger):
                """Query authorizer to monitor used columns"""
                if (
                    op_code == apsw.SQLITE_READ
                    and column
                    and database not in self.attached_databases
                ):
                    # print(f"AUTH: adding {table}.{column}")
                    DataSource.add_column(self.query_columns, table, column)
                return apsw.SQLITE_OK

            def tracer(_cursor, _query, _bindings):
                """An execution tracer that denies the query's operation"""
                # Abort the query's evaluation with an exception.  Returning
                # apsw.SQLITE_DENY seems to be doing something that takes
                # minutes to finish
                return False

            # Add the columns required by the actual query
            self.cursor.setexectrace(tracer)
            self.vdb.setauthorizer(authorizer)
            self.cursor.execute(log_sql(query), can_cache=False)
            # NOTREACHED

        try:
            trace_query_columns(query)
        except apsw.ExecTraceAbort:
            pass
        self.vdb.setauthorizer(None)
        self.cursor.setexectrace(None)

    def query(self, query, partition=False):
        """
        Run the specified query on the virtual database using the data
        specified in the object constructor's call.

        :param query: An SQL `SELECT` query specifying the required data.
        :type query: str

        :param partition: When true the query will run separately in each
            container, defaults to `False`.
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
            in quadratic (or worse) algorithmic complexity.
        :type partition: bool, optional

        :return: An iterable over the query's results.
        :rtype: iterable
        """

        self.cursor = self.vdb.cursor()

        # Easy case
        if not partition:
            for row in self.cursor.execute(log_sql(query)):
                yield row
            return

        # Even when restricting multiple JOINs with container_id
        # SQLite seems to scan all containers for each JOIN making the
        # performance intolerably slow. Address this by creating non-virtual
        # tables with the required columns for each partition, as follows.
        #
        # Identify required tables and columns
        # Create an in-memory database
        # Attach database partition and other attached dbs to in-memory database
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
            log_sql(
                "ATTACH DATABASE 'file:virtual?mode=memory&cache=shared' AS virtual"
            )
        )

        # Also attach databases to the partition
        for attach_command in self.attach_commands:
            partition.execute(log_sql(attach_command))

        for i in self.data_source.get_file_id_iterator():
            debug.log(
                "progress",
                f"Container {i} {self.data_source.get_file_name_by_id(i)}",
            )
            for table_name, table_columns in self.query_columns.items():
                columns = ", ".join(table_columns)
                partition.execute(
                    log_sql(
                        f"""CREATE TABLE {table_name}
                  AS SELECT {columns} FROM virtual.{table_name}
                    WHERE virtual.{table_name}.container_id={i}"""
                    )
                )
            self.cursor = partition.cursor()
            for row in self.cursor.execute(log_sql(query)):
                yield row
            for table_name in self.query_columns:
                partition.execute(log_sql(f"DROP TABLE {table_name}"))

    def get_query_column_names(self):
        """Return the column names associated with an executing query"""
        return [description[0] for description in self.cursor.description]

    def populate(
        self,
        database_path,
        columns=None,
        condition=None,
    ):
        """
        Populate the specified SQLite database using the data specified
        in the object constructor's call.
        The database is created if it does not exist.
        If it exists, the tables to be populated are dropped
        (if they exist) and recreated anew as specified.

        :param database_path: The path specifying the SQLite database
            to populate.
        :type database_path: str

        :param columns: A list of strings specifying the columns to
            populate, defaults to `None`.  The strings are of the form
            `table_name.column_name` or `table_name.*`.
        :type columns: list, optional

        :param condition: `SQL expression`_ specifying the rows to include
            in the database's population, defaults to `None`.
            The expression can contain references to the table's columns.
            Implicitly, if a main table is populated, its details tables
            will only get populated with the records associated with the
            correspoing main table's record.
        :type condition: str, optional


        .. _SQL expression: https://www.sqlite.org/syntax/expr.html
        """

        # pylint: disable=too-many-statements
        def set_join_columns():
            """Add columns required for joins"""
            to_add = []
            for table_name in query_and_population_tables():
                while table_name:
                    table = self.get_table_meta_by_name(table_name)
                    parent_table_name = table.get_parent_name()
                    primary_key = table.get_primary_key()
                    foreign_key = table.get_foreign_key()
                    if foreign_key:
                        to_add.append((table_name, foreign_key))
                    if parent_table_name and primary_key:
                        to_add.append((parent_table_name, primary_key))
                    table_name = parent_table_name
            # print("ADD COLUMNS ", to_add)
            for table, column in to_add:
                DataSource.add_column(
                    self.query_and_population_columns, table, column
                )

        def query_and_population_tables():
            """Return a sequence consisting of the tables required
            for populating and querying the data"""
            return set.union(
                set(self.population_columns.keys()),
                set(self.query_columns.keys()),
            )

        def joined_tables(table_names, rename_temp):
            """Return JOIN statements for all specified tables.
            If rename_temp is True, temporary tables are renamed to
            their virtual names (e.g. temp_workers becomes workers).
            This change provides a context for evaluating user-specified
            queries."""
            result = ""
            tables_meta = [self.get_table_meta_by_name(t) for t in table_names]
            sorted_tables = tsort(tables_meta, table_names)
            debug.log("sorted-tables", sorted_tables)
            for table_name in sorted_tables:
                if table_name == self.root_name:
                    continue
                table = self.get_table_meta_by_name(table_name)
                parent_table_name = table.get_parent_name()
                primary_key = table.get_primary_key()
                foreign_key = table.get_foreign_key()
                if rename_temp:
                    rename = f"AS {table_name}"
                    primary_table_name = parent_table_name
                    foreign_table_name = table_name
                else:
                    rename = ""
                    primary_table_name = f"temp_{parent_table_name}"
                    foreign_table_name = f"temp_{table_name}"
                result += f""" INNER JOIN temp_{table_name} {rename} ON
                    {primary_table_name}.{primary_key}
                      = {foreign_table_name}.{foreign_key}"""
                if not rename_temp:
                    self.index_manager.create_index(
                        f"temp_{parent_table_name}", primary_key
                    )
                    self.index_manager.create_index(
                        f"temp_{table_name}", foreign_key
                    )
            return result

        def populate_only_root_table(
            table, partition_index, selection_condition
        ):
            """Populate the root table, when no other tables will be needed"""

            columns = ", ".join(
                [f"{table}.{col}" for col in self.population_columns[table]]
            )
            if not selection_condition:
                selection_condition = "true"

            # Partition is set to -1 when no partitions exist
            partition_condition = (
                "true"
                if partition_index is SINGLE_PARTITION_INDEX
                else f"{table}.container_id = {partition_index}"
            )
            # No need for temp table matching at the root
            self.vdb.execute(
                log_sql(
                    f"""
                INSERT INTO populated.{table}
                SELECT {columns} FROM {table}
                WHERE {partition_condition}
                  AND {selection_condition}
            """
                )
            )
            perf.log(f"Populate {table}")

        def populate_table(table, partition_index, condition):
            """Populate the specified table"""

            columns = ", ".join(
                [f"{table}.{col}" for col in self.population_columns[table]]
            )

            if condition:
                path = self.tables_transitive_closure([table], self.root_name)

                # One would think that an index on rowid is implied, but
                # removing it increases the time required to process
                # 3581.json.gz from the April 2022 dataset from 6.5"
                # to 18.4".
                self.index_manager.create_index(f"temp_{table}", "rowid")

                # Putting AND in the JOIN condition, rather than WHERE
                # improves dramatically the execution's performance time
                exists = f"""AND EXISTS (SELECT 1
                  FROM temp_matched AS temp_{self.root_name}
                  {joined_tables(path, False)}
                  {"AND" if len(path) > 1 else "WHERE"}
                    {table}.rowid = temp_{table}.rowid)"""
            else:
                exists = ""

            statement = f"""
                INSERT INTO populated.{table}
                    SELECT {columns} FROM {table}
                    WHERE {table}.container_id = {partition_index} {exists}
                """
            self.vdb.execute(log_sql(statement))
            perf.log(f"Populate {table}")

        def create_database_schema(columns):
            """Create the populated database, if needed"""
            if not os.path.exists(database_path):
                pdb = sqlite3.connect(database_path)
                pdb.close()

            self.vdb.execute(
                log_sql(f"ATTACH DATABASE '{database_path}' AS populated")
            )
            set_fast_writing(self.vdb)

            self.index_manager = IndexManager(self.vdb, self.root_name)

            add_columns(
                columns,
                self.tables,
                lambda table, column: DataSource.add_column(
                    self.population_columns, table, column
                ),
            )

            # Setup the columns required for executing the query
            if condition:
                table_names = ", ".join(self.table_dict.keys())
                query = f"""SELECT DISTINCT 1 FROM {table_names} WHERE {condition}"""
                self.set_query_columns(query)
                set_join_columns()
                perf.log("Condition parsing")

            # Create empty tables
            for table_name, table_columns in self.population_columns.items():
                table = self.get_table_meta_by_name(table_name)
                self.vdb.execute(
                    log_sql(f"DROP TABLE IF EXISTS populated.{table_name}")
                )
                self.vdb.execute(
                    log_sql(table.table_schema("populated.", table_columns))
                )
            perf.log("Table creation")

        def create_matched_tables(matched_tables):
            """Create copies of the virtual tables for fast access"""
            for table in matched_tables:
                columns = self.query_and_population_columns.get(table)
                if columns:
                    columns = set.union(columns, {"rowid"})
                else:
                    columns = {"rowid"}

                # Add query columns
                query_columns_of_table = self.query_columns.get(table)
                if query_columns_of_table:
                    columns = set.union(columns, query_columns_of_table)

                column_list = ", ".join(columns)
                self.vdb.execute(
                    log_sql(f"""DROP TABLE IF EXISTS temp_{table}""")
                )
                create = f"""CREATE TEMP TABLE temp_{table} AS
                    SELECT {column_list} FROM {table}
                    WHERE container_id = {i}"""
                self.vdb.execute(log_sql(create))
            perf.log("Virtual table copies")

            # Create a table containing the root table ids ids for all root
            # table elements matching the query, which is executed in a context
            # containing all required tables.
            query_table_names = self.tables_transitive_closure(
                self.query_columns.keys(), self.root_name
            )
            create = (
                f"""CREATE TEMP TABLE temp_matched AS
                        SELECT {self.root_name}.id, {self.root_name}.rowid
                        FROM temp_{self.root_name} AS {self.root_name} """
                + joined_tables(query_table_names, True)
                + f" WHERE ({condition})"
            )
            self.vdb.execute(log_sql("DROP TABLE IF EXISTS temp_matched"))
            self.vdb.execute(log_sql(create))

            if debug.enabled("dump-matched"):
                csv_writer = csv.writer(debug.get_output(), delimiter="\t")
                for rec in self.vdb.execute("SELECT * FROM temp_matched"):
                    csv_writer.writerow(rec)

            perf.log("Matched table creation")

        def run_post_population_script(table):
            """Run the post population script of the specified table,
            if available, ignoring errors of individual statements."""
            table_meta = self.get_table_meta_by_name(table)
            post_population_script = table_meta.get_post_population_script()
            if not post_population_script:
                return

            pdb = sqlite3.connect(database_path)
            script = get_string_resource(post_population_script)
            # remove C-style comments
            script = re.sub(r"/\*.*?\*/", "", script, flags=re.DOTALL)
            # remove SQL single-line comments
            script = re.sub(r"--.*$", "", script, flags=re.MULTILINE)
            statements = script.strip().split(";")

            for statement in statements:
                try:
                    pdb.execute(log_sql(statement))
                    perf.log(f"Run {post_population_script} {statement}")
                except sqlite3.Error as err:
                    warn(
                        f"{post_population_script}: "
                        f"Unable to execute {statement}: {err} "
                        "(Column not populated?)"
                    )

            pdb.execute(log_sql("COMMIT"))
            pdb.close()

        create_database_schema(columns)
        # Populate all tables from the records of each file in sequence.
        # This improves the locality of reference and through the constraint
        # indexing and the file cache avoids opening, reading, decompressing,
        # and parsing each file multiple times.
        matched_tables = query_and_population_tables()
        for i in self.data_source.get_file_id_iterator():
            debug.log(
                "progress",
                f"Container {i} {self.data_source.get_file_name_by_id(i)}",
            )

            if len(matched_tables) == 1:
                # False positive
                # pylint: disable-next=unbalanced-dict-unpacking
                (table,) = self.population_columns
                populate_only_root_table(table, i, condition)
            else:
                if condition:
                    create_matched_tables(matched_tables)

                for table in self.population_columns:
                    populate_table(table, i, condition)
                self.index_manager.drop_indexes()
        perf.log("Table population")

        self.vdb.execute(log_sql("DETACH populated"))
        self.vdb.close()
        for table in self.population_columns:
            run_post_population_script(table)
