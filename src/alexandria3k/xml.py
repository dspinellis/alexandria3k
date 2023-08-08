#
# Alexandria3k Patent grant bibliographic metadata processing
# Copyright (C) 2023  Aggelos Margkas
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
"""XML helper functions"""

# In all cases the variable tree represents an object of the
# module xml.etree.ElementTree used for parsing and
# creating XML data. For more information check:
# https://docs.python.org/3/library/xml.etree.elementtree.html


def get_element(tree, path):
    """Return the text value of the specified element path of the given
    tree."""
    element = tree.find(path)
    if element is None:
        return None
    return element.text


def get_attribute(tree, attr, path=None):
    """Return the value of the specified attribute. If no path is
    given searches on root, if specified searches on the specified
    element."""

    if path:
        element = tree.find(path)
        return element.get(attr) if element is not None else None
    return tree.get(attr) if tree.get(attr) is not None else None


def getter(path):
    """Return a function to return an element with the specified
    path from a given tree."""
    return lambda tree: get_element(tree, path)


def agetter(attr_name, path=None):
    """Return a function to return an attribute with the specified
    name."""
    return lambda tree: get_attribute(tree, attr_name, path)


def all_getter(path):
    """Return all elements from the specified path"""
    return lambda tree: tree.findall(path)
