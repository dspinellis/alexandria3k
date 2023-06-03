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


from alexandria3k.csv_sources import CsvCursor, VTSource
from alexandria3k.data_source import DataSource
from alexandria3k.virtual_db import ColumnMeta, TableMeta


# Crossref funder data https://doi.crossref.org/funderNames?mode=list
# https://www.crossref.org/services/funder-registry/
table = TableMeta(
    "funder_names",
    cursor_class=CsvCursor,
    columns=[
        ColumnMeta("id"),
        ColumnMeta("url", lambda row: row[0]),
        ColumnMeta("name", lambda row: row[1]),
        ColumnMeta("replaced", lambda row: row[2] if len(row[2]) else None),
    ],
)


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
        super().__init__(
            VTSource(table, data_source, sample), [table], attach_databases
        )
