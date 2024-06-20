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
"""A module supporting virtual database table schema definition."""


class TableMeta:
    """A container for table meta-data"""

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
        self.extract_multiple_parent = kwargs.get("extract_multiple_parent")
        self.columns = kwargs["columns"]
        self.post_population_script = kwargs.get("post_population_script")

        self.delimiter = kwargs.get("delimiter") or ","

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
        else:
            columns = [
                f"  {self.get_column_definition_by_name(c)}" for c in columns
            ]
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

    def get_parent_extract_multiple(self):
        """Return the function for obtaining multiple records from the parent table"""
        return self.extract_multiple_parent

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


class ColumnMeta:
    """A container for column meta-data"""

    def __init__(self, name, value_extractor=None, **kwargs):
        self.name = name
        self.value_extractor = value_extractor
        self.description = kwargs.get("description")
        self.rowid = kwargs.get("rowid")
        self.data_type = kwargs.get("data_type")

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
        return f"{self.name} {self.data_type}" if self.data_type else self.name

    def get_description(self):
        """Return column's description, if any"""
        return self.description

    def get_value_extractor(self):
        """Return the column's value defined extraction function"""
        return self.value_extractor
