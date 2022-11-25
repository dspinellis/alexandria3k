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

# Based on Kahn's algorithm;
# see https://en.wikipedia.org/wiki/Topological_sorting
#
# L ← Empty list that will contain the sorted elements
# S ← Set of all nodes with no incoming edge
#
# while S is not empty do
#     remove a node n from S
#     add n to L
#     for each node m with an edge e from n to m do
#         remove edge e from the graph
#         if m has no other incoming edges then
#             insert m into S
#
# if graph has edges then
#     return error   (graph has at least one cycle)
# else
#     return L   (a topologically sorted order)


def tsort(tables_meta, table_names):
    """Return the passed iterable of table names topologically sorted
    based on their dependencies, available through tables_meta."""
    result = []
    # Nodes with no parent
    todo = {
        t.get_name()
        for t in tables_meta
        if t.get_parent_name() not in table_names
    }
    while todo:
        current = todo.pop()
        result.append(current)
        # Now that we have added "current" we can process all of its children
        for table in tables_meta:
            parent = table.get_parent_name()
            if parent == current:
                todo.add(table.get_name())
    return result
