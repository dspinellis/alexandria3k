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
"""Topological sort of database tables"""

import crossref


def tsort(table_names):
    """Return the passed iterable of table names topologically sorted
    based on their dependencies"""
    tables = [crossref.get_table_meta_by_name(t) for t in table_names]
    result = []
    todo = {"works"}
    while todo:
        current = todo.pop()
        result.append(current)
        for table in tables:
            parent = table.get_parent_name()
            if parent == current:
                todo.add(table.get_name())
    return result
