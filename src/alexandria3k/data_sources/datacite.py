#
# Alexandria3k Datacite bibliographic metadata processing
# Copyright (C) 2023-2024 Evgenia Pampidi
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
"""Datacite publication data"""

import abc
from alexandria3k.db_schema import ColumnMeta, TableMeta
from alexandria3k.file_cache import get_file_cache
import json
import tarfile

from alexandria3k.common import (
    Alexandria3kError,
    Alexandria3kInternalError,
    warn,
)
from alexandria3k.data_source import (
    CONTAINER_INDEX,
    ROWID_INDEX,
    DataFiles,
    DataSource,
    ElementsCursor,
    FilesCursor,
    StreamingCachedContainerTable,
)

from alexandria3k import perf
from alexandria3k.db_schema import ColumnMeta, TableMeta

DEFAULT_SOURCE = None

# Method names coming from apsw start with uppercase
# pylint: disable=invalid-name
# pylint: disable=too-many-lines

def dict_value(dictionary, key):
    """Return the value of dictionary for key or None if it doesn't exist"""
    if not dictionary:
        return None
    return dictionary.get(key)


class DataciteElementsCursor(ElementsCursor):
    """A cursor over Datacite elements.  It depends on the implementation
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

    
class RightsCursor(DataciteElementsCursor):
    """A cursor over the work items' rights data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "rightsList"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 1M rights"""
        return (self.parent_cursor.Rowid() << 20) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # work_id
            return self.parent_cursor.Rowid()
        return super().Column(col)


# pylint: disable-next=too-many-instance-attributes
class WorksCursor(DataciteElementsCursor):
    """A virtual table cursor over works data.
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

    def Rowid(self):
        """Return a unique id of the row along all records"""
        # Allow for 16k items per file
        return (self.files_cursor.Rowid() << 14) | (self.item_index)

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # id
            return self.Rowid()
        
        return super().Column(col)

    def Filter(self, index_number, index_name, constraint_args):
        """Always called first to initialize an iteration to the first row
        of the table according to the index"""
        self.files_cursor.Filter(index_number, index_name, constraint_args)
        self.eof = self.files_cursor.Eof()
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

    def current_row_value(self):
        """Return the current row. Not part of the apsw API."""
        return self.data_source.get_element_tree()

    def Close(self):
        """Cursor's destructor, used for cleanup"""
        if self.iterator:
            self.data_source.close()


class CreatorsCursor(DataciteElementsCursor):
    """A cursor over the items' creators data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "creators"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 16k creators."""
        return (self.parent_cursor.Rowid() << 14) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # id
            return self.record_id()

        if col == 2:  # work_id
            return self.parent_cursor.Rowid()

        return super().Column(col)


class AffiliationsCursor(DataciteElementsCursor):
    """A cursor over the creators'/contributors' affiliation data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "affiliation"

    def Rowid(self):
        """Return a unique id of the row along all records
        This allows for 128 affiliations per creator/contributor."""
        return (self.parent_cursor.Rowid() << 7) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # Creator-id/Contributor-id
            return self.parent_cursor.record_id()
        return super().Column(col)
    

class NameIdentifierCursor(DataciteElementsCursor):
    """A cursor over the creators'/contributors' name identifier data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "nameIdentifiers"

    def Rowid(self):
        """Return a unique id of the row along all records
        This allows for 128 name identifiers per creator/contributor."""
        return (self.parent_cursor.Rowid() << 7) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # Creator-id/Contributor-id
            return self.parent_cursor.record_id()
        return super().Column(col)


class TitlesCursor(DataciteElementsCursor):
    """A cursor over the work items' subject data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "titles"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 128 titles"""
        return (self.parent_cursor.Rowid() << 7) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # work_id
            return self.parent_cursor.Rowid()
        return super().Column(col)


class SubjectsCursor(DataciteElementsCursor):
    """A cursor over the work items' subject data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "subjects"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 1M subjects"""
        return (self.parent_cursor.Rowid() << 20) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # work_id
            return self.parent_cursor.Rowid()
        return super().Column(col)


class ContributorsCursor(DataciteElementsCursor):
    """A cursor over the items' contributors data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "contributors"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 16k contributors."""
        return (self.parent_cursor.Rowid() << 14) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # id
            return self.record_id()

        if col == 2:  # work_id
            return self.parent_cursor.Rowid()

        return super().Column(col)


class DatesCursor(DataciteElementsCursor):
    """A cursor over the work items' dates data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "dates"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 128 dates"""
        return (self.parent_cursor.Rowid() << 7) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # work_id
            return self.parent_cursor.Rowid()
        return super().Column(col)


class RelatedIdentifiersCursor(DataciteElementsCursor):
    """A cursor over the work items' related identifier data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "relatedIdentifiers"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 128 related identifiers"""
        return (self.parent_cursor.Rowid() << 7) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # work_id
            return self.parent_cursor.Rowid()
        return super().Column(col)
    

class SizesCursor(DataciteElementsCursor):
    """A cursor over the work items' sizes data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "sizes"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 128 sizes"""
        return (self.parent_cursor.Rowid() << 7) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # work_id
            return self.parent_cursor.Rowid()
        return super().Column(col)
    

class FormatsCursor(DataciteElementsCursor):
    """A cursor over the work items' formats data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "formats"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 128 formats"""
        return (self.parent_cursor.Rowid() << 7) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # work_id
            return self.parent_cursor.Rowid()
        return super().Column(col)


class DescriptionsCursor(DataciteElementsCursor):
    """A cursor over the work items' description data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "descriptions"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 128 description"""
        return (self.parent_cursor.Rowid() << 7) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # work_id
            return self.parent_cursor.Rowid()
        return super().Column(col)
    

class GeoLocationCursor(DataciteElementsCursor):
    """A cursor over the work items' geo-location data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "geoLocations"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 128 geo-locations."""
        return (self.parent_cursor.Rowid() << 7) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # work_id
            return self.parent_cursor.Rowid()
        return super().Column(col)


class FundingReferencesCursor(DataciteElementsCursor):
    """A cursor over the work items' funding references data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "fundingReferences"

    def Rowid(self):
        """Return a unique id of the row along all records
        This allows for 1k funding references"""
        return (self.parent_cursor.Rowid() << 10) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # work_id
            return self.parent_cursor.Rowid()
        return super().Column(col)


class TarFiles:
    """The source of the JSON files in a compressed tar archive.
    This is a singleton, iterated over either data_source
    (when partitioning is in effect) or by PersonsCursor.
    The file contents are accessed by PersonsCursor."""

    def __init__(self, file_path, sample):
        # Collect the names of all available data files
        self.file_path = file_path
        self.sample = sample
        # Set by tar_generator
        self.tar_info = None
        self.tar = None
        self.file_id = -1
        # Updated by get_json_data
        self.json_data = None

    def tar_generator(self):
        """A generator function iterating over the tar file entries."""
        # pylint: disable-next=consider-using-with
        self.tar = tarfile.open(self.file_path, "r|gz")
        for self.tar_info in self.tar:
            if not self.tar_info.isreg():
                continue

            (_root, _checksum, file_name) = self.tar_info.name.split("/")
            self.file_id += 1
            self.json_data = None
            yield self.file_id

    def get_json_data(self):
        """Return the parsed JSON data of the current element"""
        if self.json_data:
            return self.json_data
        # Extract and parse JSON data
        reader = self.tar.extractfile(self.tar_info)
        json_data = reader.read()
        self.json_data = json.loads(json_data)

        return self.json_data

    def close(self):
        """Close the opened tar file"""
        self.tar.close()

    def get_container_iterator(self):
        """Return an iterator over the int identifiers of all data files"""
        return self.tar_generator()

    def get_container_id(self):
        """Return the file id of the current element."""
        return self.file_id


class VTSource:
    """Virtual table data source. This gets registered with the apsw
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
            table, self.table_dict, self.data_files.get_file_array()
        )

    Connect = Create

    def get_container_iterator(self):
        """Return an iterator over the data files' identifiers"""
        return self.data_files.get_container_iterator()

    def get_container_name(self, fid):
        """Return the name of the file corresponding to the specified fid"""
        return self.data_files.get_container_name(fid)


# The full schema is documented in
# https://schema.datacite.org/meta/kernel-4.0/
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
            ColumnMeta(
                "identifier", 
                lambda row: dict_value(
                    dict_value(row, "container"), "identifier"
                )
            ),
            ColumnMeta(
                "identifier_type", 
                lambda row: dict_value(
                    dict_value(row, "container"), "identifierType"
                )
            ),
            ColumnMeta("doi", lambda row: dict_value(row, "doi")),
            ColumnMeta("publisher", 
                lambda row: dict_value(row, "publisher")
            ),
            ColumnMeta(
                "publication_year", 
                lambda row: dict_value(row, "publicationYear")
            ),
            ColumnMeta(
                "resource_type", 
                lambda row: dict_value(
                    dict_value(row, "types"), "resourceType"
                )
            ), 
            ColumnMeta(
                "resource_type_general", 
                lambda row: dict_value(
                    dict_value(row, "types"), "resourceTypeGeneral"
                )
            ),
            ColumnMeta("language", 
                lambda row: dict_value(row, "language")
            ), 
            ColumnMeta("schema_version", 
                lambda row: dict_value(row, "schemaVersion")
            ),
            ColumnMeta(
                "metadata_version", 
                lambda row: dict_value(row, "metadataVersion")
            ),
            ColumnMeta("url", lambda row: dict_value(row, "url")),
            ColumnMeta("created", 
                lambda row: dict_value(row, "created")
            ),
            ColumnMeta("registered", 
                lambda row: dict_value(row, "registered")
            ),
            ColumnMeta("published", 
                lambda row: dict_value(row, "published")
            ),
            ColumnMeta("updated", 
                lambda row: dict_value(row, "updated")
            ),
        ],
    ),
    TableMeta(
        "work_creators",
        foreign_key="work_id",
        parent_name="works",
        primary_key="id",
        cursor_class=CreatorsCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("work_id"),
            ColumnMeta("name",
                lambda row: dict_value(row, "name")
            ),
            ColumnMeta("given_name", 
                lambda row: dict_value(row, "givenName")
            ),
            ColumnMeta("family_name", 
                lambda row: dict_value(row, "familyName")
            ),
        ],
    ),
    TableMeta(
        "creator_name_identifiers",
        foreign_key="creator_id",
        parent_name="work_creators",
        primary_key="id",
        cursor_class=NameIdentifierCursor,
        columns=[
            ColumnMeta("creator_id"),
            ColumnMeta("container_id"),
            ColumnMeta("name_identifier",
                lambda row: dict_value(row, "nameIdentifier")
            ),
            ColumnMeta("name_identifier_scheme",
                lambda row: dict_value(row, "nameIdentifierScheme")
            ),
            ColumnMeta("scheme_uri",
                lambda row: dict_value(row, "schemeUri")
            ),
        ],
    ),
    TableMeta(
        "creator_affiliations",
        foreign_key="creator_id",
        parent_name="work_creators",
        primary_key="id",
        cursor_class=AffiliationsCursor,
        columns=[
            ColumnMeta("creator_id"),
            ColumnMeta("container_id"),
            ColumnMeta("name", lambda row: dict_value(row, "name")),
        ],
    ),
    TableMeta(
        "work_titles",
        foreign_key="work_id",
        parent_name="works",
        primary_key="id",
        cursor_class=TitlesCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("work_id"),
            ColumnMeta("title", lambda row: dict_value(row, "title")),
            ColumnMeta("title_type",
                lambda row: dict_value(row, "titleType")
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
            ColumnMeta("subject", lambda row: dict_value(row, "subject")),
            ColumnMeta("subject_scheme", 
                lambda row: dict_value(row, "subjectScheme")
                ),
            ColumnMeta("scheme_uri",
                lambda row: dict_value(row, "schemeUri")
            ),
            ColumnMeta("value_uri", 
                lambda row: dict_value(row, "valueUri")
            ),
        ]
    ),
    TableMeta(
        "work_contributors",
        foreign_key="work_id",
        parent_name="works",
        primary_key="id",
        cursor_class=ContributorsCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("work_id"),
            ColumnMeta("contributor_type", 
                lambda row: dict_value(row, "contributorType")
            ),
            ColumnMeta("name", lambda row: dict_value(row, "name")),
            ColumnMeta("family_name", 
                lambda row: dict_value(row, "familyName")
            ),
            ColumnMeta("given_name", 
                lambda row: dict_value(row, "givenName")
            ),
        ]
    ),
    TableMeta(
        "contributor_name_identifiers",
        foreign_key="contributor_id",
        parent_name="work_contributors",
        primary_key="id",
        cursor_class=NameIdentifierCursor,
        columns=[
            ColumnMeta("contributor_id"),
            ColumnMeta("container_id"),
            ColumnMeta("name_identifier", 
                lambda row: dict_value(row, "nameIdentifier")
            ),
            ColumnMeta("name_identifier_scheme",
                lambda row: dict_value(row, "nameIdentifierScheme")
            ),
            ColumnMeta("scheme_uri", 
                lambda row: dict_value(row, "schemeUri")
            ),
        ],
    ),
    TableMeta(
        "contributor_affiliations",
        foreign_key="contributor_id",
        parent_name="work_contributors",
        primary_key="id",
        cursor_class=AffiliationsCursor,
        columns=[
            ColumnMeta("contributor_id"),
            ColumnMeta("container_id"),
            ColumnMeta("name", lambda row: dict_value(row, "name")),
        ],
    ),
    TableMeta(
        "work_dates",
        foreign_key="work_id",
        parent_name="works",
        primary_key="id",
        cursor_class=DatesCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
            ColumnMeta("date", 
                lambda row: dict_value(row, "date")
            ),
            ColumnMeta("date_type",
                lambda row: dict_value(row, "dateType")
            ),
        ]
    ),
    TableMeta(
        "work_related_identifiers",
        foreign_key="work_id",
        parent_name="works",
        primary_key="id",
        cursor_class=RelatedIdentifiersCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
            ColumnMeta("related_identifier", 
                lambda row: dict_value(row, "relatedIdentifier")
            ),
            ColumnMeta("related_identifier_type",
                lambda row: dict_value(row, "relatedIdentifierType")
            ),
            ColumnMeta("relation_type", 
                lambda row: dict_value(row, "relationType")
            ),
            ColumnMeta("related_metadata_scheme", 
                lambda row: dict_value(row, "relatedMetadataSchema")
            ),
            ColumnMeta("scheme_uri", 
                lambda row: dict_value(row, "schemeUri")
            ),
            ColumnMeta("scheme_type", 
                lambda row: dict_value(row, "schemeType")
            ),
        ]
    ),
    TableMeta(
        "work_sizes",
        foreign_key="work_id",
        parent_name="works",
        primary_key="id",
        cursor_class=SizesCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
            ColumnMeta("size", 
                lambda row: dict_value(row, "sizes")
            ),
        ]
    ),
    TableMeta(
        "work_formats",
        foreign_key="work_id",
        parent_name="works",
        primary_key="id",
        cursor_class=FormatsCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
            ColumnMeta("format", 
                lambda row: dict_value(row, "formats")
            ),
        ]
    ),
    TableMeta(
        "work_rights",
        foreign_key="work_id",
        parent_name="works",
        primary_key="id",
        cursor_class=RightsCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
            ColumnMeta("rights", 
                lambda row: dict_value(row, "rights")
            ),
            ColumnMeta("rights_uri", 
                lambda row: dict_value(row, "rightsUri")
            ),
        ]
    ),
    TableMeta(
        "work_descriptions",
        foreign_key="work_id",
        parent_name="works",
        primary_key="id",
        cursor_class=DescriptionsCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
            ColumnMeta("description", 
                lambda row: dict_value(row, "description")
            ),
            ColumnMeta("description_type",
                lambda row: dict_value(row, "descriptionType")
            ),
        ]
    ),
    TableMeta(
        "work_geo_locations",
        foreign_key="work_id",
        parent_name="works",
        primary_key="id",
        cursor_class=GeoLocationCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
            ColumnMeta("geo_location_point", 
                f'[
                    {(lambda row: dict_value(
                        dict_value(row, "geoLocationPoint")), "pointLongitude")}, 
                    {(lambda row: dict_value(
                        dict_value(row, "geoLocationPoint")), "pointLatitude")} 
                ]'
            ),
            ColumnMeta("geo_location_box",
                f'[
                    {(lambda row: dict_value(
                        dict_value(row, "geoLocationPoint")), "westBoundLongitude")}, 
                    {(lambda row: dict_value(
                        dict_value(row, "geoLocationPoint")), "eastBoundLongitude")},
                    {(lambda row: dict_value(
                        dict_value(row, "geoLocationPoint")), "southBoundLatitude")}, 
                    {(lambda row: dict_value(
                        dict_value(row, "geoLocationPoint")), "northBoundLatitude")} 
                ]'
            ),
            ColumnMeta("geo_location_place", 
                lambda row: dict_value(row, "geoLocationPlace")
            ),
        ]
    ),
    TableMeta(
        "work_funding_references",
        foreign_key="work_id",
        parent_name="works",
        primary_key="id",
        cursor_class=FundingReferencesCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
            ColumnMeta("funder_name", 
                lambda row: dict_value(row, "funderName")
            ),
            ColumnMeta("funder_identifier", 
                lambda row: dict_value(row, "funderIdentifier")
            ),
            ColumnMeta("funder_identifier_type", 
                lambda row: dict_value(row, "funderIdentifierType")
            ),
            ColumnMeta("award_number", 
                lambda row: dict_value(row, "awardNumber")
            ),
            ColumnMeta("award_uri", 
                lambda row: dict_value(row, "awardUri")
            ),
            ColumnMeta("award_title", 
                lambda row: dict_value(row, "awardTitle")
            ),
        ]
    ),
]

class Datacite(DataSource):
    """
    Create an object containing Datacite meta-data that supports queries over
    its (virtual) tables and the population of an SQLite database with its
    data.

    :param datacite_directory: The directory path where the Datacite
        data files are located
    :type datacite_directory: str

    :param sample: A callable to control container sampling, defaults
        to `lambda n: True`.
        The population or query method will call this argument
        for each Datacite container file with each container's file
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
        datacite_directory,
        sample=lambda n: True,
        attach_databases=None,
    ):
        super().__init__(
            VTSource(datacite_directory, sample),
            tables,
            attach_databases,
        )
