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
"""Virtual database table access"""

# pylint: disable-next=import-error
import apsw

from .file_cache import get_file_cache


class TableMeta:
    """Meta-data of tables we maintain"""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, name, **kwargs):
        self.name = name

        # This table's key that refers to the parent table
        self.foreign_key = kwargs.get("foreign_key")

        # Parent table and its key that joins with this table's foreign key
        self.parent_name = kwargs.get("parent_name")
        self.primary_key = kwargs.get("primary_key")

        self.cursor_class = kwargs.get("cursor_class")
        self.extract_multiple = kwargs.get("extract_multiple")
        self.columns = kwargs["columns"]
        self.post_population_script = kwargs.get("post_population_script")

        # Create dictionary of columns by name
        self.columns_by_name = {}
        for column in self.columns:
            name = column.get_name()
            self.columns_by_name[name] = column

    def table_schema(self, prefix="", columns=None):
        """Return the SQL command to create a table's schema with the
        optional specified prefix.
        A columns array can be used to specify which columns to include."""
        if not columns or "*" in columns:
            columns = [f"  {c.get_definition()}" for c in self.columns]
        # A comma-separated list of the table's columns
        column_list = ",\n".join(columns)
        return f"CREATE TABLE {prefix}{self.name}(\n" + column_list + "\n);\n"

    def insert_statement(self):
        """Return an SQL command to insert data into the table"""
        # A comma-separated list of the table's columns
        columns = [c.get_name() for c in self.columns]
        column_list = ", ".join(columns)

        # A comma-separated list of one question mark per column
        values = ["?" for c in self.columns]
        values_list = ", ".join(values)

        return (
            f"INSERT INTO {self.name}({column_list}) VALUES ({values_list});"
        )

    def get_name(self):
        """Return the table's name"""
        return self.name

    def get_primary_key(self):
        """Return the parent table's column name that refers to our
        foreign key"""
        return self.primary_key

    def get_foreign_key(self):
        """Return our column that refers to the parent table's primary key"""
        return self.foreign_key

    def get_extract_multiple(self):
        """Return the function for obtaining multiple records"""
        return self.extract_multiple

    def get_post_population_script(self):
        """Return the SQL command to run after the table is populated"""
        return self.post_population_script

    def get_parent_name(self):
        """Return the name of the main table of which this has details"""
        return self.parent_name

    def get_cursor_class(self):
        """Return the table's specified cursor class"""
        return self.cursor_class

    def get_columns(self):
        """Return the table's columns"""
        return self.columns

    def get_value_extractor_by_ordinal(self, i):
        """Return defined value extraction function for column at ordinal i"""
        return self.columns[i].get_value_extractor()

    def get_value_extractor_by_name(self, name):
        """Return defined value extraction function for column name"""
        return self.columns_by_name[name].get_value_extractor()

    def get_column_definition_by_name(self, name):
        """Return defined column definition DDL for column name"""
        return self.columns_by_name[name].get_definition()

    def creation_tuple(self, table_dict, data_source):
        """Return the tuple required by the apsw.Source.Create method:
        the table's schema and the virtual table class."""
        return self.table_schema(), StreamingTable(
            self, table_dict, data_source
        )


class ColumnMeta:
    """Meta-data of table columns we maintain"""

    def __init__(self, name, value_extractor=None, **kwargs):
        self.name = name
        self.value_extractor = value_extractor
        self.description = kwargs.get("description")
        self.rowid = kwargs.get("rowid")

    def get_name(self):
        """Return column's name"""
        return self.name

    def get_definition(self):
        """Return column's DDL definition"""
        if self.rowid:
            # Special SQLite name and definition that makes rowid a
            # visible and stable row identifier.
            # See https://sqlite.org/forum/info/f78ca38d8d6bf67f
            return f"{self.name} INTEGER PRIMARY KEY"
        return self.name

    def get_description(self):
        """Return column's description, if any"""
        return self.description

    def get_value_extractor(self):
        """Return the column's value defined extraction function"""
        return self.value_extractor


# By convention column 1 of each table hold the container (file) id
# which is the index of the file in the files array
CONTAINER_ID_COLUMN = 1

ROWID_COLUMN = -1

CONTAINER_INDEX = 1
ROWID_INDEX = 2


class StreamingTable:
    """An apsw table streaming over data of the supplied table metadata"""

    def __init__(self, table_meta, table_dict, data_source):
        self.table_meta = table_meta
        self.table_dict = table_dict
        self.data_source = data_source

    def BestIndex(self, constraints, _orderbys):
        """Called by the Engine to determine the best available index
        for the operation at hand"""
        # print(f"BestIndex gets c={constraints} o={_orderbys}")
        used_constraints = []
        index_number = 0
        for (column, operation) in constraints:
            if (
                column == CONTAINER_ID_COLUMN
                and operation == apsw.SQLITE_INDEX_CONSTRAINT_EQ
            ):
                # Pass value to Filter as constraint_arg[0], and do not
                # require the engine to perform extra checks (exact match)
                used_constraints.append((0, False))
                index_number |= CONTAINER_INDEX
            elif (
                column == ROWID_COLUMN
                and operation == apsw.SQLITE_INDEX_CONSTRAINT_EQ
            ):
                # Pass value to Filter as constraint_arg[1], and do not
                # require the engine to perform extra checks (exact match)
                used_constraints.append((1, False))
                index_number |= ROWID_INDEX
            else:
                # No suitable index
                used_constraints.append(None)
        if index_number != 0:
            # print(f"BestIndex returns: {index_number}, {used_constraints}")
            return (
                used_constraints,
                # First argument to Filter: 0 no index, 1 file index,
                # 2 rowid index, 3 both indexes
                index_number,
                None,  # index name (second argument to Filter)
                False,  # results are not in orderbys order
                2000
                / index_number,  # about 2000 disk i/o (8M file / 4k block)
            )
        return None

    def Disconnect(self):
        """Called when a reference to a virtual table is no longer used"""

    Destroy = Disconnect

    def get_table_meta_by_name(self, name):
        """Return the metadata of the specified table"""
        return self.table_dict[name]

    def cursor(self, table_meta):
        """Return the cursor associated with this table.  The constructor
        for cursors embedded in others takes a parent cursor argument.  To
        handle this requirement, this method recursively calls itself until
        it reaches the top-level table."""
        cursor_class = table_meta.get_cursor_class()
        parent_name = table_meta.get_parent_name()
        if not parent_name:
            return cursor_class(self)
        parent = self.get_table_meta_by_name(parent_name)
        return cursor_class(self, self.cursor(parent))

    def Open(self):
        """Return the table's cursor object"""
        return self.cursor(self.table_meta)

    def get_value_extractor_by_ordinal(self, column_ordinal):
        """Return the value extraction function for column at specified
        ordinal.  Not part of the apsw interface."""
        return self.table_meta.get_value_extractor_by_ordinal(column_ordinal)


class FilesCursor:
    """A cursor over the items data files. Internal use only.
    Not used by a table."""

    def __init__(self, table):
        self.table = table
        self.eof = False
        # The following get initialized in Filter()
        self.file_index = None
        self.single_file = None
        self.file_read = None
        self.items = None

    def Filter(self, index_number, _index_name, constraint_args):
        """Always called first to initialize an iteration to the first
        (possibly constrained) row of the table"""
        # print(f"Filter n={index_number} c={constraint_args}")

        if index_number == 0:
            # No index; iterate through all the files
            self.file_index = -1
            self.single_file = False
        elif index_number & CONTAINER_INDEX:
            # Index; constraint reading through the specified file
            self.single_file = True
            self.file_read = False
            self.file_index = constraint_args[0] - 1
        self.Next()

    def Next(self):
        """Advance reading to the next available file. Files are assumed to be
        non-empty."""
        if self.single_file and self.file_read:
            self.eof = True
            return
        if self.file_index + 1 >= len(self.table.data_source):
            self.eof = True
            return
        self.file_index += 1
        self.items = get_file_cache().read(
            self.table.data_source[self.file_index]
        )
        self.eof = False
        # The single file has been read. Set EOF in next Next call
        self.file_read = True

    def Rowid(self):
        """Return a unique id of the row along all records"""
        return self.file_index

    def current_row_value(self):
        """Return the current row. Not part of the apsw API."""
        return self.items

    def Eof(self):
        """Return True when the end of the table's records has been reached."""
        return self.eof

    def Close(self):
        """Cursor's destructor, used for cleanup"""
        self.items = None


class TableFiller:
    """An object for adding records to a table"""

    def __init__(self, database, table, column_names, is_master=False):
        # A filler on an is_master table can only be called to insert
        # a single record returning its rowid

        # One cursor per object to allow caching the SQL statement
        self.cursor = database.cursor()

        # {title, isbn, rating} → ":title, :isbn, :rating"
        values = ",".join(map(lambda n: f":{n}", column_names))
        ret = " RETURNING rowid" if is_master else ""
        self.is_master = is_master
        self.statement = f"""
            INSERT INTO {table.get_name()} VALUES({values}) {ret}"""

        # Create a dictionary of functions to extract the record values for
        # the specified columns
        self.extractors = {}
        self.extract_multiple = table.get_extract_multiple()
        for cname in column_names:
            self.extractors[cname] = table.get_value_extractor_by_name(cname)
        self.table_name = table.get_name()

    def have_extractors(self):
        """Return True if the table has at least one extractor"""
        return len(self.extractors) > 0

    def add_records(self, data_source, id_name, id_value):
        """Add to the table the required values from the specified data
        source (e.g. XML element tree or JSON tree.
        When a single record is added return its rowid.
        """
        if self.extract_multiple:
            self.add_multiple_records(data_source, id_name, id_value)
            return None
        return self.add_single_record(data_source, id_name, id_value)

    def add_single_record(self, data_source, id_name, id_value):
        """Add to the table the required values from the provided data source"""
        # Create dictionary of names/values to insert
        values = {}
        not_null_values = 0
        for (column_name, extractor) in self.extractors.items():
            if column_name == id_name:
                values[column_name] = id_value
            elif extractor:
                value = extractor(data_source)
                values[column_name] = value
                if value is not None:
                    not_null_values += 1

        # No insertion if all non-key values are NULL
        if not_null_values == 0:
            return None

        self.cursor.execute(
            self.statement,
            values,
            prepare_flags=apsw.SQLITE_PREPARE_PERSISTENT,
        )
        if not self.is_master:
            return None
        (rowid,) = self.cursor.fetchone()
        return rowid

    def add_multiple_records(self, data_source, id_name, id_value):
        """Add to the table the required values from the XML element tree"""
        records = []
        for record in self.extract_multiple(data_source):
            # Create dictionary of names/values to insert
            values = {}
            not_null_values = 0
            for (column_name, extractor) in self.extractors.items():
                if column_name == id_name:
                    values[column_name] = id_value
                else:
                    value = extractor(record)
                    values[column_name] = value
                    if value is not None:
                        not_null_values += 1

            # No insertion if all non-key values are NULL
            if not_null_values > 0:
                records.append(values)

        self.cursor.executemany(
            self.statement,
            records,
            prepare_flags=apsw.SQLITE_PREPARE_PERSISTENT,
        )

    def get_table_name(self):
        """Return the name of the filled table"""
        return self.table_name
