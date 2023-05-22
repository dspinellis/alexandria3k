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
"""Virtual database table access of US Patent Bibliographic data"""

import abc
import csv
import os
import sqlite3

# pylint: disable-next=import-error
import apsw

from alexandria3k.common import add_columns, fail, log_sql, set_fast_writing
from alexandria3k import debug
from alexandria3k import perf
from alexandria3k.tsort import tsort
from alexandria3k.virtual_db import (
    ColumnMeta,
    TableMeta,
    CONTAINER_ID_COLUMN,
    FilesCursor,
    ROWID_INDEX,
)
