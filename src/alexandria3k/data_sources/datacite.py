#
# Alexandria3k DataCite bibliographic metadata processing
# Copyright (C) 2023-2024 Evgenia Pampidi and Diomidis Spinellis
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
"""DataCite publication data"""

import json
import os
import tarfile

from alexandria3k.common import Alexandria3kError

from alexandria3k.data_source import (
    CONTAINER_INDEX,
    PROGRESS_BAR_LENGTH,
    DataSource,
    ItemsCursor,
    NestedElementsCursor,
    RecordsCursor,
    StreamingCachedContainerTable,
)

from alexandria3k.db_schema import ColumnMeta, TableMeta
from alexandria3k import debug

DEFAULT_SOURCE = None

# Method names coming from apsw start with uppercase
# pylint: disable=invalid-name
# pylint: disable=too-many-lines


def dict_value(dictionary, key):
    """Return the value of dictionary for key or None if it doesn't exist"""
    if not dictionary:
        return None
    return dictionary.get(key)


def float_value(string):
    """Return the float value of a string or None if None is passed"""
    return float(string) if string else None


class WorksCursor(RecordsCursor):
    """A cursor over the works data."""

    def __init__(self, table):
        super().__init__(table, None)
        self.files_cursor = TarFilesCursor(table)
        self.cached_json_item_index = None
        self.json_data = None

    def current_row_value(self):
        """Return the current row. Not part of the apsw API."""
        if self.cached_json_item_index != self.item_index:
            json_string = self.files_cursor.current_row_value()[
                self.item_index
            ]
            self.json_data = json.loads(json_string)
            # Record 10.17031/637b5e4a8d3ae of file10.17031/part_00001.jsonl
            # and others have affiliation as a dict, rather than an array
            # containing a dict.  Detect and fix.
            for relation in ["creators", "contributors"]:
                for creator in self.json_data[relation]:
                    affiliation = creator.get("affiliation")
                    if isinstance(affiliation, dict):
                        creator["affiliation"] = [affiliation]
                    name_identifiers = creator.get("nameIdentifiers")
                    if isinstance(name_identifiers, dict):
                        creator["nameIdentifiers"] = [name_identifiers]
            self.cached_json_item_index = self.item_index
        return self.json_data


class CreatorsCursor(NestedElementsCursor):
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


class AffiliationsCursor(NestedElementsCursor):
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


class NameIdentifierCursor(NestedElementsCursor):
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


class TitlesCursor(NestedElementsCursor):
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


class SubjectsCursor(NestedElementsCursor):
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


class ContributorsCursor(NestedElementsCursor):
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


class DatesCursor(NestedElementsCursor):
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


class RelatedIdentifiersCursor(NestedElementsCursor):
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


class RightsCursor(NestedElementsCursor):
    """A cursor over the work items' rights data."""

    def element_name(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "rightsList"

    def Rowid(self):
        """Return a unique id of the row along all records.
        This allows for 1k rights"""
        return (self.parent_cursor.Rowid() << 10) | self.element_index

    def Column(self, col):
        """Return the value of the column with ordinal col"""
        if col == 0:  # work_id
            return self.parent_cursor.Rowid()
        return super().Column(col)


class DescriptionsCursor(NestedElementsCursor):
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


class GeoLocationCursor(NestedElementsCursor):
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


class FundingReferencesCursor(NestedElementsCursor):
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


# The full schema is documented in
# https://schema.datacite.org/meta/kernel-4.0/
#
# In this relational view, by convention column 0 is the unique or foreign key,
# and column 1 the data's container

tables = [
    TableMeta(
        "dc_works",
        cursor_class=WorksCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta(
                "identifier",
                lambda row: dict_value(
                    dict_value(row, "container"), "identifier"
                ),
            ),
            ColumnMeta(
                "identifier_type",
                lambda row: dict_value(
                    dict_value(row, "container"), "identifierType"
                ),
            ),
            ColumnMeta("doi", lambda row: dict_value(row, "doi")),
            ColumnMeta("publisher", lambda row: dict_value(row, "publisher")),
            ColumnMeta(
                "publication_year",
                lambda row: dict_value(row, "publicationYear"),
            ),
            ColumnMeta(
                "resource_type",
                lambda row: dict_value(
                    dict_value(row, "types"), "resourceType"
                ),
            ),
            ColumnMeta(
                "resource_type_general",
                lambda row: dict_value(
                    dict_value(row, "types"), "resourceTypeGeneral"
                ),
            ),
            ColumnMeta("language", lambda row: dict_value(row, "language")),
            ColumnMeta("sizes", lambda row: str(dict_value(row, "sizes"))),
            ColumnMeta("formats", lambda row: str(dict_value(row, "formats"))),
            ColumnMeta(
                "schema_version", lambda row: dict_value(row, "schemaVersion")
            ),
            ColumnMeta(
                "metadata_version",
                lambda row: dict_value(row, "metadataVersion"),
            ),
            ColumnMeta("url", lambda row: dict_value(row, "url")),
            ColumnMeta("created", lambda row: dict_value(row, "created")),
            ColumnMeta(
                "registered", lambda row: dict_value(row, "registered")
            ),
            ColumnMeta("published", lambda row: dict_value(row, "published")),
            ColumnMeta("updated", lambda row: dict_value(row, "updated")),
        ],
    ),
    TableMeta(
        "dc_work_creators",
        foreign_key="work_id",
        parent_name="dc_works",
        primary_key="id",
        cursor_class=CreatorsCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("work_id"),
            ColumnMeta("name", lambda row: dict_value(row, "name")),
            ColumnMeta("name_type", lambda row: dict_value(row, "nameType")),
            ColumnMeta("given_name", lambda row: dict_value(row, "givenName")),
            ColumnMeta(
                "family_name", lambda row: dict_value(row, "familyName")
            ),
        ],
    ),
    TableMeta(
        "dc_creator_name_identifiers",
        foreign_key="creator_id",
        parent_name="dc_work_creators",
        primary_key="id",
        cursor_class=NameIdentifierCursor,
        columns=[
            ColumnMeta("creator_id"),
            ColumnMeta("container_id"),
            ColumnMeta(
                "name_identifier",
                lambda row: dict_value(row, "nameIdentifier"),
            ),
            ColumnMeta(
                "name_identifier_scheme",
                lambda row: dict_value(row, "nameIdentifierScheme"),
            ),
            ColumnMeta("scheme_uri", lambda row: dict_value(row, "schemeUri")),
        ],
    ),
    TableMeta(
        "dc_creator_affiliations",
        foreign_key="creator_id",
        parent_name="dc_work_creators",
        primary_key="id",
        cursor_class=AffiliationsCursor,
        columns=[
            ColumnMeta("creator_id"),
            ColumnMeta("container_id"),
            ColumnMeta("name", lambda row: dict_value(row, "name")),
        ],
    ),
    TableMeta(
        "dc_work_titles",
        foreign_key="work_id",
        parent_name="dc_works",
        primary_key="id",
        cursor_class=TitlesCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
            ColumnMeta("title", lambda row: dict_value(row, "title")),
            ColumnMeta("title_type", lambda row: dict_value(row, "titleType")),
        ],
    ),
    TableMeta(
        "dc_work_subjects",
        foreign_key="work_id",
        parent_name="dc_works",
        primary_key="id",
        cursor_class=SubjectsCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
            ColumnMeta("subject", lambda row: dict_value(row, "subject")),
            ColumnMeta(
                "subject_scheme", lambda row: dict_value(row, "subjectScheme")
            ),
            ColumnMeta("scheme_uri", lambda row: dict_value(row, "schemeUri")),
            ColumnMeta("value_uri", lambda row: dict_value(row, "valueUri")),
        ],
    ),
    TableMeta(
        "dc_work_contributors",
        foreign_key="work_id",
        parent_name="dc_works",
        primary_key="id",
        cursor_class=ContributorsCursor,
        columns=[
            ColumnMeta("id"),
            ColumnMeta("container_id"),
            ColumnMeta("work_id"),
            ColumnMeta(
                "contributor_type",
                lambda row: dict_value(row, "contributorType"),
            ),
            ColumnMeta("name", lambda row: dict_value(row, "name")),
            ColumnMeta(
                "family_name", lambda row: dict_value(row, "familyName")
            ),
            ColumnMeta("given_name", lambda row: dict_value(row, "givenName")),
        ],
    ),
    TableMeta(
        "dc_contributor_name_identifiers",
        foreign_key="contributor_id",
        parent_name="dc_work_contributors",
        primary_key="id",
        cursor_class=NameIdentifierCursor,
        columns=[
            ColumnMeta("contributor_id"),
            ColumnMeta("container_id"),
            ColumnMeta(
                "name_identifier",
                lambda row: dict_value(row, "nameIdentifier"),
            ),
            ColumnMeta(
                "name_identifier_scheme",
                lambda row: dict_value(row, "nameIdentifierScheme"),
            ),
            ColumnMeta("scheme_uri", lambda row: dict_value(row, "schemeUri")),
        ],
    ),
    TableMeta(
        "dc_contributor_affiliations",
        foreign_key="contributor_id",
        parent_name="dc_work_contributors",
        primary_key="id",
        cursor_class=AffiliationsCursor,
        columns=[
            ColumnMeta("contributor_id"),
            ColumnMeta("container_id"),
            ColumnMeta("name", lambda row: dict_value(row, "name")),
        ],
    ),
    TableMeta(
        "dc_work_dates",
        foreign_key="work_id",
        parent_name="dc_works",
        primary_key="id",
        cursor_class=DatesCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
            ColumnMeta("date", lambda row: dict_value(row, "date")),
            ColumnMeta("date_type", lambda row: dict_value(row, "dateType")),
        ],
    ),
    TableMeta(
        "dc_work_related_identifiers",
        foreign_key="work_id",
        parent_name="dc_works",
        primary_key="id",
        cursor_class=RelatedIdentifiersCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
            ColumnMeta(
                "related_identifier",
                lambda row: dict_value(row, "relatedIdentifier"),
            ),
            ColumnMeta(
                "related_identifier_type",
                lambda row: dict_value(row, "relatedIdentifierType"),
            ),
            ColumnMeta(
                "relation_type", lambda row: dict_value(row, "relationType")
            ),
            ColumnMeta(
                "related_metadata_scheme",
                lambda row: dict_value(row, "relatedMetadataSchema"),
            ),
            ColumnMeta("scheme_uri", lambda row: dict_value(row, "schemeUri")),
            ColumnMeta(
                "scheme_type", lambda row: dict_value(row, "schemeType")
            ),
        ],
    ),
    TableMeta(
        "dc_work_rights",
        foreign_key="work_id",
        parent_name="dc_works",
        primary_key="id",
        cursor_class=RightsCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
            ColumnMeta("rights", lambda row: dict_value(row, "rights")),
            ColumnMeta("lang", lambda row: dict_value(row, "lang")),
            ColumnMeta("rights_uri", lambda row: dict_value(row, "rightsUri")),
            ColumnMeta(
                "rights_identifier",
                lambda row: dict_value(row, "rightsIdentifier"),
            ),
            ColumnMeta(
                "rights_identifier_scheme",
                lambda row: dict_value(row, "rightsIdentifierScheme"),
            ),
            ColumnMeta("scheme_uri", lambda row: dict_value(row, "schemeUri")),
        ],
    ),
    TableMeta(
        "dc_work_descriptions",
        foreign_key="work_id",
        parent_name="dc_works",
        primary_key="id",
        cursor_class=DescriptionsCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
            ColumnMeta(
                "description", lambda row: dict_value(row, "description")
            ),
            ColumnMeta(
                "description_type",
                lambda row: dict_value(row, "descriptionType"),
            ),
        ],
    ),
    TableMeta(
        "dc_work_geo_locations",
        foreign_key="work_id",
        parent_name="dc_works",
        primary_key="id",
        cursor_class=GeoLocationCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
            ColumnMeta(
                "geo_location_place",
                lambda row: dict_value(row, "geoLocationPlace"),
            ),
            ColumnMeta(
                "geo_location_point",
                lambda row: str(
                    [
                        float_value(
                            dict_value(
                                dict_value(row, "geoLocationPoint"),
                                "pointLongitude",
                            )
                        ),
                        float_value(
                            dict_value(
                                dict_value(row, "geoLocationPoint"),
                                "pointLatitude",
                            )
                        ),
                    ]
                ),
            ),
            ColumnMeta(
                "geo_location_box",
                lambda row: str(
                    [
                        float_value(
                            dict_value(
                                dict_value(row, "geoLocationBox"),
                                "westBoundLongitude",
                            )
                        ),
                        float_value(
                            dict_value(
                                dict_value(row, "geoLocationBox"),
                                "eastBoundLongitude",
                            )
                        ),
                        float_value(
                            dict_value(
                                dict_value(row, "geoLocationBox"),
                                "southBoundLatitude",
                            )
                        ),
                        float_value(
                            dict_value(
                                dict_value(row, "geoLocationBox"),
                                "northBoundLatitude",
                            )
                        ),
                    ]
                ),
            ),
        ],
    ),
    TableMeta(
        "dc_work_funding_references",
        foreign_key="work_id",
        parent_name="dc_works",
        primary_key="id",
        cursor_class=FundingReferencesCursor,
        columns=[
            ColumnMeta("work_id"),
            ColumnMeta("container_id"),
            ColumnMeta(
                "funder_name", lambda row: dict_value(row, "funderName")
            ),
            ColumnMeta(
                "funder_identifier",
                lambda row: dict_value(row, "funderIdentifier"),
            ),
            ColumnMeta(
                "funder_identifier_type",
                lambda row: dict_value(row, "funderIdentifierType"),
            ),
            ColumnMeta(
                "award_number", lambda row: dict_value(row, "awardNumber")
            ),
            ColumnMeta("award_uri", lambda row: dict_value(row, "awardUri")),
            ColumnMeta(
                "award_title", lambda row: dict_value(row, "awardTitle")
            ),
        ],
    ),
]


# pylint: disable=consider-using-with
# pylint: disable-next=too-many-instance-attributes
class TarFiles:
    """The source of the files residing in the tar.gz file"""

    def __init__(
        self,
        file_path,
        sample,
    ):
        self.file_path = file_path
        self.sample = sample
        self.doi_prefix = None
        self.data_files = []
        self.file_index = -1
        self.reader = None
        self.cached_file_contents_index = None
        self.cached_file_contents = None
        self.generator = self.tar_file_generator()

        try:
            self.tar = tarfile.open(file_path, "r|gz")
        except Exception as exc:
            raise Alexandria3kError(f"Error reading file {file_path}") from exc

        # For the progress bar
        self.bytes_read = 0
        self.file_size = os.path.getsize(file_path)

    def tar_file_generator(self):
        """Return a reader object for the next tar file"""
        for self.tar_info in self.tar:
            if not self.tar_info.isreg():
                continue
            # Obtain DOI prefix from file name to avoid extraction and parsing
            (_dot, doi_prefix, file_name) = self.tar_info.name.split("/")
            if not self.sample(file_name):
                continue
            self.doi_prefix = doi_prefix
            self.data_files.append(doi_prefix + "/" + file_name)
            self.file_index += 1
            yield self.file_index

    def get_file_contents(self, file_index):
        """Return the contents of the file at the specified index"""
        while True:
            try:
                if self.file_index == file_index:
                    if self.cached_file_contents_index != self.file_index:
                        reader = self.tar.extractfile(self.tar_info)
                        self.cached_file_contents = reader.read()
                        self.bytes_read += len(self.cached_file_contents)
                        self.cached_file_contents_index = self.file_index
                    return self.cached_file_contents
                next(self.generator)
            except tarfile.ReadError as e:
                if "unexpected end of data" in str(e):
                    return None
            except StopIteration:
                return None

    def get_bytes_read(self):
        """Return the number of uncompressed bytes read from the tar file"""
        return self.bytes_read

    def get_file_size(self):
        """Return an estimate of the uncompressed tar file size"""
        # Numbers obtained from a 2024 download
        COMPRESSED_SIZE = 23278506008
        UNCOMPRESSED_SIZE = 212034252800
        return self.file_size * UNCOMPRESSED_SIZE / COMPRESSED_SIZE

    def get_file_path(self):
        """Return tar file path"""
        return self.file_path

    def get_container_iterator(self):
        """Return an iterator over the int identifiers of all tar data files"""
        return self.generator

    def get_container_name(self, fid):
        """Return the name of the file corresponding to the specified fid"""
        return self.data_files[fid]


class TarFilesCursor(ItemsCursor):
    """A cursor that iterates over the elements in a tar file
    Not used directly by an SQLite table"""

    def __init__(self, table):
        """Not part of the apsw VTCursor interface.
        The table argument is a StreamingTable object"""
        super().__init__(table)
        self.data_source = table.data_source

    def debug_progress_bar(self):
        """Print a progress bar"""
        GB = 1024 * 1024 * 1024
        total_size = self.data_source.get_file_size() / GB
        current_progress = self.data_source.get_bytes_read() / GB

        percent = current_progress / total_size * 100
        progress_marker = int(
            PROGRESS_BAR_LENGTH * current_progress / total_size
        )
        progress_bar = "#" * progress_marker + "-" * (
            PROGRESS_BAR_LENGTH - progress_marker
        )
        debug.log(
            "progress_bar",
            f"\r[{progress_bar}] {percent:.1f}% | "
            f"Processed {current_progress:.0f} GB out of ~{total_size:.0f} GB",
            end="",
        )

    def current_row_value(self):
        """Return the current row. Not part of the apsw API."""
        return self.items

    def Filter(self, index_number, _index_name, constraint_args):
        """Always called first to initialize an iteration to the first
        (possibly constrained) row of the table"""
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

        self.file_index += 1
        content = self.data_source.get_file_contents(self.file_index)
        if content:
            self.eof = False
            # readlines() and "for line in file_reader" fail with:
            # tarfile.StreamError: seeking backwards is not allowed
            # Therefore, read all the content and then split into lines.
            self.items = content.splitlines()
            # The single file has been read. Set EOF in next Next call
            self.file_read = True
            self.debug_progress_bar()
        else:
            self.eof = True


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


class Datacite(DataSource):
    """
    Create an object containing DataCite meta-data that supports
    queries over its (virtual) table and the population of an SQLite database
    with its data.

    :param data_source: The file path to the DataCite .tar.gz file
    :type data_source: str

    :param sample: A callable to row sampling, defaults to `lambda n: True`.
        The population or query method will call this argument
        for each record with the record's data as its argument.  When the
        callable returns `True` the record will get processed, when it
        returns `False` the record will get skipped.
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
        data_source,
        sample=lambda n: True,
        attach_databases=None,
    ):
        super().__init__(
            VTSource(data_source, sample),
            tables,
            attach_databases,
        )
