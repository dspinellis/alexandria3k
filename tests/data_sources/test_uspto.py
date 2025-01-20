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
"""USPTO import integration tests"""

import os
import unittest
import sqlite3

from ..test_dir import add_src_dir, td

add_src_dir()

from ..common import PopulateQueries, record_count
from alexandria3k.common import ensure_unlinked
from alexandria3k.data_sources import uspto
from alexandria3k.file_xml_cache import FileCache
from alexandria3k.uspto_zip_cache import UsptoZipCache
from alexandria3k import debug


DATABASE_PATH = td("tmp/uspto.db")
ATTACHED_DATABASE_PATH = td("tmp/attached_uspto.db")


def populate_attached():
    """Create and populate an attached database"""
    ensure_unlinked(ATTACHED_DATABASE_PATH)
    attached = sqlite3.connect(ATTACHED_DATABASE_PATH)
    attached.execute("CREATE TABLE s_us_patents(type)")
    attached.execute("INSERT INTO s_us_patents VALUES('design')")
    attached.commit()
    attached.close()


class TestUsptoPopulateVanilla(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(DATABASE_PATH):
            os.unlink(DATABASE_PATH)

        FileCache.parse_counter = 0
        UsptoZipCache.file_reads = 0
        cls.uspto = uspto.Uspto(td("data/uspto-2023-04"))
        cls.uspto.populate(DATABASE_PATH)
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.uspto.close()

    def test_import(
        self,
    ):
        result = TestUsptoPopulateVanilla.cursor.execute(
            f"SELECT Count(*) from us_patents"
        )
        (count,) = result.fetchone()
        self.assertEqual(count, 14)
        self.assertEqual(UsptoZipCache.file_reads, 2)
        UsptoZipCache.file_reads = 0

    def test_type(
        self,
    ):
        result = TestUsptoPopulateVanilla.cursor.execute(
            f"""SELECT type FROM us_patents
            WHERE filename='USPP034694-20221025.XML'"""
        )
        (type,) = result.fetchone()
        self.assertEqual(type, "plant")

    def test_primary_examiner(
        self,
    ):
        result = TestUsptoPopulateVanilla.cursor.execute(
            f"""SELECT primary_examiner_firstname, primary_examiner_lastname FROM us_patents
            WHERE filename='USRE049258-20221025.XML'"""
        )
        (name, lastname) = result.fetchone()
        self.assertEqual(name, "Catherine M")
        self.assertEqual(lastname, "Tarae")

    def test_counts(self):
        self.assertEqual(self.record_count("us_patents"), 14)
        self.assertEqual(self.record_count("usp_icpr_classifications"), 30)

        self.assertEqual(
            self.record_count(
                """(SELECT DISTINCT type
          FROM us_patents)"""
            ),
            4,
        )

        self.assertEqual(
            self.record_count(
                """(SELECT DISTINCT primary_examiner_firstname
          FROM us_patents)"""
            ),
            12,
        )

        self.assertEqual(self.cond_count("us_patents", "series_code = '17'"), 3)
        self.assertEqual(FileCache.parse_counter, 14)


class TestUsptoPopulateMasterCondition(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(DATABASE_PATH):
            os.unlink(DATABASE_PATH)

        # debug.set_flags(["sql", "dump-matched"])

        FileCache.parse_counter = 0
        cls.uspto = uspto.Uspto(td("data/uspto-2023-04"))
        cls.uspto.populate(DATABASE_PATH, None, "us_patents.type = 'plant'")
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.uspto.close()

    def test_counts(self):
        self.assertEqual(self.record_count("us_patents"), 1)
        self.assertEqual(self.record_count("usp_icpr_classifications"), 2)
        self.assertEqual(FileCache.parse_counter, 14)


class TestUsptoPopulateDetailCondition(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.parse_counter = 0
        # debug.set_flags(["sql", "dump-matched"])

        cls.uspto = uspto.Uspto(td("data/uspto-2023-04"))
        cls.uspto.populate(
            DATABASE_PATH, None, "usp_icpr_classifications.subclass = 'G'"
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.uspto.close()

    def test_counts(self):
        self.assertEqual(self.record_count("us_patents"), 3)
        # Patent with filename "US11477945-20221025.XML" contains 3
        # icpr classifications. 2/3 are of subclass type G.
        # Watch out on the definition of populate().
        # "if a main table is populated, its details tables
        # will only get populated with the records associated with the
        # corresponding main table's record". That's why the icpr classifications are 5 and not 4.
        self.assertEqual(self.record_count("usp_icpr_classifications"), 5)
        self.assertEqual(FileCache.parse_counter, 14)


class TestUsptoPopulateMasterColumnNoCondition(PopulateQueries):
    """Verify column specification and population of root table"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.parse_counter = 0

        # debug.set_flags(["sql"])
        cls.uspto = uspto.Uspto(td("data/uspto-2023-04"))
        cls.uspto.populate(DATABASE_PATH, ["us_patents.type"])
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.uspto.close()

    def test_counts(self):
        self.assertEqual(self.record_count("us_patents"), 14)
        self.assertEqual(FileCache.parse_counter, 14)

    def test_no_extra_fields(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("us_patents", "country", "true")

    def test_no_extra_tables(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("usp_icpr_classifications", "class_level", "true")


class TestUsptoPopulateMasterColumnCondition(PopulateQueries):
    """Verify column specification and population of root table"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.parse_counter = 0

        # debug.set_flags(["sql"])
        cls.uspto = uspto.Uspto(td("data/uspto-2023-04"))
        cls.uspto.populate(
            DATABASE_PATH,
            ["us_patents.drawings_number"],
            "us_patents.id between 6 and 9",
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.uspto.close()

    def test_counts(self):
        self.assertEqual(self.record_count("us_patents"), 4)
        self.assertEqual(FileCache.parse_counter, 14)

    def test_no_extra_fields(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("us_patents", "country", "true")

    def test_no_extra_tables(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("usp_icpr_classifications", "class_level", "true")


class TestUsptoPopulateDetailConditionColumn(PopulateQueries):
    """Verify column specification and population of root table"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.parse_counter = 0

        # debug.set_flags(["sql"])
        cls.uspto = uspto.Uspto(td("data/uspto-2023-04"))
        cls.uspto.populate(
            DATABASE_PATH,
            ["us_patents.drawings_number", "usp_icpr_classifications.*"],
            "us_patents.type = 'reissue'",
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.uspto.close()

    def test_counts(self):
        self.assertEqual(self.record_count("us_patents"), 3)
        self.assertEqual(self.record_count("usp_icpr_classifications"), 13)
        self.assertEqual(FileCache.parse_counter, 14)

    def test_no_extra_fields(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("us_patents", "country", "true")


class TestUsptoPopulateMultipleConditionColumn(PopulateQueries):
    """Verify column specification and population of root table"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.parse_counter = 0

        # debug.set_flags(["sql"])
        cls.uspto = uspto.Uspto(td("data/uspto-2023-04"))
        cls.uspto.populate(
            DATABASE_PATH,
            ["us_patents.figures_number"],
            "us_patents.type = 'utility' AND usp_icpr_classifications.symbol_position = 'F'",
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.uspto.close()

    def test_counts(self):
        self.assertEqual(self.record_count("us_patents"), 6)
        self.assertEqual(FileCache.parse_counter, 14)

    def test_no_extra_fields(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("us_patents", "language", "true")

    def test_no_extra_tables(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.cond_field("usp_icpr_classifications", "class_level", "true")


class TestUsptoTransitive(unittest.TestCase):
    """Verify column specification and population of root table"""

    @classmethod
    def setUpClass(cls):
        populate_attached()

        # debug.set_flags(["sql"])
        cls.uspto = uspto.Uspto(
            td("data/uspto-2023-04"),
            attach_databases=[f"attached_uspto:{ATTACHED_DATABASE_PATH}"],
        )

    @classmethod
    def tearDownClass(cls):
        del cls.uspto
        os.unlink(ATTACHED_DATABASE_PATH)

    def test_single(self):
        self.assertEqual(
            self.uspto.tables_transitive_closure(["us_patents"], "us_patents"),
            set(["us_patents"]),
        )

    def test_child(self):
        self.assertEqual(
            self.uspto.tables_transitive_closure(
                ["usp_icpr_classifications"], "us_patents"
            ),
            set(["us_patents", "usp_icpr_classifications"]),
        )


class TestUsptoQuery(unittest.TestCase):
    """Verify column specification and population of root table"""

    @classmethod
    def setUpClass(cls):
        FileCache.parse_counter = 0
        UsptoZipCache.file_reads = 0
        populate_attached()

        # debug.set_flags(["sql"])
        cls.uspto = uspto.Uspto(
            td("data/uspto-2023-04"),
            attach_databases=[f"attached_uspto:{ATTACHED_DATABASE_PATH}"],
        )

    @classmethod
    def tearDownClass(cls):
        del cls.uspto
        os.unlink(ATTACHED_DATABASE_PATH)

    def test_patents(self):
        for partition in True, False:
            self.assertEqual(
                record_count(self.uspto.query("SELECT * FROM us_patents", partition)),
                14,
            )
        self.assertEqual(FileCache.parse_counter, 27)
        FileCache.parse_counter = 0

    def test_cache(self):
        self.assertEqual(
            record_count(self.uspto.query("SELECT * FROM us_patents LIMIT 1")),
            1,
        )
        self.assertEqual(FileCache.parse_counter, 1)
        self.assertEqual(UsptoZipCache.file_reads, 1)
        FileCache.parse_counter = 0
        UsptoZipCache.file_reads = 0

    def test_patents_attached(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.uspto.query(
                        """SELECT * FROM us_patents WHERE EXISTS (
                SELECT 1 FROM attached_uspto.s_us_patents WHERE us_patents.type = s_us_patents.type)
            """,
                        partition,
                    )
                ),
                4,
            )
        self.assertEqual(FileCache.parse_counter, 28)
        FileCache.parse_counter = 0
        UsptoZipCache.file_reads = 0

    def test_usp_icpr_classifications(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.uspto.query(
                        "SELECT * FROM usp_icpr_classifications", partition
                    )
                ),
                30,
            )
        self.assertEqual(FileCache.parse_counter, 28)
        FileCache.parse_counter = 0
        UsptoZipCache.file_reads = 0

    def test_usp_cpc_classifications(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.uspto.query("SELECT * FROM usp_cpc_classifications", partition)
                ),
                20,
            )
        self.assertEqual(FileCache.parse_counter, 28)
        FileCache.parse_counter = 0
        UsptoZipCache.file_reads = 0

    def test_usp_related_documents(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.uspto.query("SELECT * FROM usp_related_documents", partition)
                ),
                22,
            )
        self.assertEqual(FileCache.parse_counter, 28)
        FileCache.parse_counter = 0
        UsptoZipCache.file_reads = 0

    def test_usp_field_of_classification(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.uspto.query(
                        "SELECT * FROM usp_field_of_classification", partition
                    )
                ),
                14,
            )
        self.assertEqual(FileCache.parse_counter, 28)
        FileCache.parse_counter = 0
        UsptoZipCache.file_reads = 0

    def test_usp_inventors(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.uspto.query("SELECT * FROM usp_inventors", partition)
                ),
                33,
            )
        self.assertEqual(FileCache.parse_counter, 28)
        FileCache.parse_counter = 0
        UsptoZipCache.file_reads = 0

    def test_usp_applicants(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.uspto.query("SELECT * FROM usp_applicants", partition)
                ),
                14,
            )
        self.assertEqual(FileCache.parse_counter, 28)
        FileCache.parse_counter = 0
        UsptoZipCache.file_reads = 0

    def test_usp_agents(self):
        for partition in True, False:
            self.assertEqual(
                record_count(self.uspto.query("SELECT * FROM usp_agents", partition)),
                19,
            )
        self.assertEqual(FileCache.parse_counter, 28)
        FileCache.parse_counter = 0
        UsptoZipCache.file_reads = 0

    def test_usp_assignees(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.uspto.query("SELECT * FROM usp_assignees", partition)
                ),
                11,
            )
        self.assertEqual(FileCache.parse_counter, 28)
        FileCache.parse_counter = 0
        UsptoZipCache.file_reads = 0

    def test_usp_citations(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.uspto.query("SELECT * FROM usp_citations", partition)
                ),
                1073,
            )
        self.assertEqual(FileCache.parse_counter, 28)
        FileCache.parse_counter = 0
        UsptoZipCache.file_reads = 0

    def test_usp_patent_family(self):
        for partition in True, False:
            self.assertEqual(
                record_count(
                    self.uspto.query("SELECT * FROM usp_patent_family", partition)
                ),
                0,
            )
        self.assertEqual(FileCache.parse_counter, 28)
        FileCache.parse_counter = 0
        UsptoZipCache.file_reads = 0

    def test_patents_claims_condition(self):
        for partition in False, True:
            self.assertEqual(
                record_count(
                    self.uspto.query(
                        "SELECT us_patents.language FROM us_patents INNER JOIN"
                        + " usp_icpr_classifications ON us_patents.container_id = "
                        + " usp_icpr_classifications.patent_id WHERE us_patents.type = 'utility'"
                        + " AND usp_icpr_classifications.symbol_position = 'F'",
                        partition,
                    )
                ),
                6,
            )
        FileCache.parse_counter = 0
        UsptoZipCache.file_reads = 0

    def test_patents_column_subset_condition(self):
        for partition in False, True:
            self.assertEqual(
                record_count(
                    self.uspto.query(
                        "SELECT us_patents.claims_number,  usp_icpr_classifications.main_group "
                        + "FROM us_patents INNER JOIN usp_icpr_classifications ON us_patents."
                        + "container_id = usp_icpr_classifications.patent_id WHERE us_patents.type"
                        + " = 'utility' AND usp_icpr_classifications.symbol_position = 'L'",
                        partition,
                    )
                ),
                9,
            )
        FileCache.parse_counter = 0
        UsptoZipCache.file_reads = 0


class TestUsptoPopulateAttachedDatabaseCondition(PopulateQueries):
    """Verify column specification and population of single table"""

    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        FileCache.parse_counter = 0
        populate_attached()

        # debug.set_flags(["sql"])
        cls.uspto = uspto.Uspto(
            td("data/uspto-2023-04"),
            attach_databases=[f"attached_uspto:{ATTACHED_DATABASE_PATH}"],
        )
        cls.uspto.populate(
            DATABASE_PATH,
            ["us_patents.type"],
            "EXISTS (SELECT 1 FROM attached_uspto.s_us_patents WHERE us_patents.type = s_us_patents.type)",
        )
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        os.unlink(ATTACHED_DATABASE_PATH)
        cls.uspto.close()

    def test_counts(self):
        self.assertEqual(self.record_count("us_patents"), 4)
        self.assertEqual(FileCache.parse_counter, 14)


class TestUsptoSamplingContainer(PopulateQueries):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(DATABASE_PATH):
            os.unlink(DATABASE_PATH)

        FileCache.parse_counter = 0
        UsptoZipCache.file_reads = 0
        cls.uspto = uspto.Uspto(
            td("data/uspto-2023-04"),
            sample=lambda data: True
            if (data[0] == "path")
            else True
            if ("exercise" in data[1])
            else False,
        )
        cls.uspto.populate(DATABASE_PATH)
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.unlink(DATABASE_PATH)
        cls.uspto.close()

    def test_import(
        self,
    ):
        result = TestUsptoSamplingContainer.cursor.execute(
            f"SELECT Count(*) from us_patents"
        )
        (count,) = result.fetchone()
        self.assertEqual(count, 1)
        self.assertEqual(UsptoZipCache.file_reads, 2)
        UsptoZipCache.file_reads = 0
