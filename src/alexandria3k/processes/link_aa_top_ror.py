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
"""Link author affiliation with top-level research organization"""

from alexandria3k.processes import link_aa_base_ror

tables = link_aa_base_ror.tables


def process(database_path):
    """
    Process the specified database creating a table that links Crossref work
    authors to their corresponding research organization as codified in the
    Research Orgnization Registry (ROR).
    The link is made to the top organizational level corresponding to the
    identified organization, e.g. the hospital, university, or research
    center associated with an author's clinic, school, or institute.

    :param database_path: The path specifying the SQLite database
        to process and populate.
    :type database_path: str
    """
    link_aa_base_ror.link_author_affiliations(database_path, link_to_top=True)
