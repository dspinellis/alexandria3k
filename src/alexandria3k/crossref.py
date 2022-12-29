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
"""Virtual database table access of Crossref data"""

import abc
import csv
import os
import sqlite3

# pylint: disable-next=import-error
import apsw

from .common import add_columns, fail, log_sql, set_fast_writing
from . import debug
from . import perf
from .tsort import tsort
from .virtual_db import (
    ColumnMeta,
    TableMeta,
    CONTAINER_ID_COLUMN,
    FilesCursor,
    ROWID_INDEX,
)


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

    def get_file_id_iterator(self):
        """Return an iterator over the int identifiers of all data files"""
        return range(0, len(self.data_files))

    def get_file_name_by_id(self, fid):
        """Return the name of the file corresponding to the specified fid"""
        return self.data_files[fid]


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


class Source:
    """Virtual table data source.  This gets registered with the apsw
    Connection through createmodule in order to instantiate the virtual
    tables."""

    def __init__(self, table_dict, data_directory, sample):
        self.data_files = DataFiles(data_directory, sample)
        self.table_dict = table_dict

    def Create(self, _db, _module_name, _db_name, table_name):
        """Create the specified virtual table"""
        return self.table_dict[table_name].creation_tuple(
            self.table_dict, self.data_files.get_file_array()
        )

    Connect = Create

    def get_file_id_iterator(self):
        """Return an iterator over the data files' identifiers"""
        return self.data_files.get_file_id_iterator()

    def get_file_name_by_id(self, fid):
        """Return the name of the file corresponding to the specified fid"""
        return self.data_files.get_file_name_by_id(fid)


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
        if col == -1:
            return self.Rowid()

        if col == 0:  # id
            return self.Rowid()

        if col == CONTAINER_ID_COLUMN:
            return self.container_id()

        extract_function = self.table.get_value_extractor_by_ordinal(col)
        return extract_function(self.current_row_value())

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

        extract_function = self.table.get_value_extractor_by_ordinal(col)
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


class ReferencesCursor(ElementsCursor):
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


class UpdatesCursor(ElementsCursor):
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


class SubjectsCursor(ElementsCursor):
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


class LicensesCursor(ElementsCursor):
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


class LinksCursor(ElementsCursor):
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


class FundersCursor(ElementsCursor):
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


class AffiliationsCursor(ElementsCursor):
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


class AwardsCursor(ElementsCursor):
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

crossref_table_dict = {t.get_name(): t for t in tables}


def get_table_meta_by_name(name):
    """Return the metadata of the specified table"""
    try:
        return crossref_table_dict[name]
    except KeyError:
        fail(f"Unknown table name: '{name}'.")
        # NOTREACHED
        return None


def tables_transitive_closure(table_list, top):
    """Return the transitive closure of all named tables
    with all the ones required to reach the specified top
    """
    result = set([top])
    for table_name in table_list:
        while table_name not in result:
            result.add(table_name)
            table = get_table_meta_by_name(table_name)
            table_name = table.get_parent_name()
    return result


class IndexManager:
    """Create database indexes, avoiding duplication, and allowing
    them to be dropped."""

    def __init__(self, db):
        self.db = db
        self.indexes = set()

    def create_index(self, table, column):
        """Create an index on the specified table and column, if required"""
        if table == "temp_works":
            table = "temp_matched"
        index = (table, column)
        if index in self.indexes:
            return

        self.db.execute(
            log_sql(
                f"""CREATE INDEX {table}_{column}_idx ON {table}({column})"""
            )
        )
        self.indexes.add((table, column))

    def drop_indexes(self):
        """Drop all created indexes"""
        for (table, column) in self.indexes:
            self.db.execute(log_sql(f"DROP INDEX {table}_{column}_idx"))
        self.indexes.clear()


class Crossref:
    """Create a Crossref meta-data object that support queries over its
    (virtual) table and the population of an SQLite database with its
    data"""

    def __init__(self, crossref_directory, sample=lambda n: True):
        # A named in-memory database; it can be attached by name to others
        self.vdb = apsw.Connection(
            "file:virtual?mode=memory&cache=shared",
            apsw.SQLITE_OPEN_URI | apsw.SQLITE_OPEN_READWRITE,
        )
        self.cursor = self.vdb.cursor()
        # Register the module as filesource
        self.data_source = Source(
            crossref_table_dict, crossref_directory, sample
        )
        self.vdb.createmodule("filesource", self.data_source)

        # Dictionaries of tables containing a set of columns required
        # for querying or populating the database
        self.query_columns = {}
        self.population_columns = {}
        self.query_and_population_columns = {}
        self.index_manager = None

        for table in tables:
            self.vdb.execute(
                log_sql(
                    f"CREATE VIRTUAL TABLE {table.get_name()} USING filesource()"
                )
            )

    def get_virtual_db(self):
        """Return the virtual table database as an apsw object"""
        return self.vdb

    @staticmethod
    def add_column(dictionary, table, column):
        """Add a column required for executing a query to the
        specified dictionary"""
        if table in dictionary:
            dictionary[table].add(column)
        else:
            dictionary[table] = {column}

    def set_query_columns(self, query):
        """Set the columns a query requires to run as a set in
        self.query_columns by invoking the tracer"""

        def trace_query_columns(query):
            """Set the columns a query requires to run as a set in
            self.query_columns.
            See https://rogerbinns.github.io/apsw/tips.html#parsing-sql"""

            def authorizer(op_code, table, column, _database, _trigger):
                """Query authorizer to monitor used columns"""
                if op_code == apsw.SQLITE_READ and column:
                    # print(f"AUTH: adding {table}.{column}")
                    Crossref.add_column(self.query_columns, table, column)
                return apsw.SQLITE_OK

            def tracer(_cursor, _query, _bindings):
                """An execution tracer that denies the query's operation"""
                # Abort the query's evaluation with an exception.  Returning
                # apsw.SQLITE_DENY seems to be doing something that takes
                # minutes to finish
                return None

            # Add the columns required by the actual query
            self.cursor.setexectrace(tracer)
            self.vdb.setauthorizer(authorizer)
            self.cursor.execute(log_sql(query), can_cache=False)
            # NOTREACHED

        try:
            trace_query_columns(query)
        except apsw.ExecTraceAbort:
            pass
        self.vdb.setauthorizer(None)
        self.cursor.setexectrace(None)

    def query(self, query, partition=False):
        """Run the specified query on the virtual database.
        Returns an iterable over the query's results.
        Queries involving table joins will run substantially faster
        if access to each table's records is restricted with
        an expression `table_name.container_id = CONTAINER_ID`, and
        the `partition` argument is set to true.
        In such a case the query is repeatedly run over each database
        partition (compressed JSON file) with `CONTAINER_ID` iterating
        sequentially to cover all partitions.
        The query's result is the concatenation of the individal partition
        results.
        Running queries with joins without partitioning will often result
        in quadratic (or worse) algorithmic complexity."""

        self.cursor = self.vdb.cursor()

        # Easy case
        if not partition:
            for row in self.cursor.execute(log_sql(query)):
                yield row
            return

        # Even when restricting multiple JOINs with container_id
        # SQLite seems to scan all containers for each JOIN making the
        # performance intolerably slow. Address this by creating non-virtual
        # tables with the required columns for each partition, as follows.
        #
        # Identify required tables and columns
        # Create an in-memory database
        # Attach database partition to in-memory database
        # For each partition:
        #   Copy tables to in-memory database
        #   Run query on in-memory database
        #   drop tables
        self.set_query_columns(query)
        partition = apsw.Connection(
            "file:partition?mode=memory&cache=shared",
            apsw.SQLITE_OPEN_URI | apsw.SQLITE_OPEN_READWRITE,
        )
        partition.createmodule("filesource", self.data_source)
        partition.execute(
            log_sql(
                "ATTACH DATABASE 'file:virtual?mode=memory&cache=shared' AS virtual"
            )
        )
        for i in self.data_source.get_file_id_iterator():
            debug.log(
                "progress",
                f"Container {i} {self.data_source.get_file_name_by_id(i)}",
            )
            for (table_name, table_columns) in self.query_columns.items():
                columns = ", ".join(table_columns)
                partition.execute(
                    log_sql(
                        f"""CREATE TABLE {table_name}
                  AS SELECT {columns} FROM virtual.{table_name}
                    WHERE virtual.{table_name}.container_id={i}"""
                    )
                )
            self.cursor = partition.cursor()
            for row in self.cursor.execute(log_sql(query)):
                yield row
            for table_name in self.query_columns:
                partition.execute(log_sql(f"DROP TABLE {table_name}"))

    def get_query_column_names(self):
        """Return the column names associated with an executing query"""
        return [description[0] for description in self.cursor.description]

    def populate(self, database_path, columns=None, condition=None):
        """Populate the specified SQLite database.
        The database is created if it does not exist.
        If it exists, the populated tables are dropped
        (if they exist) and recreated anew as specified.

        columns is an array containing strings of
        table_name.column_name or table_name.*

        conditions is a dictionary of table_name to condition

        The condition is an
        [SQL expression](https://www.sqlite.org/syntax/expr.html)
        containing references to the table's columns.
        It can also contain references to populated tables, by prefixing
        the column name with `populated.`.
        Implicitly, if a main table is populated, its detail tables
        will only get populated with the records associated with the
        correspoing main table.

        indexes is an array of table_name(indexed_column...)  strings,
        that specifies indexes to be created before populating the tables.
        The indexes can be used to speed up the evaluation of the population
        conditions.
        Note that foreign key indexes will always be created and need
        not be specified.
        """

        # pylint: disable=too-many-statements
        def set_join_columns():
            """Add columns required for joins"""
            to_add = []
            for table_name in query_and_population_tables():
                while table_name:
                    table = get_table_meta_by_name(table_name)
                    parent_table_name = table.get_parent_name()
                    primary_key = table.get_primary_key()
                    foreign_key = table.get_foreign_key()
                    if foreign_key:
                        to_add.append((table_name, foreign_key))
                    if parent_table_name and primary_key:
                        to_add.append((parent_table_name, primary_key))
                    table_name = parent_table_name
            # print("ADD COLUMNS ", to_add)
            for (table, column) in to_add:
                Crossref.add_column(
                    self.query_and_population_columns, table, column
                )

        def query_and_population_tables():
            """Return a sequence consisting of the tables required
            for populating and querying the data"""
            return set.union(
                set(self.population_columns.keys()),
                set(self.query_columns.keys()),
            )

        def joined_tables(table_names, rename_temp):
            """Return JOIN statements for all specified tables.
            If rename_temp is True, temporary tables are renamed to
            their virtual names (e.g. temp_workers becomes workers).
            This change provides a context for evaluating user-specified
            queries."""
            result = ""
            tables_meta = [get_table_meta_by_name(t) for t in table_names]
            sorted_tables = tsort(tables_meta, table_names)
            debug.log("sorted-tables", sorted_tables)
            for table_name in sorted_tables:
                if table_name == "works":
                    continue
                table = get_table_meta_by_name(table_name)
                parent_table_name = table.get_parent_name()
                primary_key = table.get_primary_key()
                foreign_key = table.get_foreign_key()
                if rename_temp:
                    rename = f"AS {table_name}"
                    primary_table_name = parent_table_name
                    foreign_table_name = table_name
                else:
                    rename = ""
                    primary_table_name = f"temp_{parent_table_name}"
                    foreign_table_name = f"temp_{table_name}"
                result += f""" INNER JOIN temp_{table_name} {rename} ON
                    {primary_table_name}.{primary_key}
                      = {foreign_table_name}.{foreign_key}"""
                if not rename_temp:
                    self.index_manager.create_index(
                        f"temp_{parent_table_name}", primary_key
                    )
                    self.index_manager.create_index(
                        f"temp_{table_name}", foreign_key
                    )
            return result

        def populate_table(table, partition_index, condition):
            """Populate the specified table"""

            columns = ", ".join(
                [f"{table}.{col}" for col in self.population_columns[table]]
            )

            if condition:
                path = tables_transitive_closure([table], "works")

                # One would think that an index on rowid is implied, but
                # removing it increases the time required to process
                # 3581.json.gz from the April 2022 dataset from 6.5"
                # to 18.4".
                self.index_manager.create_index(f"temp_{table}", "rowid")

                # Putting AND in the JOIN condition, rather than WHERE
                # improves dramatically the execution's performance time
                exists = f"""AND EXISTS (SELECT 1
                  FROM temp_matched AS temp_works
                  {joined_tables(path, False)}
                  {"AND" if len(path) > 1 else "WHERE"}
                    {table}.rowid = temp_{table}.rowid)"""
            else:
                exists = ""

            statement = f"""
                INSERT INTO populated.{table}
                    SELECT {columns} FROM {table}
                    WHERE {table}.container_id = {partition_index} {exists}
                """
            self.vdb.execute(log_sql(statement))
            perf.log(f"Populate {table}")

        def create_database_schema(columns):
            """Create the populated database, if needed"""
            if not os.path.exists(database_path):
                pdb = sqlite3.connect(database_path)
                pdb.close()

            self.vdb.execute(
                log_sql(f"ATTACH DATABASE '{database_path}' AS populated")
            )
            set_fast_writing(self.vdb)

            self.index_manager = IndexManager(self.vdb)

            add_columns(
                columns,
                tables,
                lambda table, column: Crossref.add_column(
                    self.population_columns, table, column
                ),
            )

            # Setup the columns required for executing the query
            if condition:
                table_names = ", ".join(crossref_table_dict.keys())
                query = f"""SELECT DISTINCT 1 FROM {table_names} WHERE {condition}"""
                self.set_query_columns(query)
                set_join_columns()
                perf.log("Condition parsing")

            # Create empty tables
            for (table_name, table_columns) in self.population_columns.items():
                table = get_table_meta_by_name(table_name)
                self.vdb.execute(
                    log_sql(f"DROP TABLE IF EXISTS populated.{table_name}")
                )
                self.vdb.execute(
                    log_sql(table.table_schema("populated.", table_columns))
                )
            perf.log("Table creation")

        def create_matched_tables():
            """Create copies of the virtual tables for fast access"""
            query_table_names = tables_transitive_closure(
                self.query_columns.keys(), "works"
            )

            for table in query_and_population_tables():
                columns = self.query_and_population_columns.get(table)
                if columns:
                    columns = set.union(columns, {"rowid"})
                else:
                    columns = {"rowid"}

                # Add query columns
                query_columns_of_table = self.query_columns.get(table)
                if query_columns_of_table:
                    columns = set.union(columns, query_columns_of_table)

                column_list = ", ".join(columns)
                self.vdb.execute(
                    log_sql(f"""DROP TABLE IF EXISTS temp_{table}""")
                )
                create = f"""CREATE TEMP TABLE temp_{table} AS
                    SELECT {column_list} FROM {table}
                    WHERE container_id = {i}"""
                self.vdb.execute(log_sql(create))
            perf.log("Virtual table copies")

            # Create a table containing the work ids for all works
            # matching the query, which is executed in a context
            # containing all required tables.
            create = (
                """CREATE TEMP TABLE temp_matched AS
                        SELECT works.id, works.rowid
                        FROM temp_works AS works """
                + joined_tables(query_table_names, True)
                + f" WHERE ({condition})"
            )
            self.vdb.execute(log_sql("DROP TABLE IF EXISTS temp_matched"))
            self.vdb.execute(log_sql(create))

            if debug.enabled("dump-matched"):
                csv_writer = csv.writer(debug.get_output(), delimiter="\t")
                for rec in self.vdb.execute("SELECT * FROM temp_matched"):
                    csv_writer.writerow(rec)

            perf.log("Matched table creation")

        create_database_schema(columns)
        # Populate all tables from the records of each file in sequence.
        # This improves the locality of reference and through the constraint
        # indexing and the file cache avoids opening, reading, decompressing,
        # and parsing each file multiple times.
        for i in self.data_source.get_file_id_iterator():
            debug.log(
                "progress",
                f"Container {i} {self.data_source.get_file_name_by_id(i)}",
            )

            if condition:
                create_matched_tables()

            for table in self.population_columns:
                populate_table(table, i, condition)
            self.index_manager.drop_indexes()
        perf.log("Table population")

        self.vdb.execute(log_sql("DETACH populated"))
        self.vdb.close()
