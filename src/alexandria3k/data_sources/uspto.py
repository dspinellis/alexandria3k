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

import os
import re

from alexandria3k.common import Alexandria3kError
from alexandria3k.data_source import (
    CONTAINER_INDEX,
    ROWID_INDEX,
    DataSource,
    ItemsCursor,
    StreamingCachedContainerTable,
)
from alexandria3k.db_schema import ColumnMeta, TableMeta
from alexandria3k.file_xml_cache import get_file_cache
from alexandria3k.uspto_zip_cache import get_zip_cache
from alexandria3k.xml import (
    XMLCursor,
    agetter,
    all_getter,
    get_element,
    getter,
)

# Bulk data can be found here. https://bulkdata.uspto.gov
# Patent Grant Bibliographic (Front Page) Text Data (JAN 1976 - PRESENT)
DEFAULT_SOURCE = None

# Extract the date of the Zip file name.
# "ipgb" stands for "issued patent grant bibliography"
# and it is the same for every publication file.
# e.g. ipgb20230801.zip return 20230801.
NAME_EXPRESSION = r"ipgb(.*?)\.zip"

# Dataset Description — Patent grant full-text data (no images)
# JAN 1976 — present Automated Patent System (APS)
# Contains the full text of each patent grant issued weekly
# Tuesdays from January 1, 1976, to present excludes images/drawings and reexaminations.
# https://developer.uspto.gov/product/patent-grant-bibliographic-dataxml


# pylint: disable=too-many-lines
# pylint: disable=too-many-instance-attributes
class ZipFiles:
    """Iterate over all Zip files inside a directory
    and access its individual information.

    When no partitioning is in effect, return a Zip file
    path on demand using a specific id(zip_index) managed by
    PatentsFilesCursor. Iterate over all XML chunks representing
    a patent inside the Zip file and parse them. Return the number
    of Zip files in the directory to assert the EOF.

    When partitioning is in effect, access the Zip file contents
    dynamically via a generator function. Access individual patent
    XML chunks, embedded inside a single XML file, within the zip
    file. Distinguish patent XML chunks using the XML declaration,
    managed by uspto_zip_cache. Yield a Zip file path and a container
    id representing a unique patent until all zip files have been read.
    Access and parse the patent XML chunk through PatentsFilesCursor.
    """

    def __init__(self, directory, sample_container):
        # Collect the names of all available data files
        self.file_paths = []
        self.unique_patent_xml_files = []
        self.file_directory = directory
        self.filename = None
        self.file_id = 0
        self.container_id = -1
        self.zip_path = None
        self.sample = sample_container

        # Read through the directory that contains
        # the weekly patent releases of each year.
        for folder in os.listdir(self.file_directory):
            year_folder_path = os.path.join(self.file_directory, folder)
            if not os.path.isdir(year_folder_path):
                continue
            for file_name in os.listdir(year_folder_path):
                path = os.path.join(year_folder_path, file_name)
                if not path.endswith(".zip"):
                    continue
                if not os.path.isfile(path):
                    continue
                if not self.sample(("path", file_name)):
                    continue
                self.file_paths.append(path)
        # Raise error if file path list is empty.
        if len(self.file_paths) == 0:
            raise Alexandria3kError("No Zip files paths were detected.")

    def get_zip_contents(self, path):
        """Return the a list of all the patent inside the Zip."""
        # Reading Zip file.
        return get_zip_cache().read(path, self.sample)

    def get_xml_chunk(self, container_id):
        """Return a XML chunk using the container_id."""
        patent_xml = self.unique_patent_xml_files[container_id]

        return patent_xml

    def zip_generator(self):
        """A generator function iterating over the Zip files and the
        containers inside."""
        # pylint: disable-next=consider-using-with
        for path in self.file_paths:
            # Access contents inside Zip for enumeration, no parsing.
            self.unique_patent_xml_files = self.get_zip_contents(path)
            self.filename = self.get_filename(path)
            self.container_id = -1
            self.zip_path = path
            for patent in self.unique_patent_xml_files:
                if patent is None:
                    continue

                self.container_id += 1
                yield self.container_id

    def get_current_zip_path_by_id(self, zip_file_id):
        """Return the path of the current Zip file, using id."""
        self.zip_path = self.file_paths[zip_file_id]
        return self.zip_path

    def get_filename(self, path):
        "Return the filename of the current Zip file."
        # Search for the pattern in the input string
        match = re.search(NAME_EXPRESSION, path)

        if match:
            return match.group(1)
        return "No filename found."

    def get_current_zip_path(self):
        """Return the path of the current Zip file, updates from generator."""
        return self.zip_path

    def get_container_id(self):
        """Return the container id of the XML chunk."""
        return self.container_id

    def length_of_zip_files(self):
        """Return the length of the array of data files"""
        return len(self.file_paths)

    def get_container_iterator(self):
        """Return an iterator over the int identifiers of all chunks XML data files"""
        return self.zip_generator()

    # pylint: disable=unused-argument
    def get_container_name(self, fid):
        """Return the name of the file."""
        return self.filename


def alternative_path_getter(path1, path2):
    """Return all elements from the specified path. If
    path1 doesn't work, use path2 as an alternative."""
    return lambda tree: tree.findall(path1) or tree.findall(path2)


class VTSource:
    """Virtual table data source. This gets registered with the apsw
    Connection through createmodule in order to instantiate the virtual
    tables."""

    def __init__(self, data_directory, sample):
        self.data_files = ZipFiles(data_directory, sample)
        self.table_dict = {t.get_name(): t for t in tables}
        self.sample = sample

    def Create(self, _db, _module_name, _db_name, table_name):
        """Create the specified virtual table
        Return the tuple required by the apsw.Source.Create method:
        the table's schema and the virtual table class."""
        table = self.table_dict[table_name]
        return table.table_schema(), StreamingCachedContainerTable(
            table,
            self.table_dict,
            self.data_files,
            self.sample,
        )

    Connect = Create

    def get_container_iterator(self):
        """Return an iterator over the data files identifiers"""
        return self.data_files.get_container_iterator()

    def get_container_name(self, fid):
        """Return the name of the file corresponding to the specified fid"""
        return self.data_files.get_container_name(fid)


# pylint: disable=too-many-instance-attributes
class PatentsFilesCursor(ItemsCursor):
    """ "A cursor over the US patent XML data files inside a Zip file.
    If it is used through data_source partitioned data access within
    the context of a ZipFiles iterator, it shall return a single container
    representing a US patents inside the Zip file. Otherwise it shall
    iterate over all Zip files and the containers inside. Internal use only.
    Not used directly by an SQLite table.
    """

    def __init__(self, table):
        """Not part of the apsw VTCursor interface.
        The table argument is a StreamingTable object"""
        super().__init__(table)
        # The following get initialized in Filter()
        self.container_id = None
        self.zip_index = None
        self.current_file_path = None
        self.xml_contents = []

    def Filter(self, index_number, _index_name, constraint_args):
        """Always called first to initialize an iteration to the first
        (possibly constrained) row of the table"""

        if index_number == 0:
            # No index; initialize the path to the first Zip file and
            # iterate through all the containers inside.
            # The decompressing/parsing/caching and moving to the next
            # Zip file takes place inside the Next function.
            self.zip_index = 0
            self.container_id = -1
            self.single_file = False
            # Initialize the Zip file path.
            self.current_file_path = (
                self.table.data_source.get_current_zip_path_by_id(
                    self.zip_index
                )
            )
        elif index_number & CONTAINER_INDEX:
            # Index; constraint reading through the specified container.
            self.single_file = True
            self.file_read = False
            self.container_id = constraint_args[0] - 1
            self.current_file_path = (
                self.table.data_source.get_current_zip_path()
            )
        self.Next()

    def Next(self):
        """Advance reading to the next available container."""
        if self.single_file and self.file_read:
            self.eof = True
            return

        self.container_id += 1
        # Zip file read.
        self.xml_contents = get_zip_cache().read(
            self.current_file_path, self.table.data_source.sample
        )

        if self.container_id >= len(self.xml_contents):
            # Zip file ended.
            if (
                self.table.data_source.length_of_zip_files()
                > self.zip_index + 1
            ):
                # Moving to the next available Zip file.
                # Updating new container id.
                self.container_id = 0
                self.zip_index += 1
                self.current_file_path = (
                    self.table.data_source.get_current_zip_path_by_id(
                        self.zip_index
                    )
                )
                self.xml_contents = get_zip_cache().read(
                    self.current_file_path, self.table.data_source.sample
                )
            else:
                # Returns when all Zip files have been read.
                self.eof = True
                return

        # Check for EOF.
        if len(self.xml_contents) == 0:
            self.eof = True
            return

        # Container parsing.
        self.items = get_file_cache().read(
            self.xml_contents[self.container_id], self.container_id
        )
        self.eof = False
        # The single container has been read. Set EOF in next Next call.
        self.file_read = True

    def get_container_id(self):
        """Get the container id of the XML chunk."""
        return self.container_id


class PatentsElementsCursor(XMLCursor):
    """A cursor over USPTO items. It depends on the
    extract multiple table property. Gets all the elements
    below a patent and then iterates over them."""


class PatentsCursor(PatentsElementsCursor):
    """A virtual table cursor over patents data.
    If it is used through data_source partitioned data access
    within the context of a ZipFiles iterator,
    it shall return the single element of the ZipFiles iterator.
    Otherwise it shall iterate over all elements."""

    def __init__(self, table):
        """Not part of the apsw VTCursor interface.
        The table argument is a StreamingTable object"""
        super().__init__(table, None)
        self.files_cursor = PatentsFilesCursor(table)
        # Initialized in Filter()
        self.item_index = None

    def Eof(self):
        """Return True when the end of the table's records has been reached."""
        return self.eof

    def get_container_id(self):
        """Return the id of the container containing the data being fetched.
        Not part of the apsw API."""
        return self.files_cursor.get_container_id()

    def Rowid(self):
        """Return a unique id of the row along all records"""
        return self.item_index

    # pylint: disable=too-many-return-statements
    def Column(self, col):
        """Return the value of the column with ordinal col"""
        # print(f"Column {col}")
        if col == -1:
            return self.Rowid()

        if col == 0:  # id
            return self.files_cursor.get_container_id()

        if col == 1:
            return self.files_cursor.get_container_id()

        extract_function = self.table.get_value_extractor_by_ordinal(col)
        return extract_function(self.files_cursor.items)

    # pylint: disable=arguments-differ
    def Filter(self, index_number, _index_name, constraint_args):
        """Always called first to initialize an iteration to the first row
        of the table according to the index"""
        self.files_cursor.Filter(index_number, _index_name, constraint_args)
        self.eof = self.files_cursor.Eof()
        if index_number & ROWID_INDEX:
            # This has never happened, so this is untested
            self.item_index = constraint_args[1]
        else:
            self.item_index = 0

    def Next(self):
        """Advance to the next item."""
        self.item_index = 0
        self.files_cursor.Next()
        self.eof = self.files_cursor.eof

    def current_row_value(self):
        """Return the current row. Not part of the apsw API."""
        return self.files_cursor.items

    def Close(self):
        """Cursor's destructor, used for cleanup"""
        self.files_cursor.Close()


class PatentsDetailsCursor(PatentsElementsCursor):
    """A cursor over any of a patent's details data."""

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
        if col == 0:
            return self.parent_cursor.get_container_id()

        if col == 1:
            return self.parent_cursor.get_container_id()

        return super().Column(col)


class PatentsCpcCursor(PatentsElementsCursor):
    """A cursor over any of a patent's Cooperative
    Patent Classification scheme (CPC) data."""

    def __init__(self, table, parent_cursor):
        """Not part of the apsw VTCursor interface.
        The table argument is a StreamingTable object"""
        super().__init__(table, parent_cursor)
        self.extract_multiple = all_getter(
            "us-bibliographic-data-grant/classifications-cpc/*"
        )

        # The are two types of cpc classifications,
        # `main-cpc` or `further-cpc`, in both cases
        # the XML pattern are the same and given
        # in the list below.
        column_names = [
            "classification-cpc/cpc-version-indicator/date",
            "classification-cpc/section",
            "classification-cpc/class",
            "classification-cpc/subclass",
            "classification-cpc/main-group",
            "classification-cpc/subgroup",
            "classification-cpc/symbol-position",
            "classification-cpc/classification-value",
            "classification-cpc/action-date/date",
            "classification-cpc/generating-office/country",
            "classification-cpc/classification-status",
            "classification-cpc/classification-data-source",
            "classification-cpc/scheme-origination-code",
            "combination-set/group-number",
            "combination-set/combination-rank/rank-number",
        ]

        self.column_contents = {
            i + 3: value for i, value in enumerate(column_names)
        }

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 16k elements."""
        return (self.parent_cursor.Rowid() << 14) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:
            return self.parent_cursor.get_container_id()

        if col == 1:
            return self.parent_cursor.get_container_id()

        if col == 2:
            return self.elements[self.record_id()].tag

        if col >= 3:
            return get_element(
                self.elements[self.record_id()],
                f"{self.column_contents[col]}",
            )

        return super().Column(col)


class PatentsRelatedDocumentsCursor(PatentsElementsCursor):
    """A cursor over any of a patent's related documents data."""

    def __init__(self, table, parent_cursor):
        """Not part of the apsw VTCursor interface.
        The table argument is a StreamingTable object"""
        super().__init__(table, parent_cursor)
        self.extract_multiple = all_getter(
            "us-bibliographic-data-grant/us-related-documents/*"
        )
        column_names = [
            "relation/parent-doc/document-id/doc-number",
            "relation/parent-doc/document-id/kind",
            "relation/parent-doc/document-id/name",
            "relation/parent-doc/document-id/date",
            "relation/parent-doc/parent-status",
            "relation/parent-doc/parent-grant-document/document-id/doc-number",
            "relation/parent-doc/parent-pct-document/document-id/doc-number",
            "relation/parent-doc/international-filing-date",
            "relation/child-doc/document-id/doc-number",
            "relation/child-doc/document-id/kind",
            "relation/child-doc/document-id/name",
            "relation/child-doc/document-id/date",
            "relation/child-doc/international-filing-date",
            "document-id/doc-number",
            "document-id/kind",
            "document-id/name",
            "document-id/date",
            "us-provisional-application-status",
            "document-corrected/document-id/doc-number",
            "document-corrected/document-id/kind",
            "document-corrected/document-id/name",
            "document-corrected/document-id/date",
            "type-of-correction",
            "gazette-reference/gazette-num",
            "gazette-reference/date",
            "text",
        ]

        self.column_contents = {
            i + 3: value for i, value in enumerate(column_names)
        }

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 16k elements."""
        return (self.parent_cursor.Rowid() << 14) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:
            return self.parent_cursor.get_container_id()

        if col == 1:
            return self.parent_cursor.get_container_id()

        if col == 2:
            return self.elements[self.record_id()].tag

        if col >= 3:
            return get_element(
                self.elements[self.record_id()],
                f"{self.column_contents[col]}",
            )

        return super().Column(col)


class PatentsAssigneesCursor(PatentsElementsCursor):
    """A cursor over any of a patent's assignees data"""

    def __init__(self, table, parent_cursor):
        """Not part of the apsw VTCursor interface. The table argument is a
        StreamingTable object. The data under the assignee element can be
        either an entity called %name_group or an addressbook element.
        However, under the addressbook element the data appear again as
        %name_group, with some additional elements."""

        super().__init__(table, parent_cursor)
        # Get all the assignees
        self.extract_multiple = all_getter(
            "us-bibliographic-data-grant/assignees/*"
        )

        # Initialize a list of XML patterns to access the data of the
        # assignee element. If an addressbook element exist under
        # the assignee, then it is appended on the beginning of the string
        # for matching the required elements.
        column_names = [
            "name",
            "first-name",
            "middle-name",
            "last-name",
            "orgname",
            "suffix",
            "iid",
            "role",
            "department",
            "synonym",
            "registered_number",
            "email",
            "url",
            "text",
            "addressbook/address/city",
            "addressbook/address/state",
            "addressbook/address/country",
            "addressbook/address/postcode",
        ]

        self.column_contents = {
            i + 3: value for i, value in enumerate(column_names)
        }

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 16k elements."""
        return (self.parent_cursor.Rowid() << 14) | self.element_index

    # pylint: disable=too-many-return-statements
    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:
            return self.parent_cursor.get_container_id()

        if col == 1:
            return self.parent_cursor.get_container_id()

        if col == 2:
            return self.elements[self.record_id()].tag

        if col >= 3:
            # Check if an addressbook element exists.
            if self.elements[self.record_id()].find("addressbook") is not None:
                # Append addressbook string to meet XML pattern.
                pattern = "addressbook/" + f"{self.column_contents[col]}"

                return get_element(self.elements[self.record_id()], pattern)
            # If false use the dictionary without addressbook.
            return get_element(
                self.elements[self.record_id()],
                f"{self.column_contents[col]}",
            )

        return super().Column(col)


class USPartiesTableMeta(TableMeta):
    """Table metadata for US parties details. Applicants, inventors
    and agents are under the US parties element. Objects of this
    class are injected with properties and columns common to all
    US parties tables."""

    def __init__(self, name, **kwargs):
        kwargs["foreign_key"] = "patent_id"
        kwargs["parent_name"] = "us_patents"
        kwargs["primary_key"] = "id"
        kwargs["cursor_class"] = PatentsDetailsCursor
        kwargs["columns"] = [
            ColumnMeta("patent_id"),
            ColumnMeta("container_id"),
            ColumnMeta(
                "sequence",
                agetter("sequence"),
            ),
            ColumnMeta(
                "name",
                getter("addressbook/name"),
            ),
            ColumnMeta(
                "first_name",
                getter("addressbook/first-name"),
            ),
            ColumnMeta(
                "middle_name",
                getter("addressbook/middle-name"),
            ),
            ColumnMeta(
                "last_name",
                getter("addressbook/last-name"),
            ),
            ColumnMeta(
                "org_name",
                getter("addressbook/orgname"),
            ),
            ColumnMeta(
                "suffix",
                getter("addressbook/suffix"),
            ),
            ColumnMeta(
                "iid",
                getter("addressbook/iid"),
            ),
            ColumnMeta(
                "role",
                getter("addressbook/role"),
            ),
            ColumnMeta(
                "department",
                getter("addressbook/department"),
            ),
            ColumnMeta(
                "synonym",
                getter("addressbook/synonym"),
            ),
            ColumnMeta(
                "registered_number",
                getter("addressbook/registered_number"),
            ),
            ColumnMeta(
                "email",
                getter("addressbook/email"),
            ),
            ColumnMeta(
                "url",
                getter("addressbook/url"),
            ),
            ColumnMeta(
                "text",
                getter("addressbook/text"),
            ),
            ColumnMeta(
                "city",
                getter("addressbook/address/city"),
            ),
            ColumnMeta(
                "state",
                getter("addressbook/address/state"),
            ),
            ColumnMeta(
                "country",
                getter("addressbook/address/country"),
            ),
            ColumnMeta(
                "postcode",
                getter("addressbook/address/postcode"),
            ),
        ] + kwargs["columns"]
        super().__init__(name, **kwargs)


tables = [
    TableMeta(
        "us_patents",
        cursor_class=PatentsCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta(
                "language",
                agetter("lang"),
                description="Standardized value EN.",
            ),
            ColumnMeta(
                "status",
                agetter("status"),
                description="Standardized value Production.",
            ),
            ColumnMeta(
                "country",
                agetter("country"),
                description="Standardized value US.",
            ),
            ColumnMeta(
                "filename",
                agetter("file"),
                description="Filename for the specific date.",
            ),
            ColumnMeta("date_produced", agetter("date-produced")),
            ColumnMeta(
                "date_published",
                agetter("date-publ"),
            ),
            ColumnMeta(
                "publication_reference_doc_number",
                getter(
                    "us-bibliographic-data-grant/publication-reference/document-id/doc-number"
                ),
            ),
            ColumnMeta(
                "publication_reference_kind",
                getter(
                    "us-bibliographic-data-grant/publication-reference/document-id/kind"
                ),
            ),
            ColumnMeta(
                "publication_reference_name",
                getter(
                    "us-bibliographic-data-grant/publication-reference/document-id/name"
                ),
            ),
            ColumnMeta(
                "type",
                agetter(
                    "appl-type",
                    "us-bibliographic-data-grant/application-reference",
                ),
            ),
            ColumnMeta(
                "application_reference_doc_number",
                getter(
                    "us-bibliographic-data-grant/application-reference/document-id/doc-number"
                ),
            ),
            ColumnMeta(
                "application_reference_kind",
                getter(
                    "us-bibliographic-data-grant/application-reference/document-id/kind"
                ),
            ),
            ColumnMeta(
                "application_reference_name",
                getter(
                    "us-bibliographic-data-grant/application-reference/document-id/name"
                ),
            ),
            ColumnMeta(
                "application_reference_date",
                getter(
                    "us-bibliographic-data-grant/application-reference/document-id/date"
                ),
            ),
            ColumnMeta(
                "locarno_edition",
                getter(
                    "us-bibliographic-data-grant/classification-locarno/document-id/edition"
                ),
                description="Refers to Locarno Classification.",
            ),
            ColumnMeta(
                "locarno_main_classification",
                getter(
                    "us-bibliographic-data-grant/classification-locarno/main-classification"
                ),
                description="Refers to Locarno Classification.",
            ),
            ColumnMeta(
                "locarno_further_classification",
                getter(
                    "us-bibliographic-data-grant/classification-locarno/further-classification"
                ),
                description="Refers to Locarno Classification.",
            ),
            ColumnMeta(
                "locarno_text",
                getter(
                    "us-bibliographic-data-grant/classification-locarno/text"
                ),
                description="Refers to Locarno Classification.",
            ),
            ColumnMeta(
                "national_edition",
                getter(
                    "us-bibliographic-data-grant/classification-national/edition"
                ),
                description="Refers to National Classification.",
            ),
            ColumnMeta(
                "national_main_classification",
                getter(
                    "us-bibliographic-data-grant/classification-national/main-classification"
                ),
                description="Refers to National Classification.",
            ),
            ColumnMeta(
                "national_further_classification",
                getter(
                    "us-bibliographic-data-grant/classification-national/further-classification"
                ),
                description="Refers to National Classification.",
            ),
            ColumnMeta(
                "national_additional_info",
                getter(
                    "us-bibliographic-data-grant/classification-national/additional-info"
                ),
                description="Refers to National Classification.",
            ),
            ColumnMeta(
                "national_linked_indexing_code_group",
                getter(
                    "us-bibliographic-data-grant/classification-national/linked-indexing-code-group"
                ),
                description="Refers to National Classification.",
            ),
            ColumnMeta(
                "national_unlinked_indexing_code",
                getter(
                    "us-bibliographic-data-grant/classification-national/unlinked-indexing-code"
                ),
                description="Refers to National Classification.",
            ),
            ColumnMeta(
                "national_text",
                getter(
                    "us-bibliographic-data-grant/classification-national/text"
                ),
                description="Refers to National Classification.",
            ),
            ColumnMeta(
                "series_code",
                getter(
                    "us-bibliographic-data-grant/us-application-series-code"
                ),
            ),
            ColumnMeta(
                "invention_title",
                getter("us-bibliographic-data-grant/invention-title"),
            ),
            ColumnMeta(
                "botanic_name",
                getter("us-bibliographic-data-grant/us-botanic/latin-name"),
            ),
            ColumnMeta(
                "botanic_variety",
                getter("us-bibliographic-data-grant/us-botanic/variety"),
            ),
            ColumnMeta(
                "claims_number",
                getter("us-bibliographic-data-grant/number-of-claims"),
            ),
            ColumnMeta(
                "exemplary_claim",
                getter("us-bibliographic-data-grant/us-exemplary-claim"),
            ),
            ColumnMeta(
                "figures_number",
                getter(
                    "us-bibliographic-data-grant/figures/number-of-figures"
                ),
                description="Excluded element figures-to-publish.",
            ),
            ColumnMeta(
                "drawings_number",
                getter(
                    "us-bibliographic-data-grant/figures/number-of-drawing-sheets"
                ),
            ),
            ColumnMeta(
                "primary_examiner_firstname",
                getter(
                    "us-bibliographic-data-grant/examiners/primary-examiner/first-name"
                ),
            ),
            ColumnMeta(
                "primary_examiner_lastname",
                getter(
                    "us-bibliographic-data-grant/examiners/primary-examiner/last-name"
                ),
            ),
            ColumnMeta(
                "assistant_examiner_firstname",
                getter(
                    "us-bibliographic-data-grant/examiners/assistant-examiner/first-name"
                ),
            ),
            ColumnMeta(
                "assistant_examiner_lastname",
                getter(
                    "us-bibliographic-data-grant/examiners/assistant-examiner/last-name"
                ),
            ),
            ColumnMeta(
                "authorized_officer_firstname",
                getter(
                    "us-bibliographic-data-grant/authorized-officer/first-name"
                ),
            ),
            ColumnMeta(
                "authorized_officer_lastname",
                getter(
                    "us-bibliographic-data-grant/authorized-officer/last-name"
                ),
            ),
            ColumnMeta(
                "hague_reg_num",
                getter(
                    "us-bibliographic-data-grant/hague-agreement-data/"
                    + "international-registration-number"
                ),
            ),
            ColumnMeta(
                "cpa_flag",
                agetter(
                    "grant-cpa-text",
                    "us-bibliographic-data-grant/us-issued-on-continued-prosecution-application",
                ),
                description="Continued prosecution application flag.",
            ),
            ColumnMeta(
                "rule47_flag",
                getter("us-bibliographic-data-grant/rule-47-flag"),
                description="Refused to execute the application.",
            ),
        ],
    ),
    TableMeta(
        "usp_icpr_classifications",
        foreign_key="patent_id",
        parent_name="us_patents",
        primary_key="id",
        cursor_class=PatentsDetailsCursor,
        extract_multiple=all_getter(
            "us-bibliographic-data-grant/classifications-ipcr/classification-ipcr"
        ),
        columns=[
            ColumnMeta("patent_id"),
            ColumnMeta("container_id"),
            ColumnMeta(
                "ipc_date",
                getter("ipc-version-indicator/date"),
            ),
            ColumnMeta(
                "class_level",
                getter("classification-level"),
            ),
            ColumnMeta("section", getter("section")),
            ColumnMeta("class", getter("class")),
            ColumnMeta("subclass", getter("subclass")),
            ColumnMeta(
                "main_group",
                getter("main-group"),
            ),
            ColumnMeta("subgroup", getter("subgroup")),
            ColumnMeta("symbol_position", getter("symbol-position")),
            ColumnMeta("class_value", getter("classification-value")),
            ColumnMeta("action_date", getter("action-date/date")),
            ColumnMeta(
                "generating_office", getter("generating-office/country")
            ),
            ColumnMeta("class_status", getter("classification-status")),
            ColumnMeta("class_source", getter("classification-data-source")),
        ],
    ),
    TableMeta(
        "usp_cpc_classifications",
        foreign_key="patent_id",
        parent_name="us_patents",
        primary_key="id",
        cursor_class=PatentsCpcCursor,
        extract_multiple=all_getter(
            "us-bibliographic-data-grant/classifications-cpc"
        ),
        columns=[
            ColumnMeta("patent_id"),
            ColumnMeta("container_id"),
            ColumnMeta(
                "type",
                getter("ipc-version-indicator/date"),
                description="Main or further cpc.",
            ),
            ColumnMeta(
                "cpc_version_indicator",
                description="Date.",
            ),
            ColumnMeta("section"),
            ColumnMeta("class"),
            ColumnMeta("sub_class"),
            ColumnMeta("main_group"),
            ColumnMeta("sub_group"),
            ColumnMeta("symbol_position"),
            ColumnMeta("class_value"),
            ColumnMeta("action_date"),
            ColumnMeta("generating_office"),
            ColumnMeta("class_status"),
            ColumnMeta("class_data_source"),
            ColumnMeta("scheme_origination_code"),
            ColumnMeta("combination_group_number"),
            ColumnMeta("combination_rank_number"),
        ],
    ),
    TableMeta(
        "usp_related_documents",
        foreign_key="patent_id",
        parent_name="us_patents",
        primary_key="id",
        cursor_class=PatentsRelatedDocumentsCursor,
        columns=[
            ColumnMeta("patent_id"),
            ColumnMeta("container_id"),
            ColumnMeta("relation"),
            ColumnMeta(
                "parent_doc_number",
            ),
            ColumnMeta(
                "parent_doc_kind",
            ),
            ColumnMeta(
                "parent_doc_name",
            ),
            ColumnMeta(
                "parent_doc_date",
            ),
            ColumnMeta(
                "status",
            ),
            ColumnMeta(
                "parent_grant_doc_number",
            ),
            ColumnMeta(
                "parent_pct_doc_number",
            ),
            ColumnMeta(
                "parent_filing_date",
            ),
            ColumnMeta(
                "child_doc_number",
            ),
            ColumnMeta(
                "child_doc_kind",
            ),
            ColumnMeta(
                "child_doc_name",
            ),
            ColumnMeta(
                "child_doc_date",
            ),
            ColumnMeta(
                "child_filing_date",
            ),
            ColumnMeta(
                "document_number",
            ),
            ColumnMeta(
                "document_kind",
            ),
            ColumnMeta(
                "document_name",
            ),
            ColumnMeta(
                "document_date",
            ),
            ColumnMeta(
                "provisional_application_status",
            ),
            ColumnMeta(
                "corrected_document_doc_number",
            ),
            ColumnMeta(
                "corrected_document_kind",
            ),
            ColumnMeta(
                "corrected_document_name",
            ),
            ColumnMeta(
                "corrected_document_date",
            ),
            ColumnMeta(
                "type_of_correction",
            ),
            ColumnMeta(
                "gazette_number",
            ),
            ColumnMeta(
                "gazette_date",
            ),
            ColumnMeta(
                "correction_text",
            ),
        ],
    ),
    TableMeta(
        "usp_field_of_classification",
        foreign_key="patent_id",
        parent_name="us_patents",
        primary_key="id",
        cursor_class=PatentsDetailsCursor,
        extract_multiple=all_getter(
            "us-bibliographic-data-grant/us-field-of-classification-search"
        ),
        columns=[
            ColumnMeta("patent_id"),
            ColumnMeta("container_id"),
            ColumnMeta(
                "ipcr_classification",
                getter("us-classifications-ipcr"),
            ),
            ColumnMeta(
                "cpc_classification_text",
                getter("classification-cpc-text"),
            ),
            ColumnMeta(
                "cpc_classification_combination_text",
                getter("classification-cpc-combination-text"),
            ),
            ColumnMeta(
                "national_edition",
                getter("classification-national/edition"),
            ),
            ColumnMeta(
                "national_main",
                getter("classification-national/main-classification"),
            ),
            ColumnMeta(
                "national_further",
                getter("classification-national/further-classification"),
            ),
            ColumnMeta(
                "national_additional_info",
                getter("classification-national/additional-info"),
            ),
            ColumnMeta(
                "national_linked_code_group",
                getter("classification-national/linked-indexing-code-group"),
            ),
            ColumnMeta(
                "national_unlinked_code",
                getter("classification-national/unlinked-indexing-code"),
            ),
            ColumnMeta(
                "national_text",
                getter("classification-national/text"),
            ),
        ],
    ),
    USPartiesTableMeta(
        "usp_inventors",
        extract_multiple=alternative_path_getter(
            "us-bibliographic-data-grant/us-parties/inventors/inventor",
            "us-bibliographic-data-grant/parties/inventors",
        ),
        columns=[
            ColumnMeta(
                "designation",
                agetter("designation"),
            ),
            ColumnMeta(
                "designated_country",
                getter("designated-states/country"),
            ),
            ColumnMeta(
                "designated_region",
                getter("designated-states/region"),
            ),
        ],
    ),
    USPartiesTableMeta(
        "usp_applicants",
        extract_multiple=alternative_path_getter(
            "us-bibliographic-data-grant/us-parties/us-applicants/us-applicant",
            "us-bibliographic-data-grant/parties/applicants/applicant",
        ),
        columns=[
            ColumnMeta(
                "app_type",
                agetter("app-type"),
                description="Application type.",
            ),
            ColumnMeta(
                "applicant_authority_category",
                agetter("applicant-authority-category"),
            ),
            ColumnMeta(
                "designation",
                agetter("designation"),
            ),
            ColumnMeta(
                "residence",
                getter("residence/country"),
            ),
            ColumnMeta(
                "us_rights",
                getter("us-rights"),
            ),
            ColumnMeta(
                "designated_country",
                getter("designated-states/country"),
            ),
            ColumnMeta(
                "designated_region",
                getter("designated-states/region"),
            ),
            ColumnMeta(
                "designated_country_inventor",
                getter("designated-states-as-inventor/country"),
            ),
            ColumnMeta(
                "designated_region_inventor",
                getter("designated-states-as-inventor/region"),
            ),
        ],
    ),
    USPartiesTableMeta(
        "usp_agents",
        extract_multiple=alternative_path_getter(
            "us-bibliographic-data-grant/us-parties/agents/agent",
            "us-bibliographic-data-grant/parties/agents/agent",
        ),
        columns=[
            ColumnMeta(
                "rep_type",
                agetter("rep-type"),
                description="Representative type.",
            ),
        ],
    ),
    TableMeta(
        "usp_assignees",
        foreign_key="patent_id",
        parent_name="us_patents",
        primary_key="id",
        cursor_class=PatentsAssigneesCursor,
        extract_multiple=all_getter(
            "us-bibliographic-data-grant/assignees/assignee"
        ),
        columns=[
            ColumnMeta("patent_id"),
            ColumnMeta("container_id"),
            ColumnMeta("name"),
            ColumnMeta("first_name"),
            ColumnMeta("middle_name"),
            ColumnMeta("last_name"),
            ColumnMeta("org_name"),
            ColumnMeta("suffix"),
            ColumnMeta("iid"),
            ColumnMeta("role"),
            ColumnMeta("department"),
            ColumnMeta("synonym"),
            ColumnMeta("registered_number"),
            ColumnMeta("email"),
            ColumnMeta("url"),
            ColumnMeta("text"),
            ColumnMeta("city"),
            ColumnMeta("state"),
            ColumnMeta("country"),
            ColumnMeta("postcode"),
        ],
    ),
    TableMeta(
        "usp_citations",
        foreign_key="patent_id",
        parent_name="us_patents",
        primary_key="id",
        cursor_class=PatentsDetailsCursor,
        extract_multiple=alternative_path_getter(
            "us-bibliographic-data-grant/us-references-cited/us-citation",
            "us-bibliographic-data-grant/references-cited/citation",
        ),
        columns=[
            ColumnMeta("patent_id"),
            ColumnMeta("container_id"),
            ColumnMeta(
                "patcit_num",
                agetter(
                    "num",
                    "patcit",
                ),
                description="Patent Citation within abstract, description or claims.",
            ),
            ColumnMeta(
                "nplcit_num",
                agetter(
                    "num",
                    "nplcit",
                ),
                description="Non-Patent Literature (NPL) CITation.",
            ),
            ColumnMeta(
                "nplcit_othercit",
                getter("nplcit/othercit"),
            ),
            ColumnMeta(
                "patcit_doc_number",
                getter("patcit/document-id/doc-number"),
            ),
            ColumnMeta(
                "patcit_country",
                getter("patcit/document-id/country"),
            ),
            ColumnMeta(
                "patcit_kind",
                getter("patcit/document-id/kind"),
            ),
            ColumnMeta(
                "patcit_date",
                getter("patcit/document-id/date"),
            ),
            ColumnMeta(
                "patcit_rel_passage",
                getter("patcit/rel-passage/passage"),
                description="Relevant passage within cited document.",
            ),
            ColumnMeta(
                "patcit_rel_category",
                getter("patcit/rel-passage/category"),
                description="Relevant passage within cited document.",
            ),
            ColumnMeta(
                "patcit_rel_claims",
                getter("patcit/rel-passage/rel-claims"),
            ),
            ColumnMeta(
                "category",
                getter("category"),
            ),
            ColumnMeta(
                "ipc_class_edition",
                getter("classification-ipc/edition"),
                description="International Patent Classification (IPC) data",
            ),
            ColumnMeta(
                "ipc_class_main",
                getter("classification-ipc/main-classification"),
            ),
            ColumnMeta(
                "ipc_class_further",
                getter("classification-ipc/further-classification"),
            ),
            ColumnMeta(
                "cpc_class_text",
                getter("classification-cpc-text"),
                description="Unstructured classification cpc data.",
            ),
            ColumnMeta(
                "national_class_country",
                getter("classification-national/country"),
            ),
            ColumnMeta(
                "national_class_edition",
                getter("classification-national/edition"),
            ),
            ColumnMeta(
                "national_class_main",
                getter("classification-national/main-classification"),
            ),
            ColumnMeta(
                "national_class_further",
                getter("classification-national/further-classification"),
            ),
        ],
    ),
    TableMeta(
        "usp_patent_family",
        foreign_key="patent_id",
        parent_name="us_patents",
        primary_key="id",
        cursor_class=PatentsDetailsCursor,
        extract_multiple=all_getter(
            "us-bibliographic-data-grant/patent-family"
        ),
        columns=[
            ColumnMeta("patent_id"),
            ColumnMeta("container_id"),
            ColumnMeta(
                "priority_app_doc_number",
                getter("priority-application/document-id/doc-number"),
                description="Priority application number.",
            ),
            ColumnMeta(
                "priority_app_country",
                getter("priority-application/document-id/country"),
            ),
            ColumnMeta(
                "priority_app_kind",
                getter("priority-application/document-id/kind"),
            ),
            ColumnMeta(
                "priority_app_name",
                getter("priority-application/document-id/name"),
            ),
            ColumnMeta(
                "priority_app_date",
                getter("priority-application/document-id/date"),
            ),
            ColumnMeta(
                "family_member_doc_number",
                getter("family-member/document-id/doc-number"),
                description="Priority application number.",
            ),
            ColumnMeta(
                "family_member_country",
                getter("family-member/document-id/country"),
            ),
            ColumnMeta(
                "family_member_kind",
                getter("family-member/document-id/kind"),
            ),
            ColumnMeta(
                "family_member_name",
                getter("family-member/document-id/name"),
            ),
            ColumnMeta(
                "family_member_date",
                getter("family-member/document-id/date"),
            ),
            ColumnMeta(
                "text",
                getter("priority-application/text"),
            ),
        ],
    ),
]


class Uspto(DataSource):
    """
    Create an object containing United States Patent and Trademark Office
    (USPTO) meta-data that supports queries over its (virtual) tables and the
    population of an SQLite database with its data.

    :param uspto_directory: The directory path where the USPTO
        data files are located
    :type uspto_directory: str

    :param sample: A callable to control Zip file and container sampling.
        It defaults to `lambda x: True`. The population or query method
        will call this with a tuple as its argument, where the first value
        is a designator string that can be either "path" or "container" and
        the second value can be an USPTO Zip file path or a container respectively.
        (e.g. sample(("path", "path/to/ipgb20221025_wk43.zip")) or
        self.sample(("container", patent_content)).
        A container represents a patent and its sampling occurs on the USPTO
        zip cache file, during the reading of the Zip file paths.
        Perform different sampling functionalities by passing a lambda expression.
        The expression can use a variable named data to access the tuple values.
        (e.g For sampling the last USPTO files of each year:
        `lambda data: data[1].endswith("wk52.zip") if data[0] == "path" else True.
        For passing all the Zip file paths and sampling all the patents that
        have the word "exercise" in them:
        `True if data[0] == ""path"" else  (True if (""exercise"" in data[1]) else False)`
        )
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
        uspto_directory,
        sample=lambda n: True,
        attach_databases=None,
    ):
        super().__init__(
            VTSource(uspto_directory, sample),
            tables,
            attach_databases,
        )
