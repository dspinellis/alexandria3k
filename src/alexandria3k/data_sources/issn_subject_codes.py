#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2024  Panagiotis-Alexios Spanakis
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
"""ISSN Subject Codes data processing

Requests per second allowed: 9 (https://dev.elsevier.com/api_key_settings.html)
Total requests allowed: 25000 per week (https://dev.elsevier.com/api_key_settings.html)
"""

import csv
import os
import sqlite3

import pybliometrics
from pybliometrics.scopus import SerialSearch

from alexandria3k.csv_source import CsvCursor, VTSource
from alexandria3k.data_source import DataSource
from alexandria3k.db_schema import ColumnMeta, TableMeta
from alexandria3k import perf, debug
from alexandria3k.common import ensure_table_exists, get_string_resource
from alexandria3k.common import Alexandria3kError
from alexandria3k.data_source import FilesCursor
from alexandria3k.common import warn

issn_subject_codes_table = TableMeta(
    "issn_subject_codes",
    cursor_class=CsvCursor,
    delimiter=",",
    columns=[
        ColumnMeta("id", rowid=True),
        ColumnMeta("issn"),
        ColumnMeta("subject_code", data_type="INTEGER"),
    ],
)

tables = [
    issn_subject_codes_table,
]

DEFAULT_SOURCE = None


class IssnSubjectCodes(DataSource):
    """
    Create an object containing ISSN to ASJC meta-data that supports queries over
    its (virtual) table and the population of an SQLite database with its
    data.

    :param data_source: The location (file path) where the data
      are to be stored (for download) or loaded from (for populate or query).
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
        data_source=None,
        sample=lambda n: True,
        attach_databases=None,
        config_path=None,
    ):
        # Check if the environment variable is set or not
        if "PYBLIOMETRICS_CONFIG_FILE" not in os.environ:

            def get_config_path(config_path):
                if config_path:
                    return config_path
                config_path = os.path.expanduser("~/.config/pybliometrics.cfg")
                debug.log("config-file", f"Using config file at {config_path}")
                return config_path

            # Set the configuration file path
            config_path = get_config_path(config_path)
            os.environ["PYBLIOMETRICS_CONFIG_FILE"] = config_path

        self.sample = sample
        super().__init__(
            VTSource(issn_subject_codes_table, data_source, sample),
            [issn_subject_codes_table],
            attach_databases,
        )

    def execute_sql_query(self, cursor, script):
        """Execute the specified SQL query and return the results."""
        cursor.execute(script)
        issns = [row[0] for row in cursor.fetchall()]
        return issns

    def fetch_subject_codes(self, writer, issns):
        """Fetch the subject codes for the specified ISSNs."""
        total_issns = len(issns)
        for index, issn in enumerate(issns):
            FilesCursor.debug_progress_bar(
                self, current_progress=index + 1, total_length=total_issns
            )
            query = {"issn": issn}
            try:
                serial_search = SerialSearch(query=query, view="STANDARD")
                results = list(serial_search.results)

                for result in results:
                    for code in (result.get("subject_area_codes")).split(";"):
                        writer.writerow([issn, code])

            except (KeyError, ValueError):
                warn(f"Error processing ISSN {issn}")

    def download(self, data_location, database=None, sql_query=None):
        """
        Create a CSV file with ISSNs and their corresponding ASJC subject codes from API calls
        using the Scopus API.

        :param data_location: The path specifying the CSV file where
        the downloaded data will be stored.
        :type data_location: str

        :param database: The path specifying the SQLite database to use
         in order to fetch the ISSNs.
        :type database: str

        :param sql_query: The SQL query that will supply the ISSNs to fetch,
        from the database specified, where the ISSNs are
        formatted as 8 alphanumeric characters
        (.e.g 2249782X) without any spaces or dashes., defaults to `None`.
        The default query fetches all unique ISSNs from the specified
        database's `works` table where
        we use `COALESCE(issn_print, issn_electronic)`.
        The query should return a single column with the name `issn`.
        :type sql_query: str, optional
        """
        try:
            pybliometrics.scopus.init()
        except RuntimeError as e:
            raise Alexandria3kError(
                "Error in downloading data with pybliometrics"
            ) from e
        connection = sqlite3.connect(database)
        ensure_table_exists(connection, "works")
        cursor = connection.cursor()
        script = sql_query or get_string_resource("sql/get-issns.sql")
        # Use generator to apply the sample callable while fetching the results
        issns = [
            issn
            for issn in self.execute_sql_query(cursor, script)
            if self.sample(issn)
        ]

        with open(
            data_location, mode="w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.writer(file)
            writer.writerow(["issn", "subject_code"])
            self.fetch_subject_codes(writer, issns)

        connection.close()
        perf.log("create_csv_from_api")
