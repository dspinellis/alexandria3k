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

from alexandria3k.data_source import (
    CONTAINER_INDEX,
    ROWID_INDEX,
    DataSource,
    ElementsCursor,
    StreamingCachedContainerTable,
    ItemsCursor,
)

from alexandria3k.xml import agetter, all_getter, getter
from alexandria3k.file_xml_cache import get_file_cache
from alexandria3k.uspto_zip_cache import get_zip_cache
from alexandria3k.db_schema import ColumnMeta, TableMeta


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
        # TODO: Add sampling.
        # Collect the names of all available data files
        self.file_path = []
        self.unique_patent_xml_files = []
        self.file_directory = directory
        self.filename = None
        self.file_id = 0
        self.container_id = -1
        self.zip_path = None

        # Read through the directory
        for file_name in os.listdir(self.file_directory):
            path = os.path.join(self.file_directory, file_name)
            if not os.path.isfile(path):
                continue

            self.file_path.append(path)

    def get_zip_contents(self, path):
        """Return the a list of all the patent inside the Zip."""
        # Reading Zip file.
        return get_zip_cache().read(path)

    def get_xml_chunk(self, container_id):
        """Return a XML chunk using the container_id."""
        patent_xml = self.unique_patent_xml_files[container_id]

        return patent_xml

    def zip_generator(self):
        """A generator function iterating over the Zip files and the
        containers inside."""
        # pylint: disable-next=consider-using-with
        for path in self.file_path:
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
        self.zip_path = self.file_path[zip_file_id]
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
        return len(self.file_path)

    def get_container_iterator(self):
        """Return an iterator over the int identifiers of all chunks XML data files"""
        return self.zip_generator()

    def get_container_name(self, fid):
        """Return the name of the file."""
        return self.filename


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
        self.xml_contents = get_zip_cache().read(self.current_file_path)

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
                    self.current_file_path
                )
            else:
                # Returns when all Zip files have been read.
                self.eof = True
                return

        # Container parsing.
        self.items = get_file_cache().read(
            self.xml_contents[self.container_id], self.container_id
        )
        self.eof = False
        # The single container has been read. Set EOF in next Next call
        self.file_read = True

    def get_container_id(self):
        """Get the container id of the XML chunk."""
        return self.container_id


class PatentsElementsCursor(ElementsCursor):
    """A cursor over USPTO items. It depends on the
    extract multiple table property. Gets all the elements
    below a patent and then iterates over them."""

    def __init__(self, table, parent_cursor):
        """Not part of the apsw VTCursor interface.
        The table agument is a StreamingTable object"""
        super().__init__(table, parent_cursor)
        self.extract_multiple = table.get_table_meta().get_extract_multiple()

    def Next(self):
        """Advance to the next element."""
        while True:
            # End of File of patent cursor.
            if self.parent_cursor.Eof():
                self.eof = True
                return
            if not self.elements:
                # Gets elements of parent patent.
                self.elements = self.extract_multiple(
                    self.parent_cursor.current_row_value()
                )
                self.element_index = -1
            if not self.elements:
                # If parent has no element moves to the next patent.
                self.parent_cursor.Next()
                self.elements = None
                continue
            if self.element_index + 1 < len(self.elements):
                # Moves to the next element if it exists.
                self.element_index += 1
                self.eof = False
                return
            self.parent_cursor.Next()
            self.elements = None

    def Rowid(self):
        """Return a unique id of the row along all records"""
        return self.parent_cursor.Rowid()


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


class PatentsIpcrCurcor(PatentsElementsCursor):
    """A cursor over any of a patent's details data."""

    def __init__(self, table, parent_cursor):
        """Not part of the apsw VTCursor interface.
        The table agument is a StreamingTable object"""
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

        if col == 1:
            return self.parent_cursor.get_container_id()

        if col == 2:
            return self.parent_cursor.get_container_id()

        return super().Column(col)


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
                "type",
                agetter(
                    "appl-type",
                    "us-bibliographic-data-grant/application-reference",
                ),
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
                "microform_number",
                getter("lang"),
                description="UNCOMPLETEDOptical microform appendix.",
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
                "hague_filing_date",
                getter(
                    "us-bibliographic-data-grant/hague-agreement-data/international-filing-date"
                ),
            ),
            ColumnMeta(
                "hague_reg_pub_date",
                getter(
                    "us-bibliographic-data-grant/hague-agreement-data/"
                    + "international-registration-publication-date"
                ),
            ),
            ColumnMeta(
                "hague_reg_date",
                getter(
                    "us-bibliographic-data-grant/hague-agreement-data/"
                    + "international-registration-publication-date"
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
                "sir_flag",
                agetter("sir-text", "us-bibliographic-data-grant/us-sir-flag"),
                description="Statutory invention registration flag.",
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
        "icpr_classifications",
        foreign_key="patent_id",
        parent_name="us_patents",
        primary_key="id",
        cursor_class=PatentsIpcrCurcor,
        extract_multiple=all_getter(
            "us-bibliographic-data-grant/classifications-ipcr/classification-ipcr"
        ),
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("patent_id"),
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
]


class Uspto(DataSource):
    """
    Create an object containing United States Patent and Trademark Office
    (USPTO) meta-data that supports queries over its (virtual) tables and the
    population of an SQLite database with its data.

    :param uspto_directory: The directory path where the USPTO
        data files are located
    :type uspto_directory: str

    # TODO: Add sampling.

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
