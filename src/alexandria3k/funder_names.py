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
"""Provide query and population access to the funder table"""

import codecs
import csv

from alexandria3k.common import data_from_uri_provider
from alexandria3k.data_source import DataSource, SINGLE_PARTITION_INDEX
from alexandria3k.virtual_db import ColumnMeta, TableMeta, StreamingTable


# Method names coming from apsw start with uppercase
# pylint: disable=invalid-name


class Source:
    """Virtual table data source.  This gets registered with the apsw
    Connection through createmodule in order to instantiate the virtual
    tables."""

    def __init__(self, table_dict, data_source, sample):
        self.data_source = data_source
        self.sample = sample
        self.table_dict = table_dict

    def get_file_id_iterator(self):
        """Return an iterator over the int identifiers of all data files"""
        # -1 signifies that no partitions exist
        return [SINGLE_PARTITION_INDEX]

    # pylint: disable-next=unused-argument
    def get_file_name_by_id(self, fid):
        """Return the name of the file corresponding to the specified fid"""
        return self.data_source

    def Create(self, _db, _module_name, _db_name, table_name):
        """Create the specified virtual table by creating its schema
        and an apsw table (a StramingTable instance) streaming over its data"""
        table = self.table_dict[table_name]
        return table.table_schema(), StreamingTable(
            table, self.table_dict, self.data_source
        )

    Connect = Create


class FunderNamesCursor:
    """A cursor over the funders data."""

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
        self.raw_input = None
        self.reader = None

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

    # pylint: disable-next=unused-argument
    def Filter(self, index_number, _index_name, constraint_args):
        """Always called first to initialize an iteration to the first row
        of the table according to the index"""
        # print("FILTER", index_number, constraint_args)
        self.eof = False
        self.item_index = -1
        self.raw_input = data_from_uri_provider(self.table.data_source)
        self.reader = csv.reader(
            codecs.iterdecode(self.raw_input, "utf-8"),
            delimiter=self.table.get_table_meta().delimiter,
        )
        next(self.reader, None)  # Skip header row
        self.Next()  # Move to first row

    def Next(self):
        """Advance to the next item."""
        self.row_value = next(self.reader, None)
        if not self.row_value:
            self.eof = True
        else:
            self.item_index += 1

    def Close(self):
        """Cursor's destructor, used for cleanup"""
        self.raw_input.close()


# Crossref funder data https://doi.crossref.org/funderNames?mode=list
# https://www.crossref.org/services/funder-registry/
tables = [
    TableMeta(
        "funder_names",
        cursor_class=FunderNamesCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("url", lambda row: row[0]),
            ColumnMeta("name", lambda row: row[1]),
            ColumnMeta(
                "replaced", lambda row: row[2] if len(row[2]) else None
            ),
        ],
    )
]


class FunderNames(DataSource):
    """
    Create a Crossref funder name meta-data object that supports queries over
    its (virtual) tables and the population of an SQLite database with its
    data.

    :param data_source: The source where the funder data are located
    :type data_source: str
    """

    def __init__(
        self,
        data_source,
        sample=lambda n: True,
        attach_databases=None,
    ):
        table_dict = {t.get_name(): t for t in tables}
        super().__init__(
            Source(table_dict, data_source, sample), tables, attach_databases
        )
