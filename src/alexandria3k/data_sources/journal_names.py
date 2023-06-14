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
"""Crossref journal names"""


from alexandria3k.csv_source import CsvCursor, VTSource
from alexandria3k.data_source import DataSource
from alexandria3k.db_schema import ColumnMeta, TableMeta

DEFAULT_SOURCE = "http://ftp.crossref.org/titlelist/titleFile.csv"

# Crossref journal data http://ftp.crossref.org/titlelist/titleFile.csv
journals_table = TableMeta(
    "journal_names",
    cursor_class=CsvCursor,
    columns=[
        ColumnMeta("id"),
        ColumnMeta("title"),
        ColumnMeta("crossref_id"),
        ColumnMeta("publisher"),
        ColumnMeta("issn_print"),
        ColumnMeta("issn_eprint"),
        ColumnMeta("issns_additional"),
        ColumnMeta("doi"),
        ColumnMeta("volume_info"),
    ],
    post_population_script="sql/normalize-journal-names-issns.sql",
)

journals_issns_table = TableMeta(
    "journals_issns",
    columns=[
        ColumnMeta("journal_id"),
        ColumnMeta("issn"),
        ColumnMeta(
            "issn_type", description="A: Additional, E: Electronic, P: Print"
        ),
    ],
)


tables = [
    journals_table,
    journals_issns_table,
]


class JournalNames(DataSource):
    """
    Create an object containing journal meta-data that supports queries over
    its (virtual) table and the population of an SQLite database with its
    data.

    :param data_source: The location (file path or URL) where the journal data
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
            VTSource(journals_table, data_source, sample),
            [journals_table],
            attach_databases,
        )
