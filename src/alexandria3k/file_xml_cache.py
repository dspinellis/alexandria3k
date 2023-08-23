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
"""Cache of read and parsed XML files"""

import xml.etree.ElementTree as ET


class FileCache:
    """Cache the reading of a single concatenated XML file"""

    # pylint: disable=too-few-public-methods
    parse_counter = 0

    def __init__(self):
        self.cached_patent_xml_id = None
        self.cached_data = None

    def read(self, xml_chunk, container_id):
        """
        Compares container_id with cached_patent_xml_id. Return
        the parsed contents of the specified container id in etree
        form. Repeated parsing is avoided through caching.

        :param xml_chunk: A string containing the contents of a XML file,
            representing a complete US patent.

        :param container_id: An int identifier of US patents.

        """

        if container_id == self.cached_patent_xml_id:
            return self.cached_data

        self.cached_data = ET.fromstring(xml_chunk)
        self.cached_patent_xml_id = container_id

        FileCache.parse_counter += 1
        return self.cached_data


# Default
file_cache = FileCache()


def get_file_cache():
    """Return the file cache used"""
    return file_cache
