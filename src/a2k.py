import abc
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


def len_value(d, k):
    """Return array length or None for the corresponding JSON value for key k
    of dict d"""
    if not d:
        return None
    try:
        v = d[k]
    except KeyError:
        return None
    return len(v)


def first_value(a):
    """Return the first element of array a or None if it doesn't exist"""
    return array_value(a, 0)


class TableMeta:
    """Meta-data of tables we maintain"""

    def __init__(self, name, cursor_class, columns):
        self.name = name
        self.columns = columns
        self.cursor_class = cursor_class

    def column_list(self):
        """Return a comma-separated list of a table's columns"""
        return ",".join([f"'{c.get_name()}'" for c in self.columns])

    def table_schema(self, prefix=""):
        """Return the SQL command to create a table's schema with the
        optional specified prefix."""
        return f"CREATE TABLE {prefix}{self.name}(" + self.column_list() + ")"

    def get_name(self):
        return self.name

    def get_cursor_class(self):
        return self.cursor_class

    def get_value_extractor(self, i):
        """Return the value extraction function for column at ordinal i"""
        return self.columns[i].get_value_extractor()

    def creation_tuple(self, data_files):
        """Return the tuple required by the apsw.Source.Create method"""
        return self.table_schema(), StreamingTable(self, data_files)


class ColumnMeta:
    """Meta-data of table columns we maintain"""

    def __init__(self, name, value_extractor):
        self.name = name
        self.value_extractor = value_extractor

    def get_name(self):
        return self.name

    def get_value_extractor(self):
        """Return the column's value extraction function"""
        return self.value_extractor


# This gets registered with the Connection
class Source:
    def __init__(self):
        self.data_files = None

    def Create(self, db, module_name, db_name, table_name, data_directory):
        if not self.data_files:
            self.data_files = get_data_files(data_directory)

        return table_dict[table_name].creation_tuple(self.data_files)

    Connect = Create


class StreamingTable:
    """An apsw table streaming over data of the supplied table metadata"""

    def __init__(self, table_meta, data_files):
        self.table_meta = table_meta
        self.data_files = data_files

    def BestIndex(self, *args):
        return None

    def Disconnect(self):
        pass

    Destroy = Disconnect

    def Open(self):
        return self.table_meta.get_cursor_class()(self)

    def get_value_extractor(self, i):
        """Return the value extraction function for column at ordinal i.
        Not part of the apsw interface."""
        return self.table_meta.get_value_extractor(i)


class FilesCursor:
    """A cursor over the items data files. Internal use only.
    Not used by a table."""

    def __init__(self, table):
        self.table = table

    def Filter(self, *args):
        """Always called first to initialize an iteration to the first row
        of the table"""
        self.file_index = -1
        self.Next()

    def Next(self):
        """Advance reading to the next available file. Files are assumed to be
        non-empty."""
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
        extract_function = self.table.get_value_extractor(col)
        return extract_function(self.Row())

    def Filter(self, *args):
        """Always called first to initialize an iteration to the first row
        of the table"""
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


class WorkElementsCursor:
    """An (abstract) cursor over a collection in the work items' data."""

    __metaclass__ = abc.ABCMeta

    def __init__(self, table):
        self.table = table
        self.works_cursor = WorksCursor(table)

    @abc.abstractmethod
    def ElementName(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return

    def Filter(self, *args):
        """Always called first to initialize an iteration to the first row
        of the table"""
        self.works_cursor.Filter(*args)
        self.elements = None
        self.Next()

    def Eof(self):
        return self.eof

    @abc.abstractmethod
    def Rowid(self):
        """Return a unique id of the row along all records"""
        return

    def Recordid(self):
        """Return the record's identifier. Not part of the apsw API."""
        # Zero-pad for 60 bits
        return f"{self.Rowid():015X}"

    def Row(self):
        """Return the current row. Not part of the apsw API."""
        return self.elements[self.element_index]

    @abc.abstractmethod
    def Column(self, col):
        return

    def Next(self):
        """Advance reading to the next available element."""
        while True:
            if self.works_cursor.Eof():
                self.eof = True
                return
            if not self.elements:
                self.elements = self.works_cursor.Row().get(self.ElementName())
                self.element_index = -1
            if not self.elements:
                self.works_cursor.Next()
                self.elements = None
                continue
            if self.element_index + 1 < len(self.elements):
                self.element_index += 1
                self.eof = False
                return
            self.works_cursor.Next()
            self.elements = None

    def Column(self, col):
        if col == -1:
            return self.Rowid()

        extract_function = self.table.get_value_extractor(col)
        return extract_function(self.Row())

    def Close(self):
        self.works_cursor.Close()
        self.elements = None


class AuthorsCursor(WorkElementsCursor):
    """A cursor over the items' authors data."""

    def ElementName(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "author"

    def Rowid(self):
        """This allows for 65k authors. There is a Physics paper with 5k
        authors."""
        return (self.works_cursor.Rowid() << 16) | self.element_index

    def Column(self, col):
        if col == 0:  # id
            return self.Recordid()

        if col == 1:  # work_doi
            return self.works_cursor.Row().get("DOI")

        return super().Column(col)


class ReferencesCursor(WorkElementsCursor):
    """A cursor over the items' references data."""

    def ElementName(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "reference"

    def Rowid(self):
        """This allows for 16M references"""
        return (self.works_cursor.Rowid() << 24) | self.element_index

    def Column(self, col):
        if col == 0:  # work_doi
            return self.works_cursor.Row().get("DOI")

        return super().Column(col)


class UpdatesCursor(WorkElementsCursor):
    """A cursor over the items' updates data."""

    def ElementName(self):
        """The work key from which to retrieve the elements. Not part of the
        apsw API."""
        return "update-to"

    def Rowid(self):
        """This allows for 16M updates"""
        return (self.works_cursor.Rowid() << 24) | self.element_index

    def Column(self, col):
        if col == 0:  # work_doi
            return self.works_cursor.Row().get("DOI")

        return super().Column(col)


class AffiliationsCursor:
    """A cursor over the authors' affiliation data."""

    def __init__(self, table):
        self.table = table
        self.authors_cursor = AuthorsCursor(table)

    def Filter(self, *args):
        """Always called first to initialize an iteration to the first row
        of the table"""
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

        extract_function = self.table.get_value_extractor(col)
        return extract_function(self.Row())

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


tables = [
    TableMeta(
        "works",
        WorksCursor,
        [
            ColumnMeta("DOI", lambda row: dict_value(row, "DOI")),
            ColumnMeta(
                "title", lambda row: first_value(dict_value(row, "title"))
            ),
            ColumnMeta(
                "work_year",
                lambda row: array_value(
                    first_value(
                        dict_value(dict_value(row, "published"), "date-parts")
                    ),
                    0,
                ),
            ),
            ColumnMeta(
                "work_month",
                lambda row: array_value(
                    first_value(
                        dict_value(dict_value(row, "published"), "date-parts")
                    ),
                    1,
                ),
            ),
            ColumnMeta(
                "work_day",
                lambda row: array_value(
                    first_value(
                        dict_value(dict_value(row, "published"), "date-parts")
                    ),
                    2,
                ),
            ),
            # Synthetic column, which can be used for population filtering
            ColumnMeta("update_count", lambda row: len_value(row, "update-to")),
        ],
    ),
    TableMeta(
        "work_authors",
        AuthorsCursor,
        [
            ColumnMeta("id", None),
            ColumnMeta("work_doi", None),
            ColumnMeta("orcid", lambda row: author_orcid(row)),
            ColumnMeta("suffix", lambda row: dict_value(row, "suffix")),
            ColumnMeta("given", lambda row: dict_value(row, "given")),
            ColumnMeta("family", lambda row: dict_value(row, "family")),
            ColumnMeta("name", lambda row: dict_value(row, "name")),
            ColumnMeta(
                "authenticated_orcid",
                lambda row: boolean_value(row, "authenticated-orcid"),
            ),
            ColumnMeta("prefix", lambda row: dict_value(row, "prefix")),
            ColumnMeta("sequence", lambda row: dict_value(row, "sequence")),
        ],
    ),
    TableMeta(
        "author_affiliations",
        AffiliationsCursor,
        [
            ColumnMeta("author_id", None),
            ColumnMeta("name", lambda row: dict_value(row, "name")),
        ],
    ),
    TableMeta(
        "work_references",
        ReferencesCursor,
        [
            ColumnMeta("work_doi", None),
            ColumnMeta("issn", lambda row: dict_value(row, "issn")),
            ColumnMeta(
                "standards_body", lambda row: dict_value(row, "standards-body")
            ),
            ColumnMeta("issue", lambda row: dict_value(row, "issue")),
            ColumnMeta("key", lambda row: dict_value(row, "key")),
            ColumnMeta(
                "series_title", lambda row: dict_value(row, "series-title")
            ),
            ColumnMeta("isbn_type", lambda row: dict_value(row, "isbn-type")),
            ColumnMeta(
                "doi_asserted-by",
                lambda row: dict_value(row, "doi-asserted-by"),
            ),
            ColumnMeta("first_page", lambda row: dict_value(row, "first-page")),
            ColumnMeta("isbn", lambda row: dict_value(row, "isbn")),
            ColumnMeta("doi", lambda row: dict_value(row, "DOI")),
            ColumnMeta("component", lambda row: dict_value(row, "component")),
            ColumnMeta(
                "article_title", lambda row: dict_value(row, "article-title")
            ),
            ColumnMeta(
                "volume_title", lambda row: dict_value(row, "volume-title")
            ),
            ColumnMeta("volume", lambda row: dict_value(row, "volume")),
            ColumnMeta("author", lambda row: dict_value(row, "author")),
            ColumnMeta(
                "standard_designator",
                lambda row: dict_value(row, "standard-designator"),
            ),
            ColumnMeta("year", lambda row: dict_value(row, "year")),
            ColumnMeta(
                "unstructured", lambda row: dict_value(row, "unstructured")
            ),
            ColumnMeta("edition", lambda row: dict_value(row, "edition")),
            ColumnMeta(
                "journal_title", lambda row: dict_value(row, "journal-title")
            ),
            ColumnMeta("issn_type", lambda row: dict_value(row, "issn-type")),
        ],
    ),
    TableMeta(
        "work_updates",
        UpdatesCursor,
        [
            ColumnMeta("work_doi", None),
            ColumnMeta("label", lambda row: dict_value(row, "label")),
            ColumnMeta("doi", lambda row: dict_value(row, "DOI")),
            ColumnMeta(
                "timestamp",
                lambda row: dict_value(dict_value(row, "updated"), "timestamp"),
            ),
        ],
    ),
]

table_dict = {t.get_name(): t for t in tables}


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

for t in tables:
    vdb.execute(f"CREATE VIRTUAL TABLE {t.get_name()} USING filesource(sample)")


def sql_value(db, statement):
    """Return the first value of the specified SQL statement executed on db"""
    (res,) = db.execute(statement).fetchone()
    return res


# Streaming interface
if full_print:
    for r in vdb.execute("SELECT * FROM works ORDER BY title"):
        print(r)
    for r in vdb.execute(
        """SELECT work_doi, id, orcid, given, family
        FROM work_authors"""
    ):
        print(r)


def database_counts(db):
    """Print various counts on the passed database"""
    count = sql_value(db, "SELECT count(*) FROM works")
    print(f"{count} publication(s)")

    count = sql_value(db, "SELECT count(*) FROM work_authors")
    print(f"{count} author(s)")

    count = sql_value(
        db,
        """SELECT count(*) from (SELECT DISTINCT orcid FROM work_authors
                        WHERE orcid is not null)""",
    )
    print(f"{count} unique author ORCID(s)")

    count = sql_value(
        db, "SELECT count(*) FROM (SELECT DISTINCT work_doi FROM work_authors)"
    )
    print(f"{count} publication(s) with work_authors")

    count = sql_value(db, "SELECT count(*) FROM author_affiliations")
    print(f"{count} affiliation(s)")

    count = sql_value(db, "SELECT count(*) FROM work_references")
    print(f"{count} references(s)")

    count = sql_value(
        db,
        """SELECT count(*) FROM work_references WHERE
                      doi is not null""",
    )
    print(f"{count} references(s) with DOI")

    count = sql_value(db, "SELECT count(*) FROM work_updates")
    print(f"{count} update(s)")


database_counts(vdb)

# Database population via SQLite
db = sqlite3.connect("populated.db")
db.close()

vdb.execute("ATTACH DATABASE 'populated.db' AS populated")

for t in tables:
    vdb.execute(t.table_schema("populated."))

# Sampling:
#           WHERE abs(random() % 100000) = 0"""
#           WHERE update_count is not null
vdb.execute(
    """INSERT INTO populated.works SELECT * FROM works
    """
)

vdb.execute("CREATE INDEX populated.works_doi_idx ON works(doi)")

vdb.execute(
    """INSERT INTO populated.work_authors
  SELECT work_authors.* FROM work_authors
  INNER JOIN populated.works ON work_authors.work_doi = populated.works.doi"""
)
vdb.execute("CREATE INDEX populated.work_authors_id_idx ON work_authors(id)")
vdb.execute(
    """CREATE INDEX populated.work_authors_work_doi_idx
    ON work_authors(work_doi)"""
)

vdb.execute(
    """INSERT INTO populated.author_affiliations
        SELECT author_affiliations.* FROM author_affiliations
        INNER JOIN populated.work_authors
            ON author_affiliations.author_id = populated.work_authors.id
"""
)
vdb.execute(
    """CREATE INDEX populated.author_affiliations_author_id_idx
    ON author_affiliations(author_id)"""
)

vdb.execute(
    """INSERT INTO populated.work_references
  SELECT work_references.* FROM work_references
  INNER JOIN populated.works
    ON work_references.work_doi = populated.works.doi"""
)
vdb.execute(
    """CREATE INDEX populated.work_references_work_doi_idx
    ON work_references(work_doi)"""
)

vdb.execute(
    """INSERT INTO populated.work_updates
  SELECT work_updates.* FROM work_updates
  INNER JOIN populated.works
    ON work_updates.work_doi = populated.works.doi"""
)
vdb.execute(
    """CREATE INDEX populated.work_updates_work_doi_idx
    ON work_updates(work_doi)"""
)

vdb.execute("DETACH populated")

# Populated database access
db = sqlite3.connect("populated.db")
if full_print:
    for r in db.execute("select * from works order by title"):
        print(r)

# Authors with most publications
for r in db.execute(
    """SELECT count(*), orcid FROM work_authors
         WHERE orcid is not null GROUP BY orcid ORDER BY count(*) DESC
         LIMIT 3"""
):
    print(r)

# Author affiliations
if full_print:
    for r in db.execute(
        """SELECT work_authors.given, work_authors.family,
            author_affiliations.name FROM work_authors
             INNER JOIN author_affiliations
                ON work_authors.id = author_affiliations.author_id"""
    ):
        print(r)

# Canonicalize affiliations
db.execute(
    """CREATE TABLE affiliation_names AS
  SELECT row_number() OVER (ORDER BY '') AS id, name
  FROM (SELECT DISTINCT name FROM author_affiliations)"""
)

db.execute(
    """CREATE TABLE authors_affiliations AS
  SELECT affiliation_names.id AS affiliation_id, author_affiliations.author_id
    FROM affiliation_names INNER JOIN author_affiliations
      ON affiliation_names.name = author_affiliations.name"""
)

db.execute(
    """CREATE TABLE affiliation_works AS
  SELECT DISTINCT affiliation_id, work_authors.work_doi
    FROM authors_affiliations
    LEFT JOIN work_authors ON authors_affiliations.author_id = work_authors.id"""
)

# Organizations with most publications
for r in db.execute(
    """SELECT count(*), name FROM affiliation_works
    LEFT JOIN affiliation_names ON affiliation_names.id = affiliation_id
    GROUP BY affiliation_id ORDER BY count(*) DESC
    LIMIT 3"""
):
    print(r)

# Most cited references
for r in db.execute(
    """SELECT count(*), doi FROM work_references
    GROUP BY doi ORDER BY count(*) DESC
    LIMIT 3"""
):
    print(r)

database_counts(db)
