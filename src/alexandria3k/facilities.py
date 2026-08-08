#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2025 Panagiotis-Alexios Spanakis
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
"""Utilities for discovering available facilities (data sources, processes).

Separated out to avoid cyclic imports between the CLI (``__main__``) and
completion support. Only lightweight filesystem inspection lives here.
"""

from __future__ import annotations

import os
from typing import List


def facility_modules(facility: str) -> List[str]:
    """Return a list with the module names of the available *facility*.

    Examples: facility='data_sources' or 'processes'.
    """
    main_dir = os.path.dirname(os.path.realpath(__file__))
    python_files = os.listdir(f"{main_dir}/{facility}")
    return [os.path.splitext(f)[0] for f in python_files if f.endswith(".py")]


def facility_names(facility: str) -> List[str]:
    """Return user-visible facility names by converting underscores to dashes."""
    return [s.replace("_", "-") for s in facility_modules(facility)]


__all__ = ["facility_modules", "facility_names"]
