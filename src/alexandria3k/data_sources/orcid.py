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
"""Open Researcher and Contributor ID (ORCID) data"""

import tarfile
import xml.etree.ElementTree as ET

from alexandria3k.common import (
    Alexandria3kError,
    Alexandria3kInternalError,
    warn,
)
from alexandria3k.data_source import (
    CONTAINER_INDEX,
    DataSource,
    ElementsCursor,
    StreamingCachedContainerTable,
)
from alexandria3k import perf
from alexandria3k.xml import get_element, getter, all_getter
from alexandria3k.db_schema import ColumnMeta, TableMeta

# pylint: disable=R0801

DEFAULT_SOURCE = None


# pylint: disable-next=too-many-instance-attributes
class PersonsCursor:
    """A virtual table cursor over persons data.
    Each person corresponds to a single XML file.
    If it is used through data_source partitioned data access
    within the context of a TarFiles iterator,
    it shall return the single element of the TarFiles iterator.
    Otherwise it shall iterate over all elements."""

    def __init__(self, table):
        """Not part of the apsw VTCursor interface.
        The table argument is a StreamingTable object"""
        self.table = table
        self.data_source = table.get_data_source()
        # Initialized in Filter()
        self.eof = False
        self.item_index = -1
        self.single_file = None
        self.file_read = None
        self.iterator = None
        # Set in Next
        self.file_id = None

    def Eof(self):
        """Return True when the end of the table's records has been reached."""
        return self.eof

    def container_id(self):
        """Return the id of the container containing the data being fetched.
        Not part of the apsw API."""
        return self.data_source.get_container_id()

    def Rowid(self):
        """Return a unique id of the row along all records"""
        return self.item_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        # print(f"Column {col}")
        if col == -1:
            return self.Rowid()

        if col == 0:  # id
            return self.Rowid()

        if col == 1:
            return self.data_source.get_container_id()

        if col == 2:  # ORCID; obtain from file name; no XML parse
            return self.data_source.get_orcid()

        extract_function = self.table.get_value_extractor_by_ordinal(col)
        return extract_function(self.data_source.get_element_tree())

    def Filter(self, index_number, _index_name, constraint_args):
        """Always called first to initialize an iteration to the first row
        of the table according to the index"""
        # print(f"Filter n={index_number} c={constraint_args}")

        if index_number == 0:
            # No index; iterate through all the files
            self.item_index = -1
            self.single_file = False
            self.iterator = self.data_source.get_container_iterator()
        elif index_number & CONTAINER_INDEX:
            # Index; constraint reading through the specified file
            self.single_file = True
            self.file_read = False
            self.item_index = constraint_args[0]
        else:
            raise Alexandria3kInternalError(
                f"Unknown index ({index_number}) specified"
            )
        self.Next()  # Move to first row

    def Next(self):
        """Advance to the next item."""
        if self.single_file:
            if self.file_read or not self.table.sample(
                self.data_source.get_orcid()
            ):
                self.eof = True
            # The single file has been read. Set EOF in next Next call
            self.file_read = True
            return

        while True:  # Loop until sample returns True
            self.file_id = next(self.iterator, None)
            if self.file_id is None:
                self.eof = True
                return
            self.item_index += 1
            self.eof = False
            if self.table.sample(self.data_source.get_orcid()):
                break

    def current_row_value(self):
        """Return the current row. Not part of the apsw API."""
        return self.data_source.get_element_tree()

    def Close(self):
        """Cursor's destructor, used for cleanup"""
        if self.iterator:
            self.data_source.close()


class PersonDetailsCursor(ElementsCursor):
    """A cursor over any of a person's details data."""

    def __init__(self, table, parent_cursor):
        """Not part of the apsw VTCursor interface.
        The table argument is a StreamingTable object"""
        super().__init__(table, parent_cursor)
        self.extract_multiple = table.get_table_meta().get_extract_multiple()

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 16k elements."""
        return (self.parent_cursor.Rowid() << 14) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # id
            return self.record_id()

        if col == 2:  # person_id
            return self.parent_cursor.Rowid()

        return super().Column(col)

    def Next(self):
        """Advance reading to the next available element."""
        while True:
            if self.parent_cursor.Eof():
                self.eof = True
                return
            if not self.elements:
                self.elements = self.extract_multiple(
                    self.parent_cursor.current_row_value()
                )
                self.element_index = -1
            if not self.elements:
                self.parent_cursor.Next()
                self.elements = None
                continue
            if self.element_index + 1 < len(self.elements):
                self.element_index += 1
                self.eof = False
                return
            self.parent_cursor.Next()
            self.elements = None


class PersonWorksCursor(PersonDetailsCursor):
    """A cursor for the person's works.  It skips over works lacking a DOI."""

    def Next(self):
        """Advance reading to the next available element."""
        while True:
            if self.parent_cursor.Eof():
                self.eof = True
                return
            if not self.elements:
                self.elements = self.extract_multiple(
                    self.parent_cursor.current_row_value()
                )
                self.element_index = -1
            if not self.elements:
                self.parent_cursor.Next()
                self.elements = None
                continue
            if self.element_index + 1 < len(self.elements):
                self.element_index += 1
                tree = self.elements[self.element_index]
                # Skip over works lacking a DOI
                if not get_type_element_lower(
                    tree, f"{COMMON}external-id", "doi"
                ):
                    continue
                self.eof = False
                return
            self.parent_cursor.Next()
            self.elements = None


class PersonDetailsTableMeta(TableMeta):
    """Table metadata for person details. Objects of this
    class are injected with properties and columns common to all
    person details tables."""

    def __init__(self, name, **kwargs):
        kwargs["foreign_key"] = "person_id"
        kwargs["parent_name"] = "persons"
        kwargs["primary_key"] = "id"
        kwargs["cursor_class"] = PersonDetailsCursor
        kwargs["columns"] = [
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("person_id"),
        ] + kwargs["columns"]
        super().__init__(name, **kwargs)


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
        cursor_class=PersonsCursor,
        columns=[
            ColumnMeta("id", rowid=True),
            ColumnMeta("container_id"),
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
    PersonDetailsTableMeta(
        "person_researcher_urls",
        extract_multiple=all_getter(
            f"{PERSON}person/{RESEARCHER_URL}researcher-urls/"
            f"{RESEARCHER_URL}researcher-url"
        ),
        columns=[
            ColumnMeta("name", getter(f"{RESEARCHER_URL}url-name")),
            ColumnMeta("url", getter(f"{RESEARCHER_URL}url")),
        ],
    ),
    PersonDetailsTableMeta(
        "person_countries",
        extract_multiple=all_getter(
            f"{PERSON}person/{ADDRESS}addresses/{ADDRESS}address"
        ),
        columns=[
            ColumnMeta("country", getter(f"{ADDRESS}country")),
        ],
    ),
    PersonDetailsTableMeta(
        "person_keywords",
        extract_multiple=all_getter(
            f"{PERSON}person/{KEYWORD}keywords/{KEYWORD}keyword"
        ),
        columns=[
            ColumnMeta("keyword", getter(f"{KEYWORD}content")),
        ],
    ),
    PersonDetailsTableMeta(
        "person_external_identifiers",
        extract_multiple=all_getter(
            f"{PERSON}person/{EXTERNAL_IDENTIFIER}external-identifiers/"
            f"{EXTERNAL_IDENTIFIER}external-identifier"
        ),
        columns=[
            ColumnMeta("type", getter(f"{COMMON}external-id-type")),
            ColumnMeta("value", getter(f"{COMMON}external-id-value")),
            ColumnMeta("url", getter(f"{COMMON}external-id-url")),
        ],
    ),
    PersonDetailsTableMeta(
        "person_distinctions",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/{ACTIVITIES}distinctions/"
            f"{ACTIVITIES}affiliation-group/{DISTINCTION}distinction-summary"
        ),
        columns=[] + AFFILIATION,
    ),
    PersonDetailsTableMeta(
        "person_educations",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/{ACTIVITIES}educations/"
            f"{ACTIVITIES}affiliation-group/{EDUCATION}education-summary"
        ),
        columns=[] + AFFILIATION,
    ),
    PersonDetailsTableMeta(
        "person_employments",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/{ACTIVITIES}employments/"
            f"{ACTIVITIES}affiliation-group/{EMPLOYMENT}employment-summary"
        ),
        columns=[] + AFFILIATION,
    ),
    PersonDetailsTableMeta(
        "person_invited_positions",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/"
            f"{ACTIVITIES}invited-positions/"
            f"{ACTIVITIES}affiliation-group/"
            f"{INVITED_POSITION}invited-position-summary"
        ),
        columns=[] + AFFILIATION,
    ),
    PersonDetailsTableMeta(
        "person_memberships",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/"
            f"{ACTIVITIES}memberships/{ACTIVITIES}affiliation-group/"
            f"{MEMBERSHIP}membership-summary"
        ),
        columns=[] + AFFILIATION,
    ),
    PersonDetailsTableMeta(
        "person_qualifications",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/"
            f"{ACTIVITIES}qualifications/"
            f"{ACTIVITIES}affiliation-group/"
            f"{QUALIFICATION}qualification-summary"
        ),
        columns=[] + AFFILIATION,
    ),
    PersonDetailsTableMeta(
        "person_services",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/{ACTIVITIES}services/"
            f"{ACTIVITIES}affiliation-group/{SERVICE}service-summary"
        ),
        columns=[] + AFFILIATION,
    ),
    PersonDetailsTableMeta(
        "person_fundings",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/{ACTIVITIES}fundings/"
            f"{ACTIVITIES}group/{FUNDING}funding-summary"
        ),
        # pylint: disable-next=fixme
        # TODO external-ids, contributors
        columns=[
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
    PersonDetailsTableMeta(
        "person_peer_reviews",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/"
            f"{ACTIVITIES}peer-reviews/{ACTIVITIES}group/"
            f"{ACTIVITIES}peer-review-group/"
            f"{PEER_REVIEW}peer-review-summary"
        ),
        columns=[
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
    PersonDetailsTableMeta(
        "person_research_resources",
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/"
            f"{ACTIVITIES}research-resources/{ACTIVITIES}group/"
            f"{RESEARCH_RESOURCE}research-resource-summary"
        ),
        columns=[
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
    # Use generic TableMeta to setup custom cursor
    TableMeta(
        "person_works",
        foreign_key="person_id",
        parent_name="persons",
        primary_key="id",
        cursor_class=PersonWorksCursor,
        extract_multiple=all_getter(
            f"{ACTIVITIES}activities-summary/{ACTIVITIES}works/"
            f"{ACTIVITIES}group/{COMMON}external-ids"
        ),
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
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
    except KeyError as exc:
        raise Alexandria3kError(f"Unknown table name: '{name}'.") from exc


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


class ErrorElement:
    """A class used for representing error elements"""

    def find(self, _path):
        """Placeholder to the actual XML tree element."""
        return None

    def findall(self, _path):
        """Placeholder to the actual XML tree element."""
        return None


class TarFiles:
    """The source of the XML files in a compressed tar archive.
    This is a singleton, iterated over either data_source
    (when partitioning is in effect) or by PersonsCursor.
    The file contents are accessed by PersonsCursor."""

    def __init__(self, file_path, sample):
        # Collect the names of all available data files
        self.file_path = file_path
        self.sample = sample
        # Set by tar_generator
        self.tar_info = None
        self.orcid = None
        self.tar = None
        self.file_id = -1
        # Updated by get_element_tree
        self.element_tree = None

    def tar_generator(self):
        """A generator function iterating over the tar file entries."""
        # pylint: disable-next=consider-using-with
        self.tar = tarfile.open(self.file_path, "r|gz")
        for self.tar_info in self.tar:
            if not self.tar_info.isreg():
                continue

            # Obtain ORCID from file name to avoid extraction and parsing
            (_root, _checksum, file_name) = self.tar_info.name.split("/")
            self.file_id += 1
            self.orcid = file_name[:-4]
            self.element_tree = None
            yield self.file_id

    def get_element_tree(self):
        """Return the parsed XML data of the current element"""
        if self.element_tree is not None:
            return self.element_tree
        # Extract and parse XML data
        reader = self.tar.extractfile(self.tar_info)
        xml_data = reader.read()
        self.element_tree = ET.fromstring(xml_data)

        # Sanity check
        orcid_xml = self.element_tree.find(
            f"{COMMON}orcid-identifier/{COMMON}path"
        )
        if orcid_xml is None:
            # Identify error records
            warn(f"Error parsing {self.orcid}")
            self.element_tree = ErrorElement()
        else:
            assert self.orcid == orcid_xml.text

        perf.log(f"Parse {self.orcid}")
        return self.element_tree

    def close(self):
        """Close the opened tar file"""
        self.tar.close()

    def get_container_iterator(self):
        """Return an iterator over the int identifiers of all data files"""
        return self.tar_generator()

    def get_container_id(self):
        """Return the file id of the current element."""
        return self.file_id

    def get_orcid(self):
        """Return the ORCID of the current element."""
        return self.orcid

    def get_container_name(self, file_id):
        """Return the name of the file corresponding to the specified fid"""
        if file_id != self.file_id:
            raise Alexandria3kInternalError(f"Stale container id {file_id}")
        return f"{self.orcid}.xml"


class VTSource:
    """Virtual table data source.  This gets registered with the apsw
    Connection through createmodule in order to instantiate the virtual
    tables."""

    def __init__(self, data_source, sample):
        self.data_files = TarFiles(data_source, sample)
        self.table_dict = {t.get_name(): t for t in tables}
        self.sample = sample

    def Create(self, _db, _module_name, _db_name, table_name):
        """Create the specified virtual table
        Return the tuple required by the apsw.Source.Create method:
        the table's schema and the virtual table class."""
        table = self.table_dict[table_name]
        return table.table_schema(), StreamingCachedContainerTable(
            table, self.table_dict, self.data_files, self.sample
        )

    Connect = Create

    def get_container_iterator(self):
        """Return an iterator over the data files' identifiers"""
        return self.data_files.get_container_iterator()

    def get_container_name(self, fid):
        """Return the name of the file corresponding to the specified fid"""
        return self.data_files.get_container_name(fid)


class Orcid(DataSource):
    """
    Create an object containing ORCID meta-data that supports queries over
    its (virtual) table and the population of an SQLite database with its
    data.

    :param orcid_file: The file path to the compressed tar file containing
        ORCID data.
    :type orcid_file: str

    :param sample: A callable to control container sampling, defaults
        to `lambda n: True`.
        The population or query method will call this argument
        for each ORCID person record with each ORCID as its argument.
        When the callable returns `True` the container record will get
        processed, when it returns `False` the record will get skipped.
    :type sample: callable, optional

    :param attach_databases: A list of colon-joined tuples specifying
        a database name and its path, defaults to `None`.
        The specified databases are attached and made available to the
        query and the population condition through the specified database
        name.
    :type attach_databases: list, optional

    """

    def __init__(
        self,
        orcid_file,
        sample=lambda n: True,
        attach_databases=None,
    ):
        super().__init__(
            VTSource(orcid_file, sample),
            tables,
            attach_databases,
        )
