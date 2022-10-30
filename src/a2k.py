import apsw
import gzip
import json
import os
import sqlite3


def get_data_files(directory):
    columns = None
    data = []
    counter = 1
    for f in os.listdir(directory):
        path = os.path.join(directory, f)
        if not os.path.isfile(path):
            continue
        counter += 1
        data.append(path)
    return data


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


def first_value(a):
    """Return the first element of array a or None if it doesn't exist"""
    return array_value(a, 0)


columns = [
    ("DOI", lambda row: dict_value(row, "DOI")),
    ("title", lambda row: first_value(dict_value(row, "title"))),
    (
        "publication_year",
        lambda row: array_value(
            first_value(dict_value(dict_value(row, "published"), "date-parts")),
            0,
        ),
    ),
    (
        "publication_month",
        lambda row: array_value(
            first_value(dict_value(dict_value(row, "published"), "date-parts")),
            1,
        ),
    ),
    (
        "publication_day",
        lambda row: array_value(
            first_value(dict_value(dict_value(row, "published"), "date-parts")),
            2,
        ),
    ),
]

# This gets registered with the Connection
class Source:
    def Create(self, db, modulename, dbname, tablename, *args):
        data = get_data_files(args[0])
        schema = (
            "CREATE TABLE items("
            + ",".join([f"'{name}'" for (name, f) in columns])
            + ")"
        )
        return schema, Table(columns, data)

    Connect = Create


# Represents a table
class Table:
    def __init__(self, columns, data):
        self.columns = columns
        self.data = data

    def BestIndex(self, *args):
        return None

    def Open(self):
        return Cursor(self)

    def Disconnect(self):
        pass

    Destroy = Disconnect


# Represents a cursor
class Cursor:
    def file_advance(self):
        """Advance reading to the next available file"""
        if self.file_pos >= len(self.table.data):
            return
        with gzip.open(self.table.data[self.file_pos], "rb") as f:
            file_content = f.read()
            self.items = json.loads(file_content)["items"]
        self.file_pos += 1
        self.record_pos = 0

    def __init__(self, table):
        self.table = table

    def Filter(self, *args):
        self.file_pos = 0
        self.file_advance()

    def Eof(self):
        while True:
            if self.record_pos < len(self.items):
                return False
            if self.file_pos >= len(self.table.data):
                return True
            self.file_advance()

    def Rowid(self):
        return (self.file_pos << 32) | (self.record_pos)

    def Column(self, col):
        if col == -1:
            return self.Rowid()
        row = self.items[self.record_pos]
        (_, extract_function) = self.table.columns[col]
        return extract_function(row)

    def Next(self):
        self.record_pos += 1
        if self.record_pos >= len(self.items):
            self.file_advance()

    def Close(self):
        pass


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

vdb.execute("CREATE VIRTUAL TABLE sample_items USING filesource(sample)")

# Streaming interface
for r in vdb.execute("select * from sample_items order by title"):
    print(r)
(count,) = vdb.execute(
    "select count(*) from sample_items order by title"
).fetchone()
print(f"{count} row(s)")

# Database population via SQLite
db = sqlite3.connect("populated.db")
db.close()

vdb.execute("ATTACH DATABASE 'populated.db' AS populated")
vdb.execute("CREATE TABLE populated.items(doi, title)")
vdb.execute(
    """INSERT INTO populated.items(doi, title)
   SELECT doi, title
   FROM sample_items"""
)
vdb.execute("DETACH populated")

# Populated database access
db = sqlite3.connect("populated.db")
for r in db.execute("select * from items order by title"):
    print(r)
