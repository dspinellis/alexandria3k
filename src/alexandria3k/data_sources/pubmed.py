#
# Alexandria3k PubMed bibliographic metadata processing
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
"""PubMed publication data"""

from alexandria3k.data_source import (
    CONTAINER_ID_COLUMN,
    ROWID_INDEX,
    DataFiles,
    DataSource,
    FilesCursor,
    StreamingCachedContainerTable,
)
from alexandria3k.db_schema import ColumnMeta, TableMeta
from alexandria3k.file_pubmed_cache import get_file_cache
from alexandria3k.xml import (
    XMLCursor,
    agetter,
    all_getter,
    get_root_text,
    getter,
    getter_by_attribute,
    lower,
)

# Method names coming from apsw start with uppercase
# pylint: disable=invalid-name
# pylint: disable=too-many-lines

DEFAULT_SOURCE = None

FILENAME_FORMAT = r"pubmed.*\.xml\.gz"


def author_identifier(func):
    """Return the ORCID identifier of the author,
    it might start with the URL, but sometimes it doesn't"""

    def orcid(tree):
        element = func(tree)
        if element is None:
            return None
        if element.startswith("https://orcid.org/"):
            return element[18:]
        return element

    return orcid


class ArticlesElementsCursor(XMLCursor):
    """A cursor over PubMed items. Gets all the elements
    inside an xml file and then iterates over them."""

    row_id_left_shift = None

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 16k authors. There is a Physics paper with 5k
        authors."""
        return (
            self.parent_cursor.Rowid() << self.row_id_left_shift
        ) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # id
            return self.record_id()
        if col == 1:
            return self.container_id()
        if col == 2:  # work_id
            return self.parent_cursor.Rowid()

        return super().Column(col)


class ArticlesCursor(ArticlesElementsCursor):
    """Cursor over PubMed articles"""

    row_id_left_shift = 18

    def __init__(self, table):
        """Not part of the apsw VTCursor interface.
        The table argument is a StreamingTable object"""
        super().__init__(table, None)
        self.files_cursor = FilesCursor(table, get_file_cache)

    def Rowid(self):
        """Return a unique id of the row along all records"""
        return (self.files_cursor.Rowid() << self.row_id_left_shift) | (
            self.element_index
        )

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

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:
            return self.Rowid()

        if col == CONTAINER_ID_COLUMN:
            return self.container_id()

        extract_function = self.table.get_value_extractor_by_ordinal(col)
        return extract_function(self.current_row_value())


class AuthorsCursor(ArticlesElementsCursor):
    """Cursor over PubMed authors"""

    row_id_left_shift = 14


class AffiliationCursor(ArticlesElementsCursor):
    """Cursor over PubMed author affiliations"""

    row_id_left_shift = 4


class InvestigatorsCursor(ArticlesElementsCursor):
    """Cursor over PubMed investigators"""

    row_id_left_shift = 10


class AbstractsCursor(ArticlesElementsCursor):
    """Cursor over PubMed abstracts"""

    row_id_left_shift = 14


class OtherAbstractsCursor(ArticlesElementsCursor):
    """Cursor over PubMed other abstracts"""

    row_id_left_shift = 14


class OtherAbstractTextsCursor(ArticlesElementsCursor):
    """Cursor over PubMed other abstract texts"""

    row_id_left_shift = 5


class HistoryCursor(ArticlesElementsCursor):
    """Cursor over PubMed history"""

    row_id_left_shift = 14


class ChemicalsCursor(ArticlesElementsCursor):
    """Cursor over PubMed chemicals"""

    row_id_left_shift = 14


class MeshHeadingsCursor(ArticlesElementsCursor):
    """Cursor over PubMed mesh headings"""

    row_id_left_shift = 14


class SupplementMeshsCursor(ArticlesElementsCursor):
    """Cursor over PubMed supplement meshs"""

    row_id_left_shift = 4


class CommentsCorrectionsCursor(ArticlesElementsCursor):
    """Cursor over PubMed comments corrections"""

    row_id_left_shift = 14


class KeywordsCursor(ArticlesElementsCursor):
    """Cursor over PubMed keywords"""

    row_id_left_shift = 14


class GrantsCursor(ArticlesElementsCursor):
    """Cursor over PubMed grants"""

    row_id_left_shift = 14


class DataBanksCursor(ArticlesElementsCursor):
    """Cursor over PubMed data banks"""

    row_id_left_shift = 10


class DataBankAccessionsCursor(ArticlesElementsCursor):
    """Cursor over PubMed data bank accessions"""

    row_id_left_shift = 5


class ReferencesCursor(ArticlesElementsCursor):
    """Cursor over PubMed references"""

    row_id_left_shift = 20


class ReferenceArticlesCursor(ArticlesElementsCursor):
    """Cursor over PubMed reference articles"""

    row_id_left_shift = 5


class PublicationTypeListCursor(ArticlesElementsCursor):
    """Cursor over PubMed publication type list"""

    row_id_left_shift = 20


class VTSource:
    """Virtual table data source. This gets registered with the apsw
    Connection through createmodule in order to instantiate the virtual
    tables."""

    def __init__(self, data_directory, sample):
        self.data_files = DataFiles(
            data_directory, sample, file_name_regex=FILENAME_FORMAT
        )
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
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta(
                "pubmed_id",
                getter("MedlineCitation/PMID"),
            ),
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
                "journal_issn_type",
                agetter("IssnType", "MedlineCitation/Article/Journal/ISSN"),
            ),
            ColumnMeta(
                "journal_cited_medium",
                agetter(
                    "CitedMedium",
                    "MedlineCitation/Article/Journal/JournalIssue",
                ),
            ),
            ColumnMeta(
                "journal_volume",
                getter("MedlineCitation/Article/Journal/JournalIssue/Volume"),
                description="Journal volume",
                data_type="INTEGER",
            ),
            ColumnMeta(
                "journal_issue",
                getter("MedlineCitation/Article/Journal/JournalIssue/Issue"),
                description="Journal issue",
                data_type="INTEGER",
            ),
            ColumnMeta(
                "journal_year",
                getter(
                    "MedlineCitation/Article/Journal/JournalIssue/PubDate/Year"
                ),
                description="Journal year",
                data_type="INTEGER",
            ),
            ColumnMeta(
                "journal_month",
                getter(
                    "MedlineCitation/Article/Journal/JournalIssue/PubDate/Month"
                ),
                description="Journal month",
                data_type="INTEGER",
            ),
            ColumnMeta(
                "journal_day",
                getter(
                    "MedlineCitation/Article/Journal/JournalIssue/PubDate/Day"
                ),
                description="Journal day",
                data_type="INTEGER",
            ),
            ColumnMeta(
                "journal_medline_date",
                getter(
                    "MedlineCitation/Article/Journal/JournalIssue/PubDate/MedlineDate"
                ),
                description="Journal Medline date",
            ),
            ColumnMeta(
                "journal_ISO_abbreviation",
                getter("MedlineCitation/Article/Journal/ISOAbbreviation"),
                description="Journal ISO abbreviation",
            ),
            ColumnMeta(
                "article_date_year",
                getter("MedlineCitation/Article/ArticleDate/Year"),
                data_type="INTEGER",
            ),
            ColumnMeta(
                "article_date_month",
                getter("MedlineCitation/Article/ArticleDate/Month"),
                data_type="INTEGER",
            ),
            ColumnMeta(
                "article_date_day",
                getter("MedlineCitation/Article/ArticleDate/Day"),
                data_type="INTEGER",
            ),
            ColumnMeta(
                "article_date_type",
                agetter("DateType", "MedlineCitation/Article/ArticleDate"),
            ),
            ColumnMeta(
                "pagination",
                getter("MedlineCitation/Article/Pagination/MedlinePgn"),
                description="Pagination",
            ),
            ColumnMeta(
                "elocation_id", getter("MedlineCitation/Article/ELocationID")
            ),
            ColumnMeta(
                "elocation_id_type",
                agetter("EIdType", "MedlineCitation/Article/ELocationID"),
            ),
            ColumnMeta(
                "elocation_id_valid",
                agetter("ValidYN", "MedlineCitation/Article/ELocationID"),
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
                "vernacular_title",
                getter("MedlineCitation/Article/VernacularTitle"),
                description="Original title",
            ),
            ColumnMeta(
                "journal_country",
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
                data_type="INTEGER",
            ),
            ColumnMeta(
                "completed_month",
                getter("MedlineCitation/DateCompleted/Month"),
                data_type="INTEGER",
            ),
            ColumnMeta(
                "completed_day",
                getter("MedlineCitation/DateCompleted/Day"),
                data_type="INTEGER",
            ),
            ColumnMeta(
                "revised_year",
                getter("MedlineCitation/DateRevised/Year"),
                data_type="INTEGER",
            ),
            ColumnMeta(
                "revised_month",
                getter("MedlineCitation/DateRevised/Month"),
                data_type="INTEGER",
            ),
            ColumnMeta(
                "revised_day",
                getter("MedlineCitation/DateRevised/Day"),
                data_type="INTEGER",
            ),
            ColumnMeta(
                "coi_statement",
                getter("MedlineCitation/CoiStatement"),
            ),
            ColumnMeta(
                "medline_citation_status",
                agetter("Status", "MedlineCitation"),
            ),
            ColumnMeta(
                "medline_citation_owner",
                agetter("Owner", "MedlineCitation"),
            ),
            ColumnMeta(
                "medline_citation_version",
                agetter("VersionID", "MedlineCitation"),
            ),
            ColumnMeta(
                "medline_citation_indexing_method",
                agetter("IndexingMethod", "MedlineCitation"),
            ),
            ColumnMeta(
                "medline_citation_version_date",
                agetter("VersionDate", "MedlineCitation"),
            ),
            ColumnMeta(
                "keyword_list_owner",
                agetter("Owner", "MedlineCitation/KeywordList"),
            ),
            ColumnMeta(
                "publication_status", getter("PubmedData/PublicationStatus")
            ),
            ColumnMeta(
                "abstract_copyright_information",
                getter(
                    "MedlineCitation/Article/Abstract/CopyrightInformation"
                ),
            ),
            ColumnMeta(
                "other_abstract_copyright_information",
                getter("MedlineCitation/OtherAbstract/CopyrightInformation"),
            ),
        ],
        cursor_class=ArticlesCursor,
    ),
    TableMeta(
        "pubmed_authors",
        foreign_key="article_id",
        parent_name="pubmed_articles",
        primary_key="id",
        extract_multiple=all_getter(
            "MedlineCitation/Article/AuthorList/Author"
        ),
        cursor_class=AuthorsCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("article_id"),
            ColumnMeta(
                "given",
                getter("ForeName"),
            ),
            ColumnMeta(
                "family",
                getter("LastName"),
            ),
            ColumnMeta(
                "suffix",
                getter("Suffix"),
            ),
            ColumnMeta(
                "initials",
                getter("Initials"),
            ),
            ColumnMeta(
                "valid",
                agetter("ValidYN"),
            ),
            ColumnMeta(
                "identifier",
                author_identifier(getter("Identifier")),
            ),
            ColumnMeta(
                "identifier_source",
                agetter("Source", "Identifier"),
            ),
            ColumnMeta("collective_name", getter("CollectiveName")),
        ],
    ),
    TableMeta(
        "pubmed_author_affiliations",
        foreign_key="author_id",
        parent_name="pubmed_authors",
        primary_key="id",
        extract_multiple=all_getter(
            "AffiliationInfo",
        ),
        extract_multiple_parent=all_getter(
            "MedlineCitation/Article/AuthorList/Author"
        ),
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("author_id"),
            ColumnMeta(
                "affiliation",
                getter("Affiliation"),
            ),
            ColumnMeta(
                "identifier",
                getter("Identifier"),
            ),
        ],
        cursor_class=AffiliationCursor,
    ),
    TableMeta(
        "pubmed_investigators",
        foreign_key="article_id",
        parent_name="pubmed_articles",
        primary_key="id",
        extract_multiple=all_getter(
            "MedlineCitation/InvestigatorList/Investigator"
        ),
        cursor_class=InvestigatorsCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("article_id"),
            ColumnMeta(
                "given",
                getter("ForeName"),
            ),
            ColumnMeta(
                "family",
                getter("LastName"),
            ),
            ColumnMeta(
                "suffix",
                getter("Suffix"),
            ),
            ColumnMeta(
                "initials",
                getter("Initials"),
            ),
            ColumnMeta(
                "valid",
                agetter("ValidYN"),
            ),
            ColumnMeta(
                "identifier",
                getter("Identifier"),
            ),
            ColumnMeta(
                "identifier_source",
                agetter("Source", "Identifier"),
            ),
        ],
    ),
    TableMeta(
        "pubmed_investigator_affiliations",
        foreign_key="investigator_id",
        parent_name="pubmed_investigators",
        primary_key="id",
        extract_multiple=all_getter(
            "AffiliationInfo",
        ),
        extract_multiple_parent=all_getter(
            "MedlineCitation/InvestigatorList/Investigator"
        ),
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("investigator_id"),
            ColumnMeta(
                "affiliation",
                getter("Affiliation"),
            ),
            ColumnMeta(
                "identifier",
                getter("Identifier"),
            ),
        ],
        cursor_class=AffiliationCursor,
    ),
    TableMeta(
        "pubmed_abstracts",
        foreign_key="article_id",
        parent_name="pubmed_articles",
        primary_key="id",
        extract_multiple=all_getter(
            "MedlineCitation/Article/Abstract/AbstractText"
        ),
        cursor_class=AbstractsCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("article_id"),
            ColumnMeta(
                "label",
                agetter("Label"),
                description="Abstract label",
            ),
            ColumnMeta(
                "text",
                get_root_text(),
                description="Abstract text",
            ),
            ColumnMeta(
                "nlm_category",
                agetter("NlmCategory"),
            ),
            ColumnMeta(
                "copyright_information", getter("CopyrightInformation")
            ),
        ],
    ),
    TableMeta(
        "pubmed_other_abstracts",
        foreign_key="article_id",
        parent_name="pubmed_articles",
        primary_key="id",
        extract_multiple=all_getter("MedlineCitation/OtherAbstract"),
        cursor_class=OtherAbstractsCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("article_id"),
            ColumnMeta(
                "abstract_type",
                agetter("Type"),
            ),
            ColumnMeta(
                "language",
                agetter("Language"),
            ),
        ],
    ),
    TableMeta(
        "pubmed_other_abstract_texts",
        foreign_key="abstract_id",
        parent_name="pubmed_other_abstracts",
        primary_key="id",
        extract_multiple=all_getter("AbstractText"),
        extract_multiple_parent=all_getter("MedlineCitation/OtherAbstract"),
        cursor_class=OtherAbstractTextsCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("abstract_id"),
            ColumnMeta(
                "text",
                get_root_text(),
            ),
            ColumnMeta(
                "label",
                agetter("Label"),
            ),
            ColumnMeta(
                "nlm_category",
                agetter("NlmCategory"),
            ),
            ColumnMeta(
                "copyright_information", getter("CopyrightInformation")
            ),
        ],
    ),
    TableMeta(
        "pubmed_history",
        foreign_key="article_id",
        parent_name="pubmed_articles",
        primary_key="id",
        extract_multiple=all_getter("PubmedData/History/PubMedPubDate"),
        cursor_class=HistoryCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("article_id"),
            ColumnMeta(
                "publication_status",
                agetter("PubStatus"),
            ),
            ColumnMeta("year", getter("Year"), data_type="INTEGER"),
            ColumnMeta("month", getter("Month"), data_type="INTEGER"),
            ColumnMeta("day", getter("Day"), data_type="INTEGER"),
            ColumnMeta("hour", getter("Hour"), data_type="INTEGER"),
            ColumnMeta("minute", getter("Minute"), data_type="INTEGER"),
        ],
    ),
    TableMeta(
        "pubmed_chemicals",
        foreign_key="article_id",
        parent_name="pubmed_articles",
        primary_key="id",
        extract_multiple=all_getter("MedlineCitation/ChemicalList/Chemical"),
        cursor_class=ChemicalsCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("article_id"),
            ColumnMeta(
                "registry_number",
                getter("RegistryNumber"),
            ),
            ColumnMeta(
                "name_of_substance",
                getter("NameOfSubstance"),
            ),
            ColumnMeta(
                "unique_identifier",
                agetter("UI", "NameOfSubstance"),
            ),
        ],
    ),
    TableMeta(
        "pubmed_meshs",
        foreign_key="article_id",
        parent_name="pubmed_articles",
        primary_key="id",
        extract_multiple=all_getter(
            "MedlineCitation/MeshHeadingList/MeshHeading"
        ),
        cursor_class=MeshHeadingsCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("article_id"),
            ColumnMeta(
                "descriptor_name",
                getter("DescriptorName"),
            ),
            ColumnMeta(
                "descriptor_unique_identifier",
                agetter("UI", "DescriptorName"),
            ),
            ColumnMeta(
                "descriptor_major_topic",
                agetter("MajorTopicYN", "DescriptorName"),
            ),
            ColumnMeta(
                "descriptor_type",
                agetter("Type", "DescriptorName"),
            ),
            ColumnMeta(
                "qualifier_name",
                getter("QualifierName"),
            ),
            ColumnMeta(
                "qualifier_major_topic",
                agetter("MajorTopicYN", "QualifierName"),
            ),
            ColumnMeta(
                "qualifier_unique_identifier",
                agetter("UI", "QualifierName"),
            ),
        ],
    ),
    TableMeta(
        "pubmed_supplement_meshs",
        foreign_key="article_id",
        parent_name="pubmed_articles",
        primary_key="id",
        extract_multiple=all_getter(
            "MedlineCitation/SupplMeshList/SupplMeshName"
        ),
        cursor_class=SupplementMeshsCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("article_id"),
            ColumnMeta(
                "supplement_mesh_name",
                get_root_text(),
            ),
            ColumnMeta(
                "unique_identifier",
                agetter("UI"),
            ),
            ColumnMeta(
                "mesh_type",
                agetter("Type"),
            ),
        ],
    ),
    TableMeta(
        "pubmed_comments_corrections",
        foreign_key="article_id",
        parent_name="pubmed_articles",
        primary_key="id",
        extract_multiple=all_getter(
            "MedlineCitation/CommentsCorrectionsList/CommentsCorrections"
        ),
        cursor_class=CommentsCorrectionsCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("article_id"),
            ColumnMeta(
                "ref_type",
                agetter("RefType"),
                description="Reference type",
            ),
            ColumnMeta(
                "ref_source",
                getter("RefSource"),
                description="Reference source",
            ),
            ColumnMeta(
                "pmid",
                getter("PMID"),
                description="PubMed identifier",
            ),
            ColumnMeta(
                "pmid_version",
                agetter("Version", "PMID"),
                description="PubMed identifier version",
            ),
            ColumnMeta(
                "note",
                getter("Note"),
            ),
        ],
    ),
    TableMeta(
        "pubmed_keywords",
        foreign_key="article_id",
        parent_name="pubmed_articles",
        primary_key="id",
        extract_multiple=all_getter("MedlineCitation/KeywordList/Keyword"),
        cursor_class=KeywordsCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("article_id"),
            ColumnMeta(
                "keyword",
                get_root_text(),
                description="Keyword",
            ),
            ColumnMeta(
                "major_topic",
                agetter("MajorTopicYN"),
                description="Keyword major topic",
            ),
        ],
    ),
    TableMeta(
        "pubmed_grants",
        foreign_key="article_id",
        parent_name="pubmed_articles",
        primary_key="id",
        extract_multiple=all_getter("MedlineCitation/Article/GrantList/Grant"),
        cursor_class=GrantsCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("article_id"),
            ColumnMeta(
                "grant_id",
                getter("GrantID"),
                description="Grant identifier",
            ),
            ColumnMeta(
                "acronym",
                getter("Acronym"),
                description="Acronym",
            ),
            ColumnMeta(
                "agency",
                getter("Agency"),
                description="Agency",
            ),
            ColumnMeta(
                "country",
                getter("Country"),
                description="Country",
            ),
        ],
    ),
    TableMeta(
        "pubmed_data_banks",
        foreign_key="article_id",
        parent_name="pubmed_articles",
        primary_key="id",
        extract_multiple=all_getter(
            "MedlineCitation/Article/DataBankList/DataBank"
        ),
        cursor_class=DataBanksCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("article_id"),
            ColumnMeta(
                "data_bank_name",
                getter("DataBankName"),
            ),
        ],
    ),
    TableMeta(
        "pubmed_data_bank_accessions",
        foreign_key="data_bank_id",
        parent_name="pubmed_data_banks",
        primary_key="id",
        extract_multiple=all_getter("AccessionNumberList"),
        extract_multiple_parent=all_getter(
            "MedlineCitation/Article/DataBankList/DataBank"
        ),
        cursor_class=DataBankAccessionsCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("data_bank_id"),
            ColumnMeta(
                "accession_number",
                getter("AccessionNumber"),
            ),
        ],
    ),
    TableMeta(
        "pubmed_references",
        foreign_key="article_id",
        parent_name="pubmed_articles",
        primary_key="id",
        extract_multiple=all_getter("PubmedData/ReferenceList/Reference"),
        cursor_class=ReferencesCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("article_id"),
            ColumnMeta(
                "citation",
                getter("Citation"),
            ),
        ],
    ),
    TableMeta(
        "pubmed_reference_articles",
        foreign_key="reference_id",
        parent_name="pubmed_references",
        primary_key="id",
        extract_multiple=all_getter("ArticleIdList"),
        extract_multiple_parent=all_getter(
            "PubmedData/ReferenceList/Reference"
        ),
        cursor_class=ReferenceArticlesCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("reference_id"),
            ColumnMeta(
                "article_id",
                getter("ArticleId"),
            ),
            ColumnMeta(
                "id_type",
                agetter("IdType", "ArticleId"),
            ),
        ],
    ),
    TableMeta(
        "pubmed_publication_types",
        foreign_key="article_id",
        parent_name="pubmed_articles",
        primary_key="id",
        extract_multiple=all_getter(
            "MedlineCitation/Article/PublicationTypeList/PublicationType"
        ),
        cursor_class=PublicationTypeListCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("article_id"),
            ColumnMeta("publication_type", get_root_text()),
            ColumnMeta("unique_identifier", agetter("UI")),
        ],
    ),
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
        for each PubMed container file with each container's file
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
