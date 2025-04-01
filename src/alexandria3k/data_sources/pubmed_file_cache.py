#
# Alexandria2k Crossref bibliographic metadata processing
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
"""Cache of read/uncompressed/processed files"""

import gzip
import xml.etree.ElementTree as ET


class FileCache:
    """Cache the reading/decompression/parsing of a single compressed
    XML file"""

    # pylint: disable=too-few-public-methods

    file_reads = 0

    def __init__(self):
        self.cached_path = None
        self.cached_data = None

    def read(self, path):
        """Read the compressed XML file at the specified path and return
        its parsed contents"""

        if path == self.cached_path:
            return self.cached_data

        with gzip.open(path, "rb") as uncompressed_file:
            self.cached_data = ET.parse(uncompressed_file).getroot()
        self.cached_path = path
        FileCache.file_reads += 1
        return self.cached_data


# Default
file_cache = FileCache()


def get_file_cache():
    """Return the file cache used"""
    return file_cache
