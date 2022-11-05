#
# Alexandria2k Crossref bibliographic metadata processing
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
"""Virtual database table access of Crossref data"""

import abc
import os

import apsw

from file_cache import get_file_cache


class DataFiles:
    """The source of the compressed JSON data files"""

    def __init__(self, directory, sample_container=lambda path: True):
        self.data_files = []
        counter = 1
        for file_name in os.listdir(directory):
            path = os.path.join(directory, file_name)
            if not os.path.isfile(path):
                continue
            if not sample_container(path):
                continue
            counter += 1
            self.data_files.append(path)

    def get_file_array(self):
        """Return the array of data files"""
        return self.data_files

    def get_file_id_iterator(self):
        """Return an iterator over the int identifiers of all data files"""
        return range(0, len(self.data_files))


def dict_value(dictionary, key):
    """Return the value of dictionary for key or None if it doesn't exist"""
    if not dictionary:
        return None
    try:
        return dictionary[key]
    except KeyError:
        return None


def array_value(array, index):
    """Return the value of array at index or None if it doesn't exist"""
    try:
        return array[index]
    except (IndexError, TypeError):
        return None


def author_orcid(row):
    """Return the ISNI part of an ORCID URL or None if missing"""
    orcid = row.get("ORCID")
    if orcid:
        return orcid[17:]
    return None


def boolean_value(dictionary, key):
    """Return 0, 1, or None for the corresponding JSON value for key k
    of dict d"""
    if not dictionary:
        return None
    try:
        value = dictionary[key]
    except KeyError:
        return None
    if value:
        return 1
    return 0


def issn_value(dictionary, issn_type):
    """Return the ISSN of the specified type from a row that may contain
    an issn-type entry"""
    if not dictionary:
        return None
    try:
        # Array of entries like { "type": "electronic" , "value": "1756-2848" }
        type_values = dictionary["issn-type"]
    except KeyError:
        return None
    value = [tv["value"] for tv in type_values if tv["type"] == issn_type]
    return value[0] if value else None


def len_value(dictionary, key):
    """Return array length or None for the corresponding JSON value for key k
    of dict d"""
    if not dictionary:
        return None
    try:
        value = dictionary[key]
    except KeyError:
        return None
    return len(value)


def first_value(array):
    """Return the first element of array a or None if it doesn't exist"""
    return array_value(array, 0)


def tab_values(array):
    """Return the elements of array a separated by tab or None if it doesn't
    exist"""
    if not array:
        return None
    return "\t".join(array)


class TableMeta:
    """Meta-data of tables we maintain"""

    def __init__(self, name, parent_name, cursor_class, columns):
        self.name = name
        self.parent_name = parent_name
        self.columns = columns
        self.cursor_class = cursor_class

    def column_list(self):
        """Return a comma-separated list of a table's columns"""
        return ",".join([f"'{c.get_name()}'" for c in self.columns])

    def table_schema(self, prefix=""):
        """Return the SQL command to create a table's schema with the
        optional specified prefix."""
        return f"CREATE TABLE {prefix}{self.name}(" + self.column_list() + ")"

    def get_name(self):
        """Return the table's name"""
        return self.name

    def get_parent_name(self):
        """Return the name of the main table of which this has details"""
        return self.parent_name

    def get_cursor_class(self):
        """Return the table's specified cursor class"""
        return self.cursor_class

    def get_value_extractor(self, i):
        """Return the value extraction function for column at ordinal i"""
        return self.columns[i].get_value_extractor()

    def creation_tuple(self, data_files):
        """Return the tuple required by the apsw.Source.Create method"""
        return self.table_schema(), StreamingTable(self, data_files)


class ColumnMeta:
    """Meta-data of table columns we maintain"""

    def __init__(self, name, value_extractor):
        self.name = name
        self.value_extractor = value_extractor

    def get_name(self):
        """Return column's name"""
        return self.name

    def get_value_extractor(self):
        """Return the column's value extraction function"""
        return self.value_extractor


class Source:
    """Virtual table data source.  This gets registered with the Connection"""

    def __init__(self, data_directory):
        self.data_files = DataFiles(data_directory)

    def Create(self, _db, _module_name, _db_name, table_name):
        """Create the specified virtual table"""
        return table_dict[table_name].creation_tuple(
            self.data_files.get_file_array()
        )

    Connect = Create

    def get_file_id_iterator(self):
        """Return an iterator over the data files' identifiers"""
        return self.data_files.get_file_id_iterator()


# By convention column 1 of each table hold the container (file) id
# which is the index of the file in the files array
CONTAINER_ID_COLUMN = 1


class StreamingTable:
    """An apsw table streaming over data of the supplied table metadata"""

    def __init__(self, table_meta, data_files):
        self.table_meta = table_meta
        self.data_files = data_files

    def BestIndex(self, constraints, _orderbys):
        """Called by the Engine to determine the best available index
        for the operation at hand"""
        # print(f"BestIndex c={constraints} o={orderbys}")
        used_constraints = []
        found_index = False
        for (column, operation) in constraints:
            if (
                column == CONTAINER_ID_COLUMN
                and operation == apsw.SQLITE_INDEX_CONSTRAINT_EQ
            ):
                # Pass value to Filter as constraint_arg[0], and do not
                # require the engine to perform extra checks (exact match)
                used_constraints.append((0, False))
                found_index = True
            else:
                # No suitable index
                used_constraints.append(None)
        if found_index:
            return (
                used_constraints,
                1,  # index number
                None,  # index name
                False,  # results are not in orderbys order
                2000,  # about 2000 disk i/o (8M file / 4k block)
            )
        return None

    def Disconnect(self):
        """Called when a reference to a virtual table is no longer used"""

    Destroy = Disconnect

    def cursor(self, table_meta):
        """Return the cursor associated with this table.  The constructor
        for cursors embedded in others takes a parent cursor argument.  To
        handle this requirement, this method recursively calls itself until
        it reaches the top-level table."""
        cursor_class = table_meta.get_cursor_class()
        parent_name = table_meta.get_parent_name()
        if not parent_name:
            return cursor_class(self)
        parent = get_table_meta_by_name(parent_name)
        return cursor_class(self, self.cursor(parent))

    def Open(self):
        """Return the table's cursor object"""
        return self.cursor(self.table_meta)

    def get_value_extractor(self, column_ordinal):
        """Return the value extraction function for column at specified
        ordinal.  Not part of the apsw interface."""
        return self.table_meta.get_value_extractor(column_ordinal)


class FilesCursor:
    """A cursor over the items data files. Internal use only.
    Not used by a table."""

    def __init__(self, table):
        self.table = table
        self.eof = False
        # The following get initialized in Filter()
        self.file_index = None
        self.single_file = None
        self.file_read = None
        self.items = None

    def Filter(self, index_number, _index_name, constraint_args):
        """Always called first to initialize an iteration to the first
        (possibly constrained) row of the table"""
        # print(f"Filter c={constraint_args}")

        if index_number == 0:
            # No index; iterate through all the files
            self.file_index = -1
            self.single_file = False
        else:
            # Index; constraint reading through the specified file
            self.single_file = True
            self.file_read = False
            self.file_index = constraint_args[0] - 1
        self.Next()

    def Next(self):
        """Advance reading to the next available file. Files are assumed to be
        non-empty."""
        if self.single_file and self.file_read:
            self.eof = True
            return
        if self.file_index + 1 >= len(self.table.data_files):
            self.eof = True
            return
        self.file_index += 1
        self.items = get_file_cache().read(
            self.table.data_files[self.file_index]
        )
        self.eof = False
        # The single file has been read. Set EOF in next Next call
        self.file_read = True

    def Rowid(self):
        """Return a unique id of the row along all records"""
        return self.file_index

    def current_row_value(self):
        """Return the current row. Not part of the apsw API."""
        return self.items

    def Eof(self):
        """Return True when the end of the table's records has been reached."""
        return self.eof

    def Close(self):
        """Cursor's destructor, used for cleanup"""
        self.items = None


class WorksCursor:
    """A cursor over the works data."""

    def __init__(self, table):
        self.table = table
        self.files_cursor = FilesCursor(table)
        # Initialized in Filter()
        self.eof = None
        self.item_index = None

    def Eof(self):
        """Return True when the end of the table's records has been reached."""
        return self.eof

    def Rowid(self):
        """Return a unique id of the row along all records"""
        # Allow for 65k items per file (currently 5k)
        return (self.files_cursor.Rowid() << 16) | (self.item_index)

    def current_row_value(self):
        """Return the current row. Not part of the apsw API."""
        return self.files_cursor.current_row_value()[self.item_index]

    def container_id(self):
        """Return the id of the container containing the data being fetched.
        Not part of the apsw API."""
        return self.files_cursor.Rowid()

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == -1:
            return self.Rowid()

        if col == CONTAINER_ID_COLUMN:
            return self.container_id()

        extract_function = self.table.get_value_extractor(col)
        return extract_function(self.current_row_value())

    def Filter(self, *args):
        """Always called first to initialize an iteration to the first row
        of the table"""
        self.files_cursor.Filter(*args)
        self.eof = self.files_cursor.Eof()
        self.item_index = 0

    def Next(self):
        """Advance to the next item."""
        self.item_index += 1
        if self.item_index >= len(self.files_cursor.items):
            self.item_index = 0
            self.files_cursor.Next()
            self.eof = self.files_cursor.eof

    def Close(self):
        """Cursor's destructor, used for cleanup"""
        self.files_cursor.Close()


class ElementsCursor:
    """An (abstract) cursor over a collection of data embedded within
    another cursor."""

    __metaclass__ = abc.ABCMeta

    def __init__(self, table, parent_cursor):
        self.table = table
        self.parent_cursor = parent_cursor
        self.elements = None
        self.eof = None
        # Initialized in Filter()
        self.element_index = None

    @abc.abstractmethod
    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return

    def Filter(self, *args):
        """Always called first to initialize an iteration to the first row
        of the table"""
        self.parent_cursor.Filter(*args)
        self.elements = None
        self.Next()

    def Eof(self):
        """Return True when the end of the table's records has been reached."""
        return self.eof

    @abc.abstractmethod
    def Rowid(self):
        """Return a unique id of the row along all records"""
        return

    def record_id(self):
        """Return the record's identifier. Not part of the apsw API."""
        return self.Rowid()

    def current_row_value(self):
        """Return the current row. Not part of the apsw API."""
        return self.elements[self.element_index]

    def Next(self):
        """Advance reading to the next available element."""
        while True:
            if self.parent_cursor.Eof():
                self.eof = True
                return
            if not self.elements:
                self.elements = self.parent_cursor.current_row_value().get(
                    self.element_name()
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

    def container_id(self):
        """Return the id of the container containing the data being fetched.
        Not part of the apsw API."""
        return self.parent_cursor.container_id()

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == -1:
            return self.Rowid()

        if col == CONTAINER_ID_COLUMN:
            return self.container_id()

        extract_function = self.table.get_value_extractor(col)
        return extract_function(self.current_row_value())

    def Close(self):
        """Cursor's destructor, used for cleanup"""
        self.parent_cursor.Close()
        self.elements = None


class AuthorsCursor(ElementsCursor):
    """A cursor over the items' authors data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "author"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 65k authors. There is a Physics paper with 5k
        authors."""
        return (self.parent_cursor.Rowid() << 16) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # id
            return self.record_id()

        if col == 2:  # work_doi
            return self.parent_cursor.current_row_value().get("DOI")

        return super().Column(col)


class ReferencesCursor(ElementsCursor):
    """A cursor over the items' references data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "reference"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 16M references"""
        return (self.parent_cursor.Rowid() << 24) | self.element_index

    def Column(self, col):
        if col == 0:  # work_doi
            return self.parent_cursor.current_row_value().get("DOI")
        return super().Column(col)


class UpdatesCursor(ElementsCursor):
    """A cursor over the items' updates data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "update-to"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 16M updates"""
        return (self.parent_cursor.Rowid() << 24) | self.element_index

    def Column(self, col):
        if col == 0:  # work_doi
            return self.parent_cursor.current_row_value().get("DOI")
        return super().Column(col)


class SubjectsCursor(ElementsCursor):
    """A cursor over the work items' subject data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "subject"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 16M subjects"""
        return (self.parent_cursor.Rowid() << 24) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # work_doi
            return self.parent_cursor.current_row_value().get("DOI")
        return super().Column(col)


class FundersCursor(ElementsCursor):
    """A cursor over the work items' funder data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "funder"

    def Rowid(self):
        """Return a unique id of the row along all records
        This allows for 16M funders"""
        return (self.parent_cursor.Rowid() << 24) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # work_doi
            return self.parent_cursor.current_row_value().get("DOI")
        return super().Column(col)


class AffiliationsCursor(ElementsCursor):
    """A cursor over the authors' affiliation data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "affiliation"

    def Rowid(self):
        """Return a unique id of the row along all records
        This allows for 128 affiliations per author
        authors."""
        return (self.parent_cursor.Rowid() << 7) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # Author-id
            return self.parent_cursor.record_id()
        return super().Column(col)


# By convention column 0 is the unique or foreign key,
# and column 1 the data's container
tables = [
    TableMeta(
        "works",
        None,
        WorksCursor,
        [
            ColumnMeta("DOI", lambda row: dict_value(row, "DOI")),
            ColumnMeta("container_id", None),
            ColumnMeta(
                "title", lambda row: tab_values(dict_value(row, "title"))
            ),
            ColumnMeta(
                "published_year",
                lambda row: array_value(
                    first_value(
                        dict_value(dict_value(row, "published"), "date-parts")
                    ),
                    0,
                ),
            ),
            ColumnMeta(
                "published_month",
                lambda row: array_value(
                    first_value(
                        dict_value(dict_value(row, "published"), "date-parts")
                    ),
                    1,
                ),
            ),
            ColumnMeta(
                "published_day",
                lambda row: array_value(
                    first_value(
                        dict_value(dict_value(row, "published"), "date-parts")
                    ),
                    2,
                ),
            ),
            ColumnMeta("publisher", lambda row: dict_value(row, "publisher")),
            ColumnMeta("abstract", lambda row: dict_value(row, "abstract")),
            ColumnMeta("type", lambda row: dict_value(row, "type")),
            ColumnMeta("subtype", lambda row: dict_value(row, "subtype")),
            ColumnMeta("page", lambda row: dict_value(row, "page")),
            ColumnMeta("volume", lambda row: dict_value(row, "volume")),
            ColumnMeta(
                "article_number", lambda row: dict_value(row, "article-number")
            ),
            ColumnMeta(
                "journal_issue",
                lambda row: dict_value(
                    dict_value(row, "journal-issue"), "issue"
                ),
            ),
            ColumnMeta("issn_print", lambda row: issn_value(row, "print")),
            ColumnMeta(
                "issn_electronic", lambda row: issn_value(row, "electronic")
            ),
            # Synthetic column, which can be used for population filtering
            ColumnMeta(
                "update_count", lambda row: len_value(row, "update-to")
            ),
        ],
    ),
    TableMeta(
        "work_authors",
        "works",
        AuthorsCursor,
        [
            ColumnMeta("id", None),
            ColumnMeta("container_id", None),
            ColumnMeta("work_doi", None),
            ColumnMeta("orcid", author_orcid),
            ColumnMeta("suffix", lambda row: dict_value(row, "suffix")),
            ColumnMeta("given", lambda row: dict_value(row, "given")),
            ColumnMeta("family", lambda row: dict_value(row, "family")),
            ColumnMeta("name", lambda row: dict_value(row, "name")),
            ColumnMeta(
                "authenticated_orcid",
                lambda row: boolean_value(row, "authenticated-orcid"),
            ),
            ColumnMeta("prefix", lambda row: dict_value(row, "prefix")),
            ColumnMeta("sequence", lambda row: dict_value(row, "sequence")),
        ],
    ),
    TableMeta(
        "author_affiliations",
        "work_authors",
        AffiliationsCursor,
        [
            ColumnMeta("author_id", None),
            ColumnMeta("container_id", None),
            ColumnMeta("name", lambda row: dict_value(row, "name")),
        ],
    ),
    TableMeta(
        "work_references",
        "works",
        ReferencesCursor,
        [
            ColumnMeta("work_doi", None),
            ColumnMeta("container_id", None),
            ColumnMeta("issn", lambda row: dict_value(row, "issn")),
            ColumnMeta(
                "standards_body", lambda row: dict_value(row, "standards-body")
            ),
            ColumnMeta("issue", lambda row: dict_value(row, "issue")),
            ColumnMeta("key", lambda row: dict_value(row, "key")),
            ColumnMeta(
                "series_title", lambda row: dict_value(row, "series-title")
            ),
            ColumnMeta("isbn_type", lambda row: dict_value(row, "isbn-type")),
            ColumnMeta(
                "doi_asserted-by",
                lambda row: dict_value(row, "doi-asserted-by"),
            ),
            ColumnMeta(
                "first_page", lambda row: dict_value(row, "first-page")
            ),
            ColumnMeta("isbn", lambda row: dict_value(row, "isbn")),
            ColumnMeta("doi", lambda row: dict_value(row, "DOI")),
            ColumnMeta("component", lambda row: dict_value(row, "component")),
            ColumnMeta(
                "article_title", lambda row: dict_value(row, "article-title")
            ),
            ColumnMeta(
                "volume_title", lambda row: dict_value(row, "volume-title")
            ),
            ColumnMeta("volume", lambda row: dict_value(row, "volume")),
            ColumnMeta("author", lambda row: dict_value(row, "author")),
            ColumnMeta(
                "standard_designator",
                lambda row: dict_value(row, "standard-designator"),
            ),
            ColumnMeta("year", lambda row: dict_value(row, "year")),
            ColumnMeta(
                "unstructured", lambda row: dict_value(row, "unstructured")
            ),
            ColumnMeta("edition", lambda row: dict_value(row, "edition")),
            ColumnMeta(
                "journal_title", lambda row: dict_value(row, "journal-title")
            ),
            ColumnMeta("issn_type", lambda row: dict_value(row, "issn-type")),
        ],
    ),
    TableMeta(
        "work_updates",
        "works",
        UpdatesCursor,
        [
            ColumnMeta("work_doi", None),
            ColumnMeta("container_id", None),
            ColumnMeta("label", lambda row: dict_value(row, "label")),
            ColumnMeta("doi", lambda row: dict_value(row, "DOI")),
            ColumnMeta(
                "timestamp",
                lambda row: dict_value(
                    dict_value(row, "updated"), "timestamp"
                ),
            ),
        ],
    ),
    TableMeta(
        "work_subjects",
        "works",
        SubjectsCursor,
        [
            ColumnMeta("work_doi", None),
            ColumnMeta("container_id", None),
            ColumnMeta("name", lambda row: row),
        ],
    ),
    TableMeta(
        "work_funders",
        "works",
        FundersCursor,
        [
            ColumnMeta("work_doi", None),
            ColumnMeta("container_id", None),
            ColumnMeta("doi", lambda row: dict_value(row, "DOI")),
            ColumnMeta("name", lambda row: dict_value(row, "name")),
            ColumnMeta(
                "awards", lambda row: tab_values(dict_value(row, "award"))
            ),
        ],
    ),
]

table_dict = {t.get_name(): t for t in tables}


def get_table_meta_by_name(name):
    """Return the metadata of the specified table"""
    return table_dict[name]
