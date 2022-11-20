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
"""Populate journal, funder, OA data tables"""

import codecs
import csv
import re
import sqlite3
from urllib.request import urlopen

from virtual_db import ColumnMeta, TableMeta

RE_URL = re.compile(r"\w+://")


def data_source(source):
    """Given a file path or a URL return a readable source for its contents"""
    if RE_URL.match(source):
        print("READ URL")
        return urlopen(source)
    else:
        return open(source, "rb")


def record_source(source):
    """Given a file path or a URL return a record source for its contents"""
    with data_source(source) as raw_input:
        reader = csv.reader(codecs.iterdecode(raw_input, "utf-8"))
        next(reader, None)  # Skip header row
        for i in reader:
            yield i


journals_table = TableMeta(
    "journal_data",
    columns=[
        ColumnMeta("title"),
        ColumnMeta("id"),
        ColumnMeta("publisher"),
        ColumnMeta("issn_print"),
        ColumnMeta("issn_eprint"),
        ColumnMeta("issns_additional"),
        ColumnMeta("doi"),
        ColumnMeta("volume_info"),
    ],
)


def load_csv_data(database_path, table_meta, source):
    """Populate specified table of database with data from source"""
    con = sqlite3.connect(database_path)
    cur = con.cursor()
    cur.execute(f"DROP TABLE IF EXISTS {table_meta.get_name()}")
    cur.execute(table_meta.table_schema())
    print(table_meta.insert_statement())
    cur.executemany(table_meta.insert_statement(), record_source(source))
    con.commit()
    con.close()
