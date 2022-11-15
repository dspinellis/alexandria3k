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

import abc
import os

import apsw

from file_cache import get_file_cache


class TableMeta:
    """Meta-data of tables we maintain"""

    def __init__(self, name, **kwargs):
        self.name = name

        # This table's key that refers to the parent table
        self.foreign_key = kwargs.get("foreign_key")

        # Parent table and its key that joins with this table's foreign key
        self.parent_name = kwargs.get("parent_name")
        self.primary_key = kwargs.get("primary_key")

        self.cursor_class = kwargs["cursor_class"]
        self.columns = kwargs["columns"]

    def table_schema(self, prefix="", columns=None):
        """Return the SQL command to create a table's schema with the
        optional specified prefix.
        A columns array can be used to specify which columns to include."""
        if not columns or "*" in columns:
            columns = [c.get_name() for c in self.columns]
        # A comma-separated list of the table's columns
        column_list = ", ".join(columns)
        return f"CREATE TABLE {prefix}{self.name}(" + column_list + ")"

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

    def get_parent_name(self):
        """Return the name of the main table of which this has details"""
        return self.parent_name

    def get_cursor_class(self):
        """Return the table's specified cursor class"""
        return self.cursor_class

    def get_value_extractor(self, i):
        """Return the value extraction function for column at ordinal i"""
        return self.columns[i].get_value_extractor()

    def creation_tuple(self, table_dict, data_source):
        """Return the tuple required by the apsw.Source.Create method:
        the table's schema and the virtual table class."""
        return self.table_schema(), StreamingTable(
            self, table_dict, data_source
        )


class ColumnMeta:
    """Meta-data of table columns we maintain"""

    def __init__(self, name, value_extractor):
        self.name = name
        self.value_extractor = value_extractor

    def get_name(self):
        """Return column's name"""
        return self.name

    def get_value_extractor(self):
        """Return the column's value extraction function"""
        return self.value_extractor


# By convention column 1 of each table hold the container (file) id
# which is the index of the file in the files array
CONTAINER_ID_COLUMN = 1


class StreamingTable:
    """An apsw table streaming over data of the supplied table metadata"""

    def __init__(self, table_meta, table_dict, data_source):
        self.table_meta = table_meta
        self.table_dict = table_dict
        self.data_source = data_source

    def BestIndex(self, constraints, _orderbys):
        """Called by the Engine to determine the best available index
        for the operation at hand"""
        # print(f"BestIndex c={constraints} o={orderbys}")
        used_constraints = []
        found_index = False
        for (column, operation) in constraints:
            if (
                column == CONTAINER_ID_COLUMN
                and operation == apsw.SQLITE_INDEX_CONSTRAINT_EQ
            ):
                # Pass value to Filter as constraint_arg[0], and do not
                # require the engine to perform extra checks (exact match)
                used_constraints.append((0, False))
                found_index = True
            else:
                # No suitable index
                used_constraints.append(None)
        if found_index:
            return (
                used_constraints,
                1,  # index number
                None,  # index name
                False,  # results are not in orderbys order
                2000,  # about 2000 disk i/o (8M file / 4k block)
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

    def get_value_extractor(self, column_ordinal):
        """Return the value extraction function for column at specified
        ordinal.  Not part of the apsw interface."""
        return self.table_meta.get_value_extractor(column_ordinal)


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
        # print(f"Filter c={constraint_args}")

        if index_number == 0:
            # No index; iterate through all the files
            self.file_index = -1
            self.single_file = False
        else:
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