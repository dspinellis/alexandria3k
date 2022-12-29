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
"""Populate ORCID data tables"""

import tarfile
import xml.etree.ElementTree as ET

# pylint: disable-next=import-error
import apsw

from .common import add_columns, fail, log_sql, set_fast_writing
from . import perf
from .virtual_db import ColumnMeta, TableFiller, TableMeta

# The ORCID XML namespaces in XPath format
ACTIVITIES = "{http://www.orcid.org/ns/activities}"
ADDRESS = "{http://www.orcid.org/ns/address}"
BULK = "{http://www.orcid.org/ns/bulk}"
COMMON = "{http://www.orcid.org/ns/common}"
DEPRECATED = "{http://www.orcid.org/ns/deprecated}"
DISTINCTION = "{http://www.orcid.org/ns/distinction}"
EDUCATION = "{http://www.orcid.org/ns/education}"
EMAIL = "{http://www.orcid.org/ns/email}"
EMPLOYMENT = "{http://www.orcid.org/ns/employment}"
ERROR = "{http://www.orcid.org/ns/error}"
EXTERNAL_IDENTIFIER = "{http://www.orcid.org/ns/external-identifier}"
FUNDING = "{http://www.orcid.org/ns/funding}"
HISTORY = "{http://www.orcid.org/ns/history}"
INTERNAL = "{http://www.orcid.org/ns/internal}"
INVITED_POSITION = "{http://www.orcid.org/ns/invited-position}"
KEYWORD = "{http://www.orcid.org/ns/keyword}"
MEMBERSHIP = "{http://www.orcid.org/ns/membership}"
OTHER_NAME = "{http://www.orcid.org/ns/other-name}"
PEER_REVIEW = "{http://www.orcid.org/ns/peer-review}"
PERSON = "{http://www.orcid.org/ns/person}"
PERSONAL_DETAILS = "{http://www.orcid.org/ns/personal-details}"
PREFERENCES = "{http://www.orcid.org/ns/preferences}"
QUALIFICATION = "{http://www.orcid.org/ns/qualification}"
RECORD = "{http://www.orcid.org/ns/record}"
RESEARCHER_URL = "{http://www.orcid.org/ns/researcher-url}"
RESEARCH_RESOURCE = "{http://www.orcid.org/ns/research-resource}"
SERVICE = "{http://www.orcid.org/ns/service}"
WORK = "{http://www.orcid.org/ns/work}"


def get_element(tree, path):
    """Return the text value of the specified element path of the given
    tree."""
    element = tree.find(path)
    if element is None:
        return None
    return element.text


def getter(path):
    """Return a function to return an element with the specified
    path from a given tree."""
    return lambda tree: get_element(tree, path)


def get_type_element_lower(tree, path, id_type):
    """Return the text value of <common:external-id-value> in the
    specified element path of the given tree if <common:external-id-type>
    is the specified id_type or None."""
    element = tree.find(path)
    if element is None:
        return None
    found_type = get_element(element, f"{COMMON}external-id-type")
    if found_type is None or found_type != id_type:
        return None

    return get_element(element, f"{COMMON}external-id-value").lower()


def type_getter_lower(path, id_type):
    """Return a function to return an element converted to lowercase
    with the specified path and <common:external-id-type> from a given tree."""
    return lambda tree: get_type_element_lower(tree, path, id_type)


def all_getter(path):
    """Return all elements from the specified path"""
    return lambda tree: tree.findall(path)


# Map from XML to relational schema
# The XML schema is described in
# https://info.orcid.org/documentation/integration-guide/orcid-record/#Research_Resources
# https://github.com/ORCID/orcid-model/blob/master/src/main/resources/record_3.0/README.md

START_END_DATE = [
    ColumnMeta("start_year", getter(f"{COMMON}start-date/{COMMON}year")),
    ColumnMeta("start_month", getter(f"{COMMON}start-date/{COMMON}month")),
    ColumnMeta("start_day", getter(f"{COMMON}start-date/{COMMON}day")),
    ColumnMeta("end_year", getter(f"{COMMON}end-date/{COMMON}year")),
    ColumnMeta("end_month", getter(f"{COMMON}end-date/{COMMON}month")),
    ColumnMeta("end_day", getter(f"{COMMON}end-date/{COMMON}day")),
]

ORGANIZATION = [
    ColumnMeta(
        "organization_name", getter(f"{COMMON}organization/{COMMON}name")
    ),
    ColumnMeta(
        "organization_city",
        getter(f"{COMMON}organization/{COMMON}address/{COMMON}city"),
    ),
    ColumnMeta(
        "organization_region",
        getter(f"{COMMON}organization/{COMMON}address/{COMMON}region"),
    ),
    ColumnMeta(
        "organization_country",
        getter(f"{COMMON}organization/{COMMON}address/{COMMON}country"),
    ),
    ColumnMeta(
        "organization_identifier",
        getter(
            f"{COMMON}organization/{COMMON}disambiguated-organization/"
            f"{COMMON}disambiguated-organization-identifier"
        ),
    ),
]

DEPARTMENT_NAME_ROLE = [
    ColumnMeta("department_name", getter(f"{COMMON}department-name")),
    ColumnMeta("role_title", getter(f"{COMMON}role-title")),
]

AFFILIATION = ORGANIZATION + DEPARTMENT_NAME_ROLE + START_END_DATE

tables = [
    TableMeta(
        "persons",
        columns=[
            ColumnMeta("id", rowid=True),
            ColumnMeta(
                "orcid", getter(f"{COMMON}orcid-identifier/{COMMON}path")
            ),
            ColumnMeta(
                "given_names",
                getter(
                    f"{PERSON}person/{PERSON}name/{PERSONAL_DETAILS}given-names"
                ),
            ),
            ColumnMeta(
                "family_name",
                getter(
                    f"{PERSON}person/{PERSON}name/{PERSONAL_DETAILS}family-name"
                ),
            ),
            ColumnMeta(
                "biography",
                getter(
                    f"{PERSON}person/{PERSON}biography/{PERSONAL_DETAILS}content"
                ),
            ),
        ],
    ),
    TableMeta(
        "person_researcher_urls",
        extract_multiple=all_getter(
            f"{PERSON}person/{RESEARCHER_URL}researcher-urls/"
            f"{RESEARCHER_URL}researcher-url"
        ),
        columns=[
            ColumnMeta("person_id"),
            ColumnMeta("name", getter(f"{RESEARCHER_URL}url-name")),
            ColumnMeta("url", getter(f"{RESEARCHER_URL}url")),
        ],
    ),
    TableMeta(
        "person_countries",
        extract_multiple=all_getter(
            f"{PERSON}person/{ADDRESS}addresses/{ADDRESS}address"
        ),
        columns=[
            ColumnMeta("person_id"),
            ColumnMeta("country", getter(f"{ADDRESS}country")),
        ],
    ),
    TableMeta(
        "person_keywords",
        extract_multiple=all_getter(
            f"{PERSON}person/{KEYWORD}keywords/{KEYWORD}keyword"
        ),
        columns=[
            ColumnMeta("person_id"),
            ColumnMeta("keyword", getter(f"{KEYWORD}content")),
        ],
    ),
    TableMeta(
        "person_external_identifiers",
        extract_multiple=all_getter(
            f"{PERSON}person/{EXTERNAL_IDENTIFIER}external-identifiers/"
            f"{EXTERNAL_IDENTIFIER}external-identifier"
        ),
        columns=[
            ColumnMeta("person_id"),
            ColumnMeta("type", getter(f"{COMMON}external-id-type")),
            ColumnMeta("value", getter(f"{COMMON}external-id-value")),
            ColumnMeta("url", getter(f"{COMMON}external-id-url")),
        ],
    ),
    TableMeta(
        "person_distinctions",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/{ACTIVITIES}distinctions/"
            f"{ACTIVITIES}affiliation-group/{DISTINCTION}distinction-summary"
        ),
        columns=[
            ColumnMeta("person_id"),
        ]
        + AFFILIATION,
    ),
    TableMeta(
        "person_educations",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/{ACTIVITIES}educations/"
            f"{ACTIVITIES}affiliation-group/{EDUCATION}education-summary"
        ),
        columns=[
            ColumnMeta("person_id"),
        ]
        + AFFILIATION,
    ),
    TableMeta(
        "person_employments",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/{ACTIVITIES}employments/"
            f"{ACTIVITIES}affiliation-group/{EMPLOYMENT}employment-summary"
        ),
        columns=[
            ColumnMeta("person_id"),
        ]
        + AFFILIATION,
    ),
    TableMeta(
        "person_invited_positions",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/"
            f"{ACTIVITIES}invited-positions/"
            f"{ACTIVITIES}affiliation-group/"
            f"{INVITED_POSITION}invited-position-summary"
        ),
        columns=[
            ColumnMeta("person_id"),
        ]
        + AFFILIATION,
    ),
    TableMeta(
        "person_memberships",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/"
            f"{ACTIVITIES}memberships/{ACTIVITIES}affiliation-group/"
            f"{MEMBERSHIP}membership-summary"
        ),
        columns=[
            ColumnMeta("person_id"),
        ]
        + AFFILIATION,
    ),
    TableMeta(
        "person_qualifications",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/"
            f"{ACTIVITIES}qualifications/"
            f"{ACTIVITIES}affiliation-group/"
            f"{QUALIFICATION}qualification-summary"
        ),
        columns=[
            ColumnMeta("person_id"),
        ]
        + AFFILIATION,
    ),
    TableMeta(
        "person_services",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/{ACTIVITIES}services/"
            f"{ACTIVITIES}affiliation-group/{SERVICE}service-summary"
        ),
        columns=[
            ColumnMeta("person_id"),
        ]
        + AFFILIATION,
    ),
    TableMeta(
        "person_fundings",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/{ACTIVITIES}fundings/"
            f"{ACTIVITIES}group/{FUNDING}funding-summary"
        ),
        # pylint: disable-next=fixme
        # TODO external-ids, contributors
        columns=[
            ColumnMeta("person_id"),
            ColumnMeta("title", getter(f"{FUNDING}funding-title")),
            ColumnMeta("type", getter(f"{FUNDING}funding-type")),
            ColumnMeta(
                "short_description", getter(f"{COMMON}short-description")
            ),
            ColumnMeta("amount", getter(f"{COMMON}amount")),
            ColumnMeta("url", getter(f"{COMMON}url")),
        ]
        + START_END_DATE
        + ORGANIZATION,
    ),
    TableMeta(
        "person_peer_reviews",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/"
            f"{ACTIVITIES}peer-reviews/{ACTIVITIES}group/"
            f"{ACTIVITIES}peer-review-group/"
            f"{PEER_REVIEW}peer-review-summary"
        ),
        columns=[
            ColumnMeta("person_id"),
            ColumnMeta("reviewer_role", getter(f"{PEER_REVIEW}reviewer-role")),
            ColumnMeta("review_type", getter(f"{PEER_REVIEW}review-type")),
            ColumnMeta("subject_type", getter(f"{PEER_REVIEW}subject-type")),
            ColumnMeta("subject_name", getter(f"{PEER_REVIEW}subject-name")),
            ColumnMeta("subject_url", getter(f"{PEER_REVIEW}subject-url")),
            ColumnMeta("group_id", getter(f"{PEER_REVIEW}review-group-id")),
            ColumnMeta(
                "completion_year",
                getter(f"{PEER_REVIEW}completion-date/{COMMON}year"),
            ),
            ColumnMeta(
                "completion_month",
                getter(f"{PEER_REVIEW}completion-date/{COMMON}month"),
            ),
            ColumnMeta(
                "completion_day",
                getter(f"{PEER_REVIEW}completion-date/{COMMON}day"),
            ),
            ColumnMeta(
                "organization_name",
                getter(f"{PEER_REVIEW}convening-organization/{COMMON}name"),
            ),
            ColumnMeta(
                "organization_city",
                getter(
                    f"{PEER_REVIEW}convening-organization/"
                    f"{COMMON}address/{COMMON}city"
                ),
            ),
            ColumnMeta(
                "organization_region",
                getter(
                    f"{PEER_REVIEW}convening-organization/"
                    f"{COMMON}address/{COMMON}region"
                ),
            ),
            ColumnMeta(
                "organization_country",
                getter(
                    f"{PEER_REVIEW}convening-organization/"
                    f"{COMMON}address/{COMMON}country"
                ),
            ),
        ],
    ),
    TableMeta(
        "person_research_resources",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/"
            f"{ACTIVITIES}research-resources/{ACTIVITIES}group/"
            f"{RESEARCH_RESOURCE}research-resource-summary"
        ),
        columns=[
            ColumnMeta("person_id"),
            ColumnMeta(
                "title",
                getter(
                    f"{RESEARCH_RESOURCE}proposal/{RESEARCH_RESOURCE}title/"
                    f"{COMMON}title"
                ),
            ),
            ColumnMeta(
                "start_year",
                getter(
                    f"{RESEARCH_RESOURCE}proposal/{COMMON}start-date/{COMMON}year"
                ),
            ),
            ColumnMeta(
                "start_month",
                getter(
                    f"{RESEARCH_RESOURCE}proposal/{COMMON}start-date/"
                    f"{COMMON}month"
                ),
            ),
            ColumnMeta(
                "start_day",
                getter(
                    f"{RESEARCH_RESOURCE}proposal/{COMMON}start-date/{COMMON}day"
                ),
            ),
            ColumnMeta(
                "end_year",
                getter(
                    f"{RESEARCH_RESOURCE}proposal/{COMMON}end-date/{COMMON}year"
                ),
            ),
            ColumnMeta(
                "end_month",
                getter(
                    f"{RESEARCH_RESOURCE}proposal/{COMMON}end-date/{COMMON}month"
                ),
            ),
            ColumnMeta(
                "end_day",
                getter(
                    f"{RESEARCH_RESOURCE}proposal/{COMMON}end-date/{COMMON}day"
                ),
            ),
        ],
    ),
    TableMeta(
        "person_works",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/{ACTIVITIES}works/"
            f"{ACTIVITIES}group/{COMMON}external-ids"
        ),
        columns=[
            ColumnMeta("person_id"),
            ColumnMeta(
                "doi", type_getter_lower(f"{COMMON}external-id", "doi")
            ),
        ],
    ),
]

table_dict = {t.get_name(): t for t in tables}


def get_table_meta_by_name(name):
    """Return the metadata of the specified table"""
    try:
        return table_dict[name]
    except KeyError:
        fail(f"Unknown table name: '{name}'.")
        # NOTREACHED
        return None


def order_columns_by_schema(table_name, column_names):
    """Return the passed set of columns as an iterable ordered in the same
    order as that in which columns are defined in the table's schema"""
    all_columns = get_table_meta_by_name(table_name).get_columns()
    all_column_names = map(lambda c: c.get_name(), all_columns)
    result = []
    for column in all_column_names:
        if column in column_names:
            result.append(column)
    return result


def order_column_definitions_by_schema(table, column_names):
    """Return the passed set of columns as an iterable of column creation
    DDL statements, ordered in the same order as that in which columns are
    defined in the table's schema"""
    all_columns = table.get_columns()
    all_column_names = map(lambda c: c.get_name(), all_columns)
    result = []
    for column in all_column_names:
        if column in column_names:
            result.append(table.get_column_definition_by_name(column))
    return result


# pylint: disable-next=too-many-locals,too-many-branches,too-many-statements
def populate(
    data_path,
    database_path,
    columns=None,
    authors_only=False,
    works_only=False,
):
    """Populate the specified SQLite database.
    The database is created if it does not exist.
    If it exists, the populated tables are dropped
    (if they exist) and recreated anew as specified.

    columns is an array containing strings of
    table_name.column_name or table_name.*

    If authors_only is True then only ORCID records of persons that exist in the
    Crossref work_authors table will be added.

    If works_only is True then only ORCID records of persons whose works
    exist in the Crossref works table will be added.
    """

    def add_column(table, column):
        """Add a column required for executing a query to the
        specified dictionary"""
        if column == "*":
            columns = get_table_meta_by_name(table).get_columns()
            column_names = map(lambda c: c.get_name(), columns)
            population_columns[table] = set(column_names)
        elif table in population_columns:
            population_columns[table].add(column)
        else:
            population_columns[table] = {column}

    def work_dois_in_crossref():
        """
        Return True if any the work dois included under "works" in element_tree
        exist in the Crossref works table.
        """
        external_id = f"{COMMON}external-id"
        # Person's work DOIs
        work_dois = []
        for record in element_tree.findall(
            f"{ACTIVITIES}activities-summary/{ACTIVITIES}works/"
            f"{ACTIVITIES}group/{COMMON}external-ids"
        ):
            doi = get_type_element_lower(record, external_id, "doi")

            # Include only defined DOIs and DOIs not cointaining "'",
            # which would mess the generated SQL (shouldn't happen,
            # but data can always contain some garbage).
            # This also reduces the possibility of an SQLIA; not a big
            # concern in the context of this application.
            if doi and doi.find("'") == -1:
                work_dois.append(f"'{doi}'")

        if not work_dois:
            return False
        doi_set = ",".join(work_dois)
        # print(doi_set)

        # For many DOIs SQLite executes OpenEphemeral and then a series of
        # IdxInsert, which suggests it is optizing the search for all of
        # them by creating a temporary index
        cursor.execute(
            log_sql(
                f"""
                SELECT 1 WHERE EXISTS (
                    SELECT 1 FROM works WHERE doi IN ({doi_set})
                )
            """
            ),
        )
        return cursor.fetchone()

    population_columns = {}
    add_columns(columns, tables, add_column)

    # Reorder columns to match the defined schema order
    # This creates schemas with a deterministic column order
    for (table_name, table_columns) in population_columns.items():
        population_columns[table_name] = order_columns_by_schema(
            table_name, population_columns[table_name]
        )

    # Create empty tables and their TableFiller objects
    database = apsw.Connection(database_path)
    set_fast_writing(database)
    cursor = database.cursor()
    table_fillers = []
    for (table_name, table_columns) in population_columns.items():
        # Table creation
        table = get_table_meta_by_name(table_name)
        cursor.execute(log_sql(f"DROP TABLE IF EXISTS {table_name}"))
        column_definitions = order_column_definitions_by_schema(
            table, table_columns
        )
        cursor.execute(log_sql(table.table_schema("", column_definitions)))

        # Value addition
        is_master = table_name == "persons"
        filler = TableFiller(database, table, table_columns, is_master)
        table_fillers.append(filler)

    if authors_only:
        cursor.execute(
            log_sql(
                """
            CREATE INDEX IF NOT EXISTS work_authors_orcid_idx
                ON work_authors(orcid)
        """
            )
        )
    # Streaming read from compressed file
    with tarfile.open(data_path, "r|gz") as tar:
        for tar_info in tar:
            if not tar_info.isreg():
                continue

            # Obtain ORCID from file name to avoid extraction and parsing
            (_root, _checksum, file_name) = tar_info.name.split("/")
            orcid = file_name[:-4]

            # Skip records of non-linked authors
            if authors_only:
                cursor.execute(
                    log_sql(
                        """
                        SELECT 1 WHERE EXISTS (
                            SELECT 1 FROM work_authors WHERE orcid = ?
                        )
                    """
                    ),
                    (orcid,),
                )
                if not cursor.fetchone():
                    continue

            # Extract and parse XML data
            reader = tar.extractfile(tar_info)
            data = reader.read()
            element_tree = ET.fromstring(data)
            orcid_xml = element_tree.find(
                f"{COMMON}orcid-identifier/{COMMON}path"
            )
            # Skip error records
            if orcid_xml is None:
                continue

            assert orcid == orcid_xml.text

            perf.log(f"Parse {orcid}")

            if works_only and not work_dois_in_crossref():
                continue

            # Insert data to the specified tables
            person_id = None
            for filler in table_fillers:
                if filler.get_table_name() == "persons":
                    person_id = filler.add_records(
                        element_tree, "person_id", person_id
                    )
                else:
                    filler.add_records(element_tree, "person_id", person_id)
            perf.log(f"Populate {orcid}")

    for table_name in population_columns:
        if table_name != "persons":
            cursor.execute(
                f"""CREATE INDEX {table_name}_person_id_idx
                    ON {table_name}(person_id)"""
            )
    cursor.execute("CREATE INDEX persons_orcid_idx ON persons(orcid)")
