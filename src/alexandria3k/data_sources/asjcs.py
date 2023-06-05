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
"""Scopus Subject Areas and All Science Journal Classification Codes (ASJC) data"""


from alexandria3k.csv_sources import CsvCursor, VTSource
from alexandria3k.data_source import DataSource
from alexandria3k.virtual_db import ColumnMeta, TableMeta

DEFAULT_SOURCE = "resource:data/asjc.csv"


# Scopus Subject Areas and All Science Journal Classification Codes (ASJC)
# https://service.elsevier.com/app/answers/detail/a_id/15181/supporthub/scopus/
asjc_import_table = TableMeta(
    "asjc_import",
    cursor_class=CsvCursor,
    delimiter=";",
    columns=[
        ColumnMeta("id"),
        ColumnMeta("code"),
        ColumnMeta("field"),
        ColumnMeta("subject_area"),
    ],
    post_population_script="sql/normalize-asjc.sql",
)

asjcs_table = TableMeta(
    "asjcs",
    columns=[
        ColumnMeta("id"),
        ColumnMeta("field"),
        ColumnMeta("subject_area_id"),
        ColumnMeta("general_field_id"),
    ],
    post_population_script="sql/normalize-asjc.sql",
)

asjc_general_fields_table = TableMeta(
    "asjc_general_fields",
    columns=[
        ColumnMeta("id"),
        ColumnMeta("name"),
    ],
)

asjc_subject_areas_table = TableMeta(
    "asjc_subject_areas",
    columns=[
        ColumnMeta("id"),
        ColumnMeta("name"),
    ],
)


tables = [
    asjc_import_table,
    asjc_general_fields_table,
    asjc_subject_areas_table,
    asjcs_table,
]


class Asjcs(DataSource):
    """
    Create an ASJC meta-data object that supports queries over
    its (virtual) table and the population of an SQLite database with its
    data.

    :param data_source: The source where the ASJC data are located
    :type data_source: str
    """

    def __init__(
        self,
        data_source,
        sample=lambda n: True,
        attach_databases=None,
    ):
        super().__init__(
            VTSource(asjc_import_table, data_source, sample),
            [asjc_import_table],
            attach_databases,
        )
