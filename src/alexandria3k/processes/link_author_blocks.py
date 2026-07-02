"""Create author_name_blocks table based on normalised author names"""

import unicodedata

import apsw

from alexandria3k.common import ensure_table_exists, log_sql, set_fast_writing

# from alexandria3k import perf
from alexandria3k.db_schema import ColumnMeta, TableMeta


table = [
    TableMeta(
        "author_name_blocks",
        columns=[
            ColumnMeta("work_author_id"),
            ColumnMeta("normalized_name"),
            ColumnMeta("normalized_family_name"),
            ColumnMeta("work_id"),
            ColumnMeta("block_key"),
        ],
    ),
]


def normalized(s: str):
    tmp = "".join(
        c for c in unicodedata.normalize("NFKD", s) 
        if unicodedata.category(c) != "Mn" and (c.isalpha() or c.isspace())
    )
    return tmp.lower().strip()


def create_author_blocks_table(database_path):
    """Create the blocks table from the populated dataset.
    Procedure is mentioned in the comment of the process below"""

    # TODO: LOG ALL COMMANDS , LINK UNIT TESTS

    database = apsw.Connection(database_path)
    database.execute(log_sql("DROP TABLE IF EXISTS author_name_blocks"))
    database.execute(log_sql(table[0].table_schema()))
    set_fast_writing(database)
    ensure_table_exists(database, "work_authors")

    select_cursor = database.cursor()
    insert_cursor = database.cursor()
    # perf.log("author_blocks SELECT")
    for author_id, given, family_name, work_id in select_cursor.execute(
        """
        SELECT id , given , family , work_id FROM work_authors"""
    ):

        if not given or not family_name:
            continue

        normalized_name = normalized(given)
        normalized_family = normalized(family_name)
        block_key = normalized_family + "_" + normalized_name[0]  # last name + initial

        insert_cursor.execute(
            "INSERT INTO author_name_blocks VALUES (?, ?, ?, ?, ?) ",
            (author_id, normalized_name, normalized_family, work_id, block_key),
            prepare_flags=apsw.SQLITE_PREPARE_PERSISTENT,
        )
    select_cursor.close()
    insert_cursor.close()
    database.execute(log_sql(
        "CREATE INDEX IF NOT EXISTS idx_block_key ON author_name_blocks(block_key)"
    ))
    database.execute(log_sql(
        "CREATE INDEX IF NOT EXISTS idx_work_author_id ON author_name_blocks(work_author_id)"
    ))
    # perf.log("filled author_blocks table")


def process(database_path):
    """This process will create the name_block tables for every author in the database
    For each author in the database, his named will be passed through a name-normalisation function,
    based on that output each author will be put into a block with that id so that we need less comparisons
    to disambiguate authors.
    Table consists of work_author_id normalised_name normalised_family_name work_id block_key
    block_key is consisted of the normalised_family_name + first inital of normalised name"""

    create_author_blocks_table(database_path)
    print("Created author_blocks table")
