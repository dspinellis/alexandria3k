# test_issn_subject_codes.py

import os
import sqlite3
import unittest
from unittest.mock import patch, MagicMock
import csv
from pybliometrics.scopus import SerialSearch

from alexandria3k.common import ensure_unlinked, query_result
from alexandria3k.data_sources import issn_subject_codes
from ..test_dir import add_src_dir, td

add_src_dir()

DATABASE_PATH = td("tmp/issn_subjects.db")
INPUT_FILE_PATH = td("data/issn_subjects.csv")
CONFIG_PATH = td("data/pybliometrics.cfg")


class TestIssnSubjectCodesPopulateVanilla(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_unlinked(DATABASE_PATH)
        cls.con = sqlite3.connect(DATABASE_PATH)
        cls.cursor = cls.con.cursor()

        # Ensure tables are dropped before creating
        cls.cursor.executescript("""
            DROP TABLE IF EXISTS issn_subject_codes;
            DROP TABLE IF EXISTS works;
            DROP TABLE IF EXISTS asjcs;
            CREATE TABLE works (
                id INTEGER PRIMARY KEY,
                issn_print TEXT,
                issn_electronic TEXT
            );
            CREATE TABLE asjcs (
                id INTEGER PRIMARY KEY,
                code INTEGER
            );
        """)

        # Populate the works table with some test data
        cls.cursor.executemany(
            "INSERT INTO works (issn_print, issn_electronic) VALUES (?, ?)",
            [('03636127', '03636127'), ('15221466', '15221466'), ('1931857X', '1931857X'), ('08203946', '08203946'), ('14882329', '14882329'), ('10400605', '10400605')]
        )
        cls.con.commit()

        cls.issn_subject_codes = issn_subject_codes.IssnSubjectCodes(
            data_source=INPUT_FILE_PATH,
            config_path=CONFIG_PATH
        )

        # Mocking the API call to return specific subject codes for each ISSN
        def mock_serial_search_init(self, query, view):
            self.query = query
            self.view = view

        # Mocking the API call to return specific subject codes for each ISSN
        def mock_serial_search_results(self, query, view):
            self.results = []
            issn = query.get('issn')
            if issn == '03636127':
                self.results = [{'subject_area_codes': '3956'}]
            elif issn == '15221466':
                self.results = [{'subject_area_codes': '3956'}]
            elif issn == '1931857X':
                self.results = [{'subject_area_codes': '3956'}]
            elif issn == '08203946':
                self.results = [{'subject_area_codes': '3177'}]
            elif issn == '14882329':
                self.results = [{'subject_area_codes': '3177'}]
            elif issn == '10400605':
                self.results = [{'subject_area_codes': '2377'}]

        with patch.object(SerialSearch, '__init__', mock_serial_search_init), \
             patch.object(SerialSearch, 'results', new_callable=MagicMock, return_value=mock_serial_search_results):
            cls.issn_subject_codes.populate(database_path=DATABASE_PATH)

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        os.remove(DATABASE_PATH)

    def record_count(self, table):
        result = query_result(self.cursor, f"SELECT COUNT(*) FROM {table}")
        return result if isinstance(result, int) else result[0] if result else 0

    def cond_field(self, table, field, condition):
        result_set = self.cursor.execute(f"SELECT {field} FROM {table} WHERE {condition}").fetchone()
        if result_set is None:
            return None
        return result_set[0]

    def test_counts(self):
        self.assertEqual(self.record_count("issn_subject_codes"), 6)

    def test_contents(self):
        result = self.cond_field("issn_subject_codes", "subject_code", "issn = '03636127'")
        self.assertIsNotNone(result, "The subject_code for issn '03636127' should not be None")
        self.assertEqual(int(result), 3956)

        result = self.cond_field("issn_subject_codes", "subject_code", "issn = '08203946'")
        self.assertIsNotNone(result, "The subject_code for issn '08203946' should not be None")
        self.assertEqual(int(result), 3177)

    def test_csv_creation(self):
        self.assertTrue(os.path.exists(INPUT_FILE_PATH))
        # Read csv
        with open(INPUT_FILE_PATH, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            self.assertEqual(rows[0], ['issn', 'subject_code'])
            self.assertEqual(rows[1:], [['03636127', '3956'], ['15221466', '3956'], ['1931857X', '3956'],
                                        ['08203946', '3177'], ['14882329', '3177'], ['10400605', '2377']])
            self.assertEqual(len(rows), 7)