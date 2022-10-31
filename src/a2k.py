import apsw
import gzip
import json
import os
import sqlite3
from uuid import uuid4
import sys

full_print = False


def get_data_files(directory):
    columns = None
    data_files = []
    counter = 1
    for f in os.listdir(directory):
        path = os.path.join(directory, f)
        if not os.path.isfile(path):
            continue
        counter += 1
        data_files.append(path)
    return data_files


def dict_value(d, k):
    """Return the value of dict d for key or None if it doesn't exist"""
    if not d:
        return None
    try:
        return d[k]
    except KeyError:
        return None


def array_value(a, i):
    """Return the value of array a for index i or None if it doesn't exist"""
    try:
        return a[i]
    except (IndexError, TypeError):
        return None


def author_orcid(row):
    """Return the ISNI part of an ORCID URL or None if missing"""
    orcid = row.get("ORCID")
    if orcid:
        return orcid[17:]
    return None


def boolean_value(d, k):
    """Return 0, 1, or None for the corresponding JSON value for key k
    of dict d"""
    if not d:
        return None
    try:
        v = d[k]
    except KeyError:
        return None
    if v:
        return 1
    return 0


def first_value(a):
    """Return the first element of array a or None if it doesn't exist"""
    return array_value(a, 0)


work_columns = [
    ("DOI", lambda row: dict_value(row, "DOI")),
    ("title", lambda row: first_value(dict_value(row, "title"))),
    (
        "work_year",
        lambda row: array_value(
            first_value(dict_value(dict_value(row, "published"), "date-parts")),
            0,
        ),
    ),
    (
        "work_month",
        lambda row: array_value(
            first_value(dict_value(dict_value(row, "published"), "date-parts")),
            1,
        ),
    ),
    (
        "work_day",
        lambda row: array_value(
            first_value(dict_value(dict_value(row, "published"), "date-parts")),
            2,
        ),
    ),
]

author_columns = [
    ("doi", None),
    ("id", None),
    ("orcid", lambda row: author_orcid(row)),
    ("suffix", lambda row: dict_value(row, "suffix")),
    ("given", lambda row: dict_value(row, "given")),
    ("family", lambda row: dict_value(row, "family")),
    ("name", lambda row: dict_value(row, "name")),
    (
        "authenticated_orcid",
        lambda row: boolean_value(row, "authenticated-orcid"),
    ),
    ("prefix", lambda row: dict_value(row, "prefix")),
    ("sequence", lambda row: dict_value(row, "sequence")),
]

affiliation_columns = [
    ("author_id", None),
    ("name", lambda row: dict_value(row, "name")),
]


def table_columns(columns):
    """Return a comma-separated list of a table's columns"""
    return ",".join([f"'{name}'" for (name, _) in columns])


def table_schema(table_name, columns):
    """Return the SQL command to create a table's schema"""
    return f"CREATE TABLE {table_name}(" + table_columns(columns) + ")"


# This gets registered with the Connection
class Source:
    def __init__(self):
        self.data_files = None

    def Create(self, db, module_name, db_name, table_name, data_directory):
        if not self.data_files:
            self.data_files = get_data_files(data_directory)
        if table_name == "works":
            return table_schema(table_name, work_columns), StreamingTable(
                work_columns, self.data_files, WorksCursor
            )
        if table_name == "authors":
            return table_schema(table_name, author_columns), StreamingTable(
                author_columns, self.data_files, AuthorsCursor
            )

        if table_name == "affiliations":
            return table_schema(
                table_name, affiliation_columns
            ), StreamingTable(
                affiliation_columns, self.data_files, AffiliationsCursor
            )

    Connect = Create


class StreamingTable:
    """A table streaming over data through a supplied cursor class"""

    def __init__(self, columns, data_files, cursor_class):
        self.columns = columns
        self.data_files = data_files
        self.cursor_class = cursor_class

    def BestIndex(self, *args):
        return None

    def Disconnect(self):
        pass

    Destroy = Disconnect

    def Open(self):
        return self.cursor_class(self)


class FilesCursor:
    """A cursor over the items data files. Internal use only. Not used by a table."""

    def __init__(self, table):
        self.table = table

    def Filter(self, *args):
        """Always called first to initialize an iteration to the first row of the table"""
        self.file_index = -1
        self.Next()

    def Next(self):
        """Advance reading to the next available file. Files are assumed to be non-empty."""
        if self.file_index + 1 >= len(self.table.data_files):
            self.eof = True
            return
        self.file_index += 1
        with gzip.open(self.table.data_files[self.file_index], "rb") as f:
            file_content = f.read()
            self.items = json.loads(file_content)["items"]
        self.eof = False

    def Rowid(self):
        return self.file_index

    def Row(self):
        """Return the current row. Not part of the apsw API."""
        return self.items

    def Eof(self):
        return self.eof

    def Close(self):
        self.items = None


class WorksCursor:
    """A cursor over the works data."""

    def __init__(self, table):
        self.table = table
        self.files_cursor = FilesCursor(table)

    def Eof(self):
        return self.eof

    def Rowid(self):
        # Allow for 65k items per file (currently 5k)
        return (self.files_cursor.Rowid() << 16) | (self.item_index)

    def Row(self):
        """Return the current row. Not part of the apsw API."""
        return self.files_cursor.Row()[self.item_index]

    def Column(self, col):
        if col == -1:
            return self.Rowid()
        (_, extract_function) = self.table.columns[col]
        return extract_function(self.Row())

    def Filter(self, *args):
        """Always called first to initialize an iteration to the first row of the table"""
        self.files_cursor.Filter(*args)
        self.eof = self.files_cursor.Eof()
        self.item_index = 0

    def Next(self):
        """Advance to the next item."""
        self.item_index += 1
        if self.item_index >= len(self.files_cursor.items):
            self.item_index = 0
            self.files_cursor.Next()
            self.eof = self.files_cursor.eof

    def Close(self):
        self.files_cursor.Close()


class AuthorsCursor:
    """A cursor over the items' authors data."""

    def __init__(self, table):
        self.table = table
        self.works_cursor = WorksCursor(table)

    def Filter(self, *args):
        """Always called first to initialize an iteration to the first row of the table"""
        self.works_cursor.Filter(*args)
        self.authors = None
        self.Next()

    def Eof(self):
        return self.eof

    def Rowid(self):
        """This allows for 65k authors. There is a Physics paper with 5k
        authors."""
        return (self.works_cursor.Rowid() << 16) | self.author_index

    def Recordid(self):
        """Return the record's identifier. Not part of the apsw API."""
        # Zero-pad for 60 bits
        return f"{self.Rowid():015X}"

    def Row(self):
        """Return the current row. Not part of the apsw API."""
        return self.authors[self.author_index]

    def Column(self, col):
        if col == -1:
            return self.Rowid()

        if col == 0:  # DOI
            return self.works_cursor.Row().get("DOI")

        row = self.Row()

        if col == 1:  # id
            return self.Recordid()

        (_, extract_function) = self.table.columns[col]
        return extract_function(row)

    def Next(self):
        """Advance reading to the next available author."""
        while True:
            if self.works_cursor.Eof():
                self.eof = True
                return
            if not self.authors:
                self.authors = self.works_cursor.Row().get("author")
                self.author_index = -1
            if not self.authors:
                self.works_cursor.Next()
                self.authors = None
                continue
            if self.author_index + 1 < len(self.authors):
                self.author_index += 1
                self.eof = False
                return
            self.works_cursor.Next()
            self.authors = None

    def Close(self):
        self.works_cursor.Close()
        self.authors = None


class AffiliationsCursor:
    """A cursor over the authors' affiliation data."""

    def __init__(self, table):
        self.table = table
        self.authors_cursor = AuthorsCursor(table)

    def Filter(self, *args):
        """Always called first to initialize an iteration to the first row of the table"""
        self.authors_cursor.Filter(*args)
        self.affiliations = None
        self.Next()

    def Eof(self):
        return self.eof

    def Rowid(self):
        """This allows for 128 affiliations per author
        authors."""
        return (self.authors_cursor.Rowid() << 7) | self.affiliation_index

    def Row(self):
        """Return the current row. Not part of the apsw API."""
        return self.affiliations[self.affiliation_index]

    def Column(self, col):
        if col == -1:
            return self.Rowid()

        if col == 0:  # Author-id
            return self.authors_cursor.Recordid()

        row = self.Row()

        (_, extract_function) = self.table.columns[col]
        return extract_function(row)

    def Next(self):
        """Advance reading to the next available affiliation ."""
        while True:
            if self.authors_cursor.Eof():
                self.eof = True
                return
            if not self.affiliations:
                self.affiliations = self.authors_cursor.Row().get("affiliation")
                self.affiliation_index = -1
            if not self.affiliations:
                self.authors_cursor.Next()
                self.affiliations = None
                continue
            if self.affiliation_index + 1 < len(self.affiliations):
                self.affiliation_index += 1
                self.eof = False
                return
            self.authors_cursor.Next()
            self.affiliations = None

    def Close(self):
        self.authors_cursor.Close()
        self.affiliations = None


try:
    os.unlink("virtual.db")
except FileNotFoundError:
    pass

try:
    os.unlink("populated.db")
except FileNotFoundError:
    pass

vdb = apsw.Connection("virtual.db")

# Register the module as filesource
vdb.createmodule("filesource", Source())

vdb.execute("CREATE VIRTUAL TABLE works USING filesource(sample)")
vdb.execute("CREATE VIRTUAL TABLE authors USING filesource(sample)")
vdb.execute("CREATE VIRTUAL TABLE affiliations USING filesource(sample)")


def sql_value(statement):
    """Return the first value of the specified SQL statement executed on vdb"""
    (res,) = vdb.execute(statement).fetchone()
    return res


# Streaming interface
if full_print:
    for r in vdb.execute("SELECT * FROM works ORDER BY title"):
        print(r)

count = sql_value("SELECT count(*) FROM works")
print(f"{count} publication(s)")

if full_print:
    for r in vdb.execute("SELECT doi, id, orcid, given, family FROM authors"):
        print(r)

count = sql_value("SELECT count(*) FROM authors")
print(f"{count} author(s)")

count = sql_value(
    """SELECT count(*) from (SELECT DISTINCT orcid FROM authors
                    WHERE orcid is not null)"""
)
print(f"{count} unique author ORCID(s)")

count = sql_value("SELECT count(*) FROM (SELECT DISTINCT doi FROM authors)")
print(f"{count} publication(s) with authors")

count = sql_value("SELECT count(*) FROM affiliations")
print(f"{count} affiliation(s)")

# Database population via SQLite
db = sqlite3.connect("populated.db")
db.close()

vdb.execute("ATTACH DATABASE 'populated.db' AS populated")

vdb.execute("CREATE TABLE populated.works AS SELECT * FROM works")
vdb.execute("CREATE TABLE populated.authors AS SELECT * FROM authors")
vdb.execute("CREATE TABLE populated.affiliations AS SELECT * FROM affiliations")

vdb.execute("DETACH populated")

# Populated database access
db = sqlite3.connect("populated.db")
if full_print:
    for r in db.execute("select * from works order by title"):
        print(r)

# Authors with most publications
for r in db.execute(
    """SELECT count(*), orcid FROM authors
         WHERE orcid is not null GROUP BY orcid ORDER BY count(*) DESC
         LIMIT 10"""
):
    print(r)

# Author affiliations
if full_print:
    for r in db.execute(
        """SELECT authors.given, authors.family, affiliations.name FROM authors
             INNER JOIN affiliations ON authors.id = affiliations.author_id"""
    ):
        print(r)

# Canonicalize affiliations
db.execute(
    """CREATE TABLE affiliation_names AS
  SELECT row_number() OVER (ORDER BY '') AS id, name
  FROM (SELECT DISTINCT name FROM affiliations)"""
)

db.execute(
    """CREATE TABLE author_affiliations AS
  SELECT affiliation_names.id AS affiliation_id, affiliations.author_id
    FROM affiliation_names INNER JOIN affiliations
      ON affiliation_names.name = affiliations.name"""
)

db.execute(
    """CREATE TABLE affiliation_works AS
  SELECT DISTINCT affiliation_id, authors.doi
    FROM author_affiliations
    LEFT JOIN authors ON author_affiliations.author_id = authors.id"""
)

# Orgnizations with most publications
for r in db.execute(
    """SELECT count(*), name FROM affiliation_works
    LEFT JOIN affiliation_names ON affiliation_names.id = affiliation_id
    GROUP BY affiliation_id ORDER BY count(*) DESC
    LIMIT 10"""
):
    print(r)
