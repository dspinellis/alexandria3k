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
"""Cache of decompressed/extracted path of US patent data"""

import zipfile

# Delimiter for extracting concatenated XML files.
XML_DELIMITER = '<?xml version="1.0" encoding="UTF-8"?>'


class UsptoZipCache:
    """Cache the reading/decompression/extraction of Zip file"""

    # pylint: disable=too-few-public-methods
    file_reads = 0

    def __init__(self):
        self.cached_path = None
        self.cached_data = []
        self.file_name = None

    def read(self, zip_path, sampling=lambda n: True):
        """Return a list of XML containers in the specified zip file.

        :param zip_path: Path to the Zip file.

        :param sampling: callable
        """

        # Compare Zip path for caching.
        if zip_path == self.cached_path:
            return self.cached_data

        self.cached_data = []
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # There is only one XML file inside the Zip file.
            xml_file = [
                file for file in zip_ref.namelist() if file.endswith(".xml")
            ]

            # Extract filename and decoding the XML
            (self.file_name,) = xml_file
            xml_content = zip_ref.read(self.file_name).decode("utf-8")

            # The first item of the list is None.
            patent_xml_files_list = xml_content.split(XML_DELIMITER)[1:]

            # When sampling returns False it will skip the container.
            # Sample the patents inside the Zip file by passing to the sampling
            # function a tuple with the designator string being "container"
            # and the second value being a string that contains all the
            # contents of a unique US patent.
            # (e.g. random.random() < 0.1 if data[0] == ""container"" else True)
            self.cached_data = [
                patent_xml
                for patent_xml in patent_xml_files_list
                if sampling(("container", patent_xml))
            ]
            self.cached_path = zip_path
            UsptoZipCache.file_reads += 1
        return self.cached_data


# Default
file_cache = UsptoZipCache()


def get_zip_cache():
    """Return the file cache used"""
    return file_cache
