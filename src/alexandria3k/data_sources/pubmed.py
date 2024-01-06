#
# Alexandria3k Pubmed bibliographic metadata processing
# Copyright (C) 2023 Bas Verlooy
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
"""Pubmed publication data"""

from alexandria3k.data_source import (
    ROWID_INDEX,
    DataFiles,
    DataSource,
    ElementsCursor,
    FilesCursor,
    StreamingCachedContainerTable,
)
from alexandria3k.db_schema import ColumnMeta, TableMeta
from alexandria3k.file_pubmed_cache import get_file_cache
from alexandria3k.xml import agetter, getter, getter_by_attribute, lower

# Method names coming from apsw start with uppercase
# pylint: disable=invalid-name

DEFAULT_SOURCE = None


class ArticlesElementsCursor(ElementsCursor):
    """A cursor over Pubmed items. Gets all the articles
    inside an xml file and then iterates over them."""

    def Next(self):
        """Advance to the next element."""
        while True:
            # End of File of article cursor.
            if self.parent_cursor.Eof():
                self.eof = True
                return
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


class ArticlesCursor(ArticlesElementsCursor):
    """Cursor over Pubmed articles"""

    def __init__(self, table):
        """Not part of the apsw VTCursor interface.
        The table argument is a StreamingTable object"""
        super().__init__(table, None)
        self.files_cursor = FilesCursor(table, get_file_cache)

    def Rowid(self):
        """Return a unique id of the row along all records"""
        # Allow for 16k items per file
        return (self.files_cursor.Rowid() << 14) | (self.element_index)

    # pylint: disable=arguments-differ
    def Filter(self, index_number, _index_name, constraint_args):
        """Always called first to initialize an iteration to the first row
        of the table according to the index"""
        self.files_cursor.Filter(index_number, _index_name, constraint_args)
        self.eof = self.files_cursor.Eof()
        if index_number & ROWID_INDEX:
            # This has never happened, so this is untested
            self.element_index = constraint_args[1]
        else:
            self.element_index = 0

    def Next(self):
        """Advance to the next item."""
        self.element_index += 1
        if self.element_index >= len(self.files_cursor.items):
            self.element_index = 0
            self.files_cursor.Next()
            self.eof = self.files_cursor.eof

    def current_row_value(self):
        """Return the current row. Not part of the apsw API."""
        return self.files_cursor.current_row_value()[self.element_index]

    def Close(self):
        """Cursor's destructor, used for cleanup"""
        self.files_cursor.Close()

    def container_id(self):
        """Return the id of the container containing the data being fetched.
        Not part of the apsw API."""
        return self.files_cursor.Rowid()


class VTSource:
    """Virtual table data source. This gets registered with the apsw
    Connection through createmodule in order to instantiate the virtual
    tables."""

    def __init__(self, data_directory, sample):
        self.data_files = DataFiles(data_directory, sample, ".gz")
        self.table_dict = {t.get_name(): t for t in tables}
        self.sample = sample

    def Create(self, _db, _module_name, _db_name, table_name):
        """Create a virtual table with the specified name"""
        table = self.table_dict[table_name]

        return table.table_schema(), StreamingCachedContainerTable(
            table,
            self.table_dict,
            self.data_files.get_file_array(),
            self.sample,
        )

    Connect = Create

    def get_container_iterator(self):
        """Return an iterator over the data files identifiers"""
        return self.data_files.get_container_iterator()

    def get_container_name(self, fid):
        """Return the name of the file corresponding to the specified fid"""
        return self.data_files.get_container_name(fid)


# https://www.nlm.nih.gov/bsd/mms/medlineelements.html lists all abbreviations
tables = [
    TableMeta(
        "pubmed_articles",
        columns=[
            ColumnMeta("id", getter("MedlineCitation/PMID")),
            ColumnMeta("container_id"),
            ColumnMeta(
                "doi",
                lower(
                    getter_by_attribute(
                        "IdType", "doi", "PubmedData/ArticleIdList/ArticleId"
                    )
                ),
            ),
            ColumnMeta(
                "publisher_item_identifier_article_id",
                getter_by_attribute(
                    "IdType", "pii", "PubmedData/ArticleIdList/ArticleId"
                ),
                description="Publisher item identifier (pii)",
            ),
            ColumnMeta(
                "pmc_article_id",
                getter_by_attribute(
                    "IdType", "pmc", "PubmedData/ArticleIdList/ArticleId"
                ),
                description="PubMed Central article identifier (pmc)",
            ),
            ColumnMeta(
                "journal_title",
                getter("MedlineCitation/Article/Journal/Title"),
                description="Journal title",
            ),
            ColumnMeta(
                "journal_issn",
                getter("MedlineCitation/Article/Journal/ISSN"),
                description="Journal ISSN",
            ),
            ColumnMeta(
                "journal_volume",
                getter("MedlineCitation/Article/Journal/JournalIssue/Volume"),
                description="Journal volume",
            ),
            ColumnMeta(
                "journal_issue",
                getter("MedlineCitation/Article/Journal/JournalIssue/Issue"),
                description="Journal issue",
            ),
            ColumnMeta(
                "journal_year",
                getter(
                    "MedlineCitation/Article/Journal/JournalIssue/PubDate/Year"
                ),
                description="Journal year",
            ),
            ColumnMeta(
                "journal_month",
                getter(
                    "MedlineCitation/Article/Journal/JournalIssue/PubDate/Month"
                ),
                description="Journal month",
            ),
            ColumnMeta(
                "journal_day",
                getter(
                    "MedlineCitation/Article/Journal/JournalIssue/PubDate/Day"
                ),
                description="Journal day",
            ),
            ColumnMeta(
                "journal_ISO_abbreviation",
                getter("MedlineCitation/Article/Journal/IsoAbbreviation"),
                description="Journal ISO abbreviation",
            ),
            ColumnMeta(
                "pagination",
                getter("MedlineCitation/Article/Pagination/MedlinePgn"),
                description="Pagination",
            ),
            ColumnMeta(
                "language",
                getter("MedlineCitation/Article/Language"),
                description="Language",
            ),
            ColumnMeta(
                "title", getter("MedlineCitation/Article/ArticleTitle")
            ),
            ColumnMeta(
                "country",
                getter("MedlineCitation/MedlineJournalInfo/Country"),
            ),
            ColumnMeta(
                "medline_ta",
                getter("MedlineCitation/MedlineJournalInfo/MedlineTA"),
                description="Journal title abbreviation",
            ),
            ColumnMeta(
                "nlm_unique_id",
                getter("MedlineCitation/MedlineJournalInfo/NlmUniqueID"),
                description="National Library of Medicine unique identifier",
            ),
            ColumnMeta(
                "issn_linking",
                getter("MedlineCitation/MedlineJournalInfo/ISSNLinking"),
            ),
            ColumnMeta(
                "article_pubmodel",
                agetter("PubModel", "MedlineCitation/Article"),
                description="Article publication method",
            ),
            ColumnMeta(
                "citation_subset",
                getter("MedlineCitation/CitationSubset"),
                description="Citation subset",
            ),
            ColumnMeta(
                "completed_year",
                getter("MedlineCitation/DateCompleted/Year"),
            ),
            ColumnMeta(
                "completed_month",
                getter("MedlineCitation/DateCompleted/Month"),
            ),
            ColumnMeta(
                "completed_day",
                getter("MedlineCitation/DateCompleted/Day"),
            ),
            ColumnMeta(
                "revised_year",
                getter("MedlineCitation/DateRevised/Year"),
                data_type="INTEGER",
            ),
            ColumnMeta(
                "revised_month",
                getter("MedlineCitation/DateRevised/Month"),
            ),
            ColumnMeta(
                "revised_day",
                getter("MedlineCitation/DateRevised/Day"),
            ),
        ],
        cursor_class=ArticlesCursor,
    )
]


class Pubmed(DataSource):
    """
    Create an object containing PubMed meta-data that supports queries
    over its (virtual) tables and the population of an SQLite database with its data.

    :param directory: The directory path where the PubMed data files are located
    :type directory: str

    :param sample: A callable to control container sampling, defaults
        to `lambda n: True`.
        The population or query method will call this argument
        for each Pubmed container file with each container's file
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
        self, directory, sample=lambda n: True, attach_databases=None
    ):
        super().__init__(VTSource(directory, sample), tables, attach_databases)
