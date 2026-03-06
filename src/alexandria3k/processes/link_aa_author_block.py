#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2022-2026  Diomidis Spinellis
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
"""Author blocking for disambiguation based on first name initial and family name."""


import unicodedata
import re
from alexandria3k import perf
from alexandria3k.common import ensure_table_exists
import apsw

def make_blocking_key(given: str | None, family: str | None):
    """
    Return a blocking key for an author based on their first name
    initial and normalized family name.
    Returns None if family name is missing.
    """
    # Skip if family name is missing
    if not family:
        return None

    # Normalize family name: lowercase, strip diacritics, strip punctuation
    family_normalized = unicodedata.normalize("NFD", family.lower())
    family_normalized = "".join(
        c for c in family_normalized
        if unicodedata.category(c) != "Mn"
    )
    family_normalized = family_normalized.replace("-", " ")
    family_normalized = re.sub(r"[^\w\s]", "", family_normalized)
    family_normalized = family_normalized.strip()

    # If given name is missing, use family name alone
    if not given:
        return family_normalized

    # Normalize given name and extract first alphabetic character
    given_normalized = unicodedata.normalize("NFD", given.lower())
    initial = next(
        (c for c in given_normalized if c.isalpha()), None
    )

    if not initial:
        return family_normalized

    return f"{initial}.{family_normalized}"

def blocking(database_path: str):
    """
    Build blocking dictionary from work_authors table.
    Returns a dictionary mapping blocking keys to lists of
    (author_id, work_id) paper-level mentions.
    """
    database = apsw.Connection(database_path)
    ensure_table_exists(database, "work_authors")
    select_cursor = database.cursor()

    blocks = {}
    for author_id, given, family, work_id in select_cursor.execute(
        "SELECT id, given, family, work_id FROM work_authors"
    ):
        key = make_blocking_key(given, family)
        if key is None:
            continue
        if key not in blocks:
            blocks[key] = []
        blocks[key].append((author_id, work_id))

    select_cursor.close()
    perf.log(f"blocking built {len(blocks)} blocks")
    return blocks

def process(database_path: str):
    """
    Process the specified database building author blocks
    for disambiguation.
    """
    return blocking(database_path)
