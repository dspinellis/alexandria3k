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
"""Crossref publication data"""

import abc
import os

from alexandria3k.data_source import (
    CONTAINER_INDEX,
    DataSource,
    ElementsCursor,
    ROWID_INDEX,
    StreamingCachedContainerTable,
)
from alexandria3k.file_cache import get_file_cache
from alexandria3k.db_schema import ColumnMeta, TableMeta


DEFAULT_SOURCE = None

# Method names coming from apsw start with uppercase
# pylint: disable=invalid-name
# pylint: disable=too-many-lines


class DataFiles:
    """The source of the compressed JSON data files"""

    def __init__(self, directory, sample_container):
        # Collect the names of all available data files
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

    def get_container_iterator(self):
        """Return an iterator over the int identifiers of all data files"""
        return range(0, len(self.data_files))

    def get_container_name(self, fid):
        """Return the name of the file corresponding to the specified fid"""
        return self.data_files[fid]


def dict_value(dictionary, key):
    """Return the value of dictionary for key or None if it doesn't exist"""
    if not dictionary:
        return None
    return dictionary.get(key)


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
    # Normalize by removing the dash
    return value[0].replace("-", "") if value else None


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


def normalized_doi(doi_string):
    """
    Return the string in lowercase with spaces removed and common HTML
    escapes replaced (or None if None is passed)
    """
    if not doi_string:
        return None
    normalized = doi_string.lower()
    if normalized.find(" ") != -1:
        # Some DOIs appear double, separated by a space
        parts = normalized.split(" ")
        if len(parts) == 2 and parts[0] == parts[1]:
            normalized = parts[0]
        else:
            normalized = normalized.replace(" ", "")
    if normalized.find("&") == -1:
        return normalized
    return (
        normalized.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&ndash;", "-")
        .replace("&#x003c;", "<")
        .replace("&#x003e;", ">")
        .replace("&#60;", "<")
        .replace("&#62;", ">")
    )


def lower_or_none(string):
    """Return the string in lowercase or None if None is passed"""
    return string.lower() if string else None


class VTSource:
    """Virtual table data source.  This gets registered with the apsw
    Connection through createmodule in order to instantiate the virtual
    tables."""

    def __init__(self, data_directory, sample):
        self.data_files = DataFiles(data_directory, sample)
        self.table_dict = {t.get_name(): t for t in tables}

    def Create(self, _db, _module_name, _db_name, table_name):
        """Create the specified virtual table
        Return the tuple required by the apsw.Source.Create method:
        the table's schema and the virtual table class."""
        table = self.table_dict[table_name]
        return table.table_schema(), StreamingCachedContainerTable(
            table, self.table_dict, self.data_files.get_file_array()
        )

    Connect = Create

    def get_container_iterator(self):
        """Return an iterator over the data files' identifiers"""
        return self.data_files.get_container_iterator()

    def get_container_name(self, fid):
        """Return the name of the file corresponding to the specified fid"""
        return self.data_files.get_container_name(fid)


class FilesCursor:
    """A cursor over the items data files. Internal use only.
    Not used directly by an SQLite table."""

    def __init__(self, table):
        """Not part of the apsw VTCursor interface.
        The table agument is a StreamingTable object"""
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
        # print(f"Filter n={index_number} c={constraint_args}")

        if index_number == 0:
            # No index; iterate through all the files
            self.file_index = -1
            self.single_file = False
        elif index_number & CONTAINER_INDEX:
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
        if self.file_index + 1 >= len(self.table.data_source):
            self.eof = True
            return
        self.file_index += 1
        self.items = get_file_cache().read(
            self.table.data_source[self.file_index]
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


class CrossrefElementsCursor(ElementsCursor):
    """A cursor over Crossref elements.  It depends on the implementation
    of the abstract method element_name."""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return

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


class WorksCursor(CrossrefElementsCursor):
    """A cursor over the works data."""

    def __init__(self, table):
        super().__init__(table, None)
        self.files_cursor = FilesCursor(table)
        # Initialized in Filter()
        self.item_index = None

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return None

    def Eof(self):
        """Return True when the end of the table's records has been reached."""
        return self.eof

    def Rowid(self):
        """Return a unique id of the row along all records"""
        # Allow for 16k items per file (currently 5k)
        return (self.files_cursor.Rowid() << 14) | (self.item_index)

    def current_row_value(self):
        """Return the current row. Not part of the apsw API."""
        return self.files_cursor.current_row_value()[self.item_index]

    def container_id(self):
        """Return the id of the container containing the data being fetched.
        Not part of the apsw API."""
        return self.files_cursor.Rowid()

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # id
            return self.Rowid()

        return super().Column(col)

    # pylint: disable=arguments-differ
    def Filter(self, index_number, index_name, constraint_args):
        """Always called first to initialize an iteration to the first row
        of the table according to the index"""
        self.files_cursor.Filter(index_number, index_name, constraint_args)
        self.eof = self.files_cursor.Eof()
        # print("FILTER", index_number, constraint_args)
        if index_number & ROWID_INDEX:
            # This has never happened, so this is untested
            self.item_index = constraint_args[1]
        else:
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


class AuthorsCursor(CrossrefElementsCursor):
    """A cursor over the items' authors data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "author"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 16k authors. There is a Physics paper with 5k
        authors."""
        return (self.parent_cursor.Rowid() << 14) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # id
            return self.record_id()

        if col == 2:  # work_id
            return self.parent_cursor.Rowid()

        return super().Column(col)


class ReferencesCursor(CrossrefElementsCursor):
    """A cursor over the items' references data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "reference"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 1M references"""
        return (self.parent_cursor.Rowid() << 20) | self.element_index

    def Column(self, col):
        if col == 0:  # work_id
            return self.parent_cursor.Rowid()
        return super().Column(col)


class UpdatesCursor(CrossrefElementsCursor):
    """A cursor over the items' updates data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "update-to"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 1M updates"""
        return (self.parent_cursor.Rowid() << 20) | self.element_index

    def Column(self, col):
        if col == 0:  # work_id
            return self.parent_cursor.Rowid()
        return super().Column(col)


class SubjectsCursor(CrossrefElementsCursor):
    """A cursor over the work items' subject data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "subject"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 1M subjects"""
        return (self.parent_cursor.Rowid() << 20) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # work_id
            return self.parent_cursor.Rowid()
        return super().Column(col)


class LicensesCursor(CrossrefElementsCursor):
    """A cursor over the work items' subject data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "license"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 1M links"""
        return (self.parent_cursor.Rowid() << 20) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # work_id
            return self.parent_cursor.Rowid()
        return super().Column(col)


class LinksCursor(CrossrefElementsCursor):
    """A cursor over the work items' subject data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "link"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 1M links"""
        return (self.parent_cursor.Rowid() << 20) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # work_id
            return self.parent_cursor.Rowid()
        return super().Column(col)


class FundersCursor(CrossrefElementsCursor):
    """A cursor over the work items' funder data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "funder"

    def Rowid(self):
        """Return a unique id of the row along all records
        This allows for 1k funders"""
        return (self.parent_cursor.Rowid() << 10) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # id
            return self.record_id()

        if col == 2:  # work_id
            return self.parent_cursor.Rowid()

        return super().Column(col)


class AffiliationsCursor(CrossrefElementsCursor):
    """A cursor over the authors' affiliation data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "affiliation"

    def Rowid(self):
        """Return a unique id of the row along all records
        This allows for 128 affiliations per author."""
        return (self.parent_cursor.Rowid() << 7) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # Author-id
            return self.parent_cursor.record_id()
        return super().Column(col)


class AwardsCursor(CrossrefElementsCursor):
    """A cursor over the authors' affiliation data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "award"

    def Rowid(self):
        """Return a unique id of the row along all records
        This allows for 1k awards per funder."""
        return (self.parent_cursor.Rowid() << 10) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # Funder-id
            return self.parent_cursor.record_id()
        return super().Column(col)


# The full schema is documented in
# https://api.crossref.org/swagger-ui/index.html
#
# In this relational view, by convention column 0 is the unique or foreign key,
# and column 1 the data's container
tables = [
    TableMeta(
        "works",
        cursor_class=WorksCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("doi", lambda row: dict_value(row, "DOI").lower()),
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
            ColumnMeta(
                "short_container_title",
                lambda row: tab_values(
                    dict_value(row, "short-container-title")
                ),
            ),
            ColumnMeta(
                "container_title",
                lambda row: tab_values(dict_value(row, "container-title")),
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
            # Columns to facilitate queries without requiring building
            # a references graph.
            ColumnMeta(
                "references_count",
                lambda row: dict_value(row, "references-count"),
            ),
            ColumnMeta(
                "is_referenced_by_count",
                lambda row: dict_value(row, "is-referenced-by-count"),
            ),
        ],
    ),
    TableMeta(
        "work_authors",
        foreign_key="work_id",
        parent_name="works",
        primary_key="id",
        cursor_class=AuthorsCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("work_id"),
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
        foreign_key="author_id",
        parent_name="work_authors",
        primary_key="id",
        cursor_class=AffiliationsCursor,
        columns=[
            ColumnMeta("author_id"),
            ColumnMeta("container_id"),
            ColumnMeta("name", lambda row: dict_value(row, "name")),
        ],
    ),
    TableMeta(
        "work_references",
        foreign_key="work_id",
        parent_name="works",
        primary_key="id",
        cursor_class=ReferencesCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
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
                "doi_asserted_by",
                lambda row: dict_value(row, "doi-asserted-by"),
            ),
            ColumnMeta(
                "first_page", lambda row: dict_value(row, "first-page")
            ),
            ColumnMeta("isbn", lambda row: dict_value(row, "isbn")),
            ColumnMeta(
                "doi", lambda row: normalized_doi(dict_value(row, "DOI"))
            ),
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
        foreign_key="work_id",
        parent_name="works",
        primary_key="id",
        cursor_class=UpdatesCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
            ColumnMeta("label", lambda row: dict_value(row, "label")),
            ColumnMeta(
                "doi", lambda row: lower_or_none(dict_value(row, "DOI"))
            ),
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
        foreign_key="work_id",
        parent_name="works",
        primary_key="id",
        cursor_class=SubjectsCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
            ColumnMeta("name", lambda row: row),
        ],
    ),
    TableMeta(
        "work_licenses",
        foreign_key="work_id",
        parent_name="works",
        primary_key="id",
        cursor_class=LicensesCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
            ColumnMeta("url", lambda row: dict_value(row, "URL")),
            ColumnMeta(
                "start_timestamp",
                lambda row: dict_value(dict_value(row, "start"), "timestamp"),
            ),
            ColumnMeta(
                "delay_in_days", lambda row: dict_value(row, "delay-in-days")
            ),
        ],
    ),
    TableMeta(
        "work_links",
        foreign_key="work_id",
        parent_name="works",
        primary_key="id",
        cursor_class=LinksCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
            ColumnMeta("url", lambda row: dict_value(row, "URL")),
            ColumnMeta(
                "content_type", lambda row: dict_value(row, "content-type")
            ),
        ],
    ),
    TableMeta(
        "work_funders",
        foreign_key="work_id",
        parent_name="works",
        primary_key="id",
        cursor_class=FundersCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("work_id"),
            ColumnMeta(
                "doi", lambda row: lower_or_none(dict_value(row, "DOI"))
            ),
            ColumnMeta("name", lambda row: dict_value(row, "name")),
        ],
    ),
    TableMeta(
        "funder_awards",
        foreign_key="funder_id",
        parent_name="work_funders",
        primary_key="id",
        cursor_class=AwardsCursor,
        columns=[
            ColumnMeta("funder_id"),
            ColumnMeta("container_id"),
            ColumnMeta("name", lambda row: row),
        ],
    ),
]


class Crossref(DataSource):
    """
    Create an object containing Crossref meta-data that supports queries over
    its (virtual) tables and the population of an SQLite database with its
    data.

    :param crossref_directory: The directory path where the Crossref
        data files are located
    :type crossref_directory: str

    :param sample: A callable to control container sampling, defaults
        to `lambda n: True`.
        The population or query method will call this argument
        for each Crossref container file with each container's file
        name as its argument.  When the callable returns `True` the
        container file will get processed, when it returns `False` the
        container will get skipped.
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
        crossref_directory,
        sample=lambda n: True,
        attach_databases=None,
    ):
        super().__init__(
            VTSource(crossref_directory, sample),
            tables,
            attach_databases,
        )
