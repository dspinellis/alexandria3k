import unittest
from unittest.mock import patch
from alexandria3k.__main__ import download
import argparse

# Mock classes for testing
class MockArgs:
    def __init__(self, database, sql_query, data_location, extra_args):
        self.database = database
        self.sql_query = sql_query
        self.data_location = data_location
        self.extra_args = extra_args or []  # Ensure extra_args is an iterable
        
    def validate_args(self, args):
        """Validate that both database and sql_query are either both provided or both omitted."""
        if bool(args.database) != bool(args.sql_query):
            raise argparse.ArgumentTypeError(
                "Both --database and --sql-query must be provided together or not at all."
            )
        return args

class MockDataSource:
    def download(self, database, sql_query, data_location, *extra_args):
        self.database = database
        self.sql_query = sql_query
        self.data_location = data_location
        self.extra_args = extra_args

# Test case
class TestDownloadFunction(unittest.TestCase):
    @patch('alexandria3k.__main__.get_data_source_instance')
    @patch('alexandria3k.__main__.perf.log')
    def test_download_function(self, mock_log, mock_get_data_source_instance):
        mock_args = MockArgs(
            database='test_db',
            sql_query='SELECT * FROM test_table',
            data_location='/path/to/data',
            extra_args=None  # No extra args
        )
        mock_data_source_instance = MockDataSource()
        mock_get_data_source_instance.return_value = mock_data_source_instance

        # Call the function
        download(mock_args)

        # Assert the download method was called with correct arguments
        mock_get_data_source_instance.assert_called_once_with(mock_args)
        self.assertEqual(mock_data_source_instance.database, 'test_db')
        self.assertEqual(mock_data_source_instance.sql_query, 'SELECT * FROM test_table')
        self.assertEqual(mock_data_source_instance.data_location, '/path/to/data')
        self.assertEqual(mock_data_source_instance.extra_args, ())

        # Assert the log function was called correctly
        mock_log.assert_called_once_with('Data downloaded and saved to /path/to/data')
