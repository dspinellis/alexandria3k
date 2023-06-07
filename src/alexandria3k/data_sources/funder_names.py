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
"""Crossref funder names"""


from alexandria3k.csv_source import CsvCursor, VTSource
from alexandria3k.data_source import DataSource
from alexandria3k.db_schema import ColumnMeta, TableMeta

DEFAULT_SOURCE = "https://doi.crossref.org/funderNames?mode=list"

# Crossref funder data https://doi.crossref.org/funderNames?mode=list
# https://www.crossref.org/services/funder-registry/
table = TableMeta(
    "funder_names",
    cursor_class=CsvCursor,
    columns=[
        ColumnMeta("id"),
        ColumnMeta("url"),
        ColumnMeta("name"),
        ColumnMeta("replaced", lambda row: row[2] if len(row[2]) else None),
    ],
)

tables = [table]


class FunderNames(DataSource):
    """
    Create an object containing Crossref funder name meta-data that supports
    queries over its (virtual) table and the population of an SQLite database
    with its data.

    :param data_source: The location (file path or URL) where the funder data
      are located.
    :type data_source: str

    :param sample: A callable to row sampling, defaults to `lambda n: True`.
        The population or query method will call this argument
        for each record with the record's data as its argument.  When the
        callable returns `True` the record will get processed, when it
        returns `False` the record will get skipped.
    :type sample: callable, optional

    :param attach_databases: A list of colon-joined tuples specifying
        a database name and its path, defaults to `None`.
        The specified databases are attached and made available to the
        query and the population condition through the specified database
        name.
    :type attach_databases: list, optional
    """

    def __init__(
        self,
        data_source,
        sample=lambda n: True,
        attach_databases=None,
    ):
        super().__init__(
            VTSource(table, data_source, sample), [table], attach_databases
        )
