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
"""Patent grant bibliographic (front page) text data (JAN 1976 - present)"""

from alexandria3k.db_schema import ColumnMeta, TableMeta

# Bulk data can be found here. https://bulkdata.uspto.gov
# Patent Grant Bibliographic (Front Page) Text Data (JAN 1976 - PRESENT)
DEFAULT_SOURCE = None


# Dataset Description — Patent grant full-text data (no images)
# JAN 1976 — present Automated Patent System (APS)
# Contains the full text of each patent grant issued weekly
# Tuesdays from January 1, 1976, to present excludes images/drawings and reexaminations.
# https://developer.uspto.gov/product/patent-grant-bibliographic-dataxml

tables = [
    TableMeta(
        "us_patents",
        # cursor_class=PatentCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("language", description="Fixed EN for publishing."),
            ColumnMeta("status", description="Not used for publishing."),
            ColumnMeta("country", description="Fixed US."),
            ColumnMeta(
                "filename",
                description="Filename for the specific date.",
            ),
            ColumnMeta("date_produced"),
            ColumnMeta("date_published"),
            ColumnMeta("type"),
            ColumnMeta("series_code"),
            ColumnMeta("invention_title"),
            ColumnMeta("botanic_name"),
            ColumnMeta("botanic_variety"),
            ColumnMeta("claims_number"),
            ColumnMeta(
                "figures_number",
                description="Excluded element figures-to-publish.",
            ),
            ColumnMeta("drawings_number"),
            ColumnMeta(
                "microform_number", description="Optical microform appendix."
            ),
            ColumnMeta("primary_examiner_firstname"),
            ColumnMeta("primary_examiner_lastname"),
            ColumnMeta("assistant_examiner_firstname"),
            ColumnMeta("assistant_examiner_lastname"),
            ColumnMeta("authorized_officer_firstname"),
            ColumnMeta("authorized_officer_lastname"),
            ColumnMeta("hague_filing_date"),
            ColumnMeta("hague_reg_pub_date"),
            ColumnMeta("hague_reg_date"),
            ColumnMeta("hague_reg_num"),
            ColumnMeta(
                "sir_flag",
                description="Statutory invention registration flag.",
            ),
            ColumnMeta(
                "cpa_flag",
                description="Continued prosecution application flag.",
            ),
            ColumnMeta(
                "rule47_flag",
                description="Refused to execute the application.",
            ),
        ],
    )
]
