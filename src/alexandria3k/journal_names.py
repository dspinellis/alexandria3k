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
"""Provide query and population access to the Crossref journal names data."""


from alexandria3k.csv_sources import CsvCursor, VTSource
from alexandria3k.data_source import DataSource
from alexandria3k.virtual_db import ColumnMeta, TableMeta

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
        super().__init__(
            VTSource(journals_table, data_source, sample),
            [journals_table],
            attach_databases,
        )
