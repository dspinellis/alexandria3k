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
"""XML getter functions test"""

import unittest
from xml.etree import ElementTree as ET

from .test_dir import add_src_dir

add_src_dir()

from alexandria3k.xml import *


class TestXMLFunctions(unittest.TestCase):
    def setUp(self):
        # Example XML tree for testing
        self.xml_data = """
            <us-patent-grant file="US11617522-20230404.XML">
                <us-bibliographic-data-grant attribute="Value2">
                    <element1>Value1</element1>
                    <element2 id="2">Text</element2>
                    <element id="3">Value3</element>
                    <element id="4">Value4</element>
                </us-bibliographic-data-grant>
            </us-patent-grant>
        """
        self.tree = ET.fromstring(self.xml_data)

    def test_get_element_existing(self):
        self.assertEqual(
            get_element(
                self.tree,
                "us-bibliographic-data-grant/element1",
            ),
            "Value1",
        )
        self.assertEqual(
            get_element(
                self.tree,
                "us-bibliographic-data-grant/element2",
            ),
            "Text",
        )

    def test_get_element_non_existing(self):
        self.assertIsNone(
            get_element(
                self.tree,
                "us-bibliographic-data-grant/element3",
            ),
            "non_existin_value",
        )

    def test_get_attribute_root(self):
        self.assertEqual(get_attribute(self.tree, "file"), "US11617522-20230404.XML")

    def test_get_attribute_existing_element(self):
        self.assertEqual(
            get_attribute(self.tree, "attribute", "us-bibliographic-data-grant"),
            "Value2",
        )

    def test_get_attribute_non_existing_element(self):
        self.assertIsNone(get_attribute(self.tree, "attribute", "non_existent_element"))

    def test_getter(self):
        path = "us-bibliographic-data-grant/element2"
        element_getter = getter(path)
        self.assertEqual(element_getter(self.tree), "Text")

    def test_agetter_root(self):
        attribute_name = "file"
        attribute_getter = agetter(attribute_name)
        self.assertEqual(attribute_getter(self.tree), "US11617522-20230404.XML")

    def test_agetter_existing_element(self):
        attribute_name = "id"
        path = "us-bibliographic-data-grant/element2"
        attribute_getter = agetter(attribute_name, path)
        self.assertEqual(attribute_getter(self.tree), "2")

    def test_agetter_non_existing_element(self):
        attribute_name = "attribute"
        path = "non_existent_element"
        attribute_getter = agetter(attribute_name, path)
        self.assertIsNone(attribute_getter(self.tree))

    def test_all_getter(self):
        path = "us-bibliographic-data-grant/"
        all_elements_getter = all_getter(path)
        elements = all_elements_getter(self.tree)
        self.assertEqual(len(elements), 4)
        self.assertEqual(elements[0].text, "Value1")

    def test_getter_by_attribute(self):
        attribute_name = "id"
        attribute_value = "4"
        path = "us-bibliographic-data-grant/"
        element_getter = getter_by_attribute(attribute_name, attribute_value, path)
        self.assertEqual(element_getter(self.tree), "Value4")

    def test_lower(self):
        path = "us-bibliographic-data-grant/element1"
        element_getter = getter(path)
        lower_element_getter = lower(element_getter)
        self.assertEqual(lower_element_getter(self.tree), "value1")

    def test_lower_none_value(self):
        path = "us-bibliographic-data-grant/elementx"
        element_getter = getter(path)
        lower_element_getter = lower(element_getter)
        self.assertEqual(lower_element_getter(self.tree), None)

    def test_get_root_text(self):
        path = "us-bibliographic-data-grant/"
        all_elements_getter = all_getter(path)
        element = all_elements_getter(self.tree)[0]
        self.assertEqual(get_root_text()(element), "Value1")


if __name__ == "__main__":
    unittest.main()
