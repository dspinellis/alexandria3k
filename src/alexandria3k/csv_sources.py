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


# Crossref journal data http://ftp.crossref.org/titlelist/titleFile.csv
journals_table = TableMeta(
    "journal_names",
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

# Crossref funder data https://doi.crossref.org/funderNames?mode=list
# https://www.crossref.org/services/funder-registry/
funders_table = TableMeta(
    "funder_names",
    columns=[
        ColumnMeta("url"),
        ColumnMeta("name"),
        ColumnMeta("replaced"),
    ],
)

# DOAJ open access journal metadata data
# https://doaj.org/csv
open_access_table = TableMeta(
    "open_access_journals",
    columns=[
        ColumnMeta("name", help="Journal title"),
        ColumnMeta("url", help="Journal URL"),
        ColumnMeta("doaj_ur", help="URL in DOAJ"),
        ColumnMeta(
            "oaj_start",
            help="When did the journal start to publish all content using an open license?",
        ),
        ColumnMeta("alternative_name", help="Alternative title"),
        ColumnMeta("issn_print", help="Journal ISSN (print version)"),
        ColumnMeta("issn_eprint", help="Journal EISSN (online version)"),
        ColumnMeta("keywords", help="Keywords"),
        ColumnMeta(
            "languages",
            help="Languages in which the journal accepts manuscripts",
        ),
        ColumnMeta("publisher", help="Publisher"),
        ColumnMeta("pubisher_country", help="Country of publisher"),
        ColumnMeta("society", help="Society or institution"),
        ColumnMeta(
            "society_country", help="Country of society or institution"
        ),
        ColumnMeta("license", help="Journal license"),
        ColumnMeta("license_attributes", help="License attributes"),
        ColumnMeta("license_terms_url", help="URL for license terms"),
        ColumnMeta(
            "license_embedded",
            help="Machine-readable CC licensing information embedded or displayed in articles",
        ),
        ColumnMeta(
            "example_license_embedded_url",
            help="URL to an example page with embedded licensing information",
        ),
        ColumnMeta(
            "author_copyright",
            help="Author holds copyright without restrictions",
        ),
        ColumnMeta("copyright_info_url", help="Copyright information URL"),
        ColumnMeta("review_process", help="Review process"),
        ColumnMeta(
            "review_process_url", help="Review process information URL"
        ),
        ColumnMeta(
            "plagiarism_screening", help="Journal plagiarism screening policy"
        ),
        ColumnMeta("plagiarism_info_url", help="Plagiarism information URL"),
        ColumnMeta("aims_scope_url", help="URL for journal's aims & scope"),
        ColumnMeta("board_url", help="URL for the Editorial Board page"),
        ColumnMeta(
            "author_instructions_url",
            help="URL for journal's instructions for authors",
        ),
        ColumnMeta(
            "sub_pub_weeks",
            help="Average number of weeks between article submission and publication",
        ),
        ColumnMeta("apc", help="APC"),
        ColumnMeta("apc_info_url", help="APC information URL"),
        ColumnMeta("apc_amount", help="APC amount"),
        ColumnMeta(
            "apc_waiver",
            help="Journal waiver policy (for developing country authors etc)",
        ),
        ColumnMeta(
            "apc_waiver_info_url", help="Waiver policy information URL"
        ),
        ColumnMeta("other_fees", help="Has other fees"),
        ColumnMeta("other_fees_info_url", help="Other fees information URL"),
        ColumnMeta("preservation_services", help="Preservation Services"),
        ColumnMeta(
            "preservation_national_library",
            help="Preservation Service: national library",
        ),
        ColumnMeta(
            "preservation_info_url", help="Preservation information URL"
        ),
        ColumnMeta(
            "deposit_policy_directory", help="Deposit policy directory"
        ),
        ColumnMeta(
            "deposit_policy_directory_url", help="URL for deposit policy"
        ),
        ColumnMeta(
            "persistent_article_identifiers",
            help="Persistent article identifiers",
        ),
        ColumnMeta(
            "orcid_in_metadata", help="Article metadata includes ORCIDs"
        ),
        ColumnMeta(
            "i4oc_compliance",
            help="Journal complies with I4OC standards for open citations",
        ),
        ColumnMeta(
            "doaj_oa_compliance",
            help="Does the journal comply to DOAJ's definition of open access?",
        ),
        ColumnMeta(
            "oa_statement_url", help="URL for journal's Open Access statement"
        ),
        ColumnMeta("continues", help="Continues"),
        ColumnMeta("continued_by", help="Continued By"),
        ColumnMeta("lcc_codes", help="LCC Codes"),
        ColumnMeta("subjects", help="Subjects"),
        ColumnMeta("doaj_Seal", help="DOAJ Seal"),
        ColumnMeta("added_on", help="Added on Date"),
        ColumnMeta("last_updated", help="Last updated Date"),
        ColumnMeta("article_records_number", help="Number of Article Records"),
        ColumnMeta("most_recent_addition", help="Most Recent Article Added"),
    ],
)


def load_csv_data(database_path, table_meta, source):
    """Populate specified table of database with data from source"""
    con = sqlite3.connect(database_path)
    cur = con.cursor()
    cur.execute(f"DROP TABLE IF EXISTS {table_meta.get_name()}")
    cur.execute(table_meta.table_schema())
    cur.executemany(table_meta.insert_statement(), record_source(source))
    con.commit()
    con.close()
