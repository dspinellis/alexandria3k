"""
Process creates and links author_name_blocks table
(work_author_id, normalized_name, normalized_family_name, work_id, block_key)

Takes input work_authors table which gets populated with Crossref metadata

Process is the first phase of the author_name_disambiguation layer in alexandria3k
- Gets every author in the populated table
- Normalizes name with custom function normalize()
- Groups them on "blocks" based on that normalization function
  (current grouping logic is normalized_last_name + normalized first name initial)

Output is the filled author_name_blocks table
"""

import apsw

from alexandria3k.common import ensure_table_exists, log_sql, set_fast_writing

from alexandria3k.author_name_disambiguation_utils import normalized

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


def create_author_blocks_table(database_path):
    """Creates the author_blocks_table from the populated dataset.
    Procedure is mentioned in the comment of the process below"""

    database = apsw.Connection(database_path)
    database.execute(log_sql("DROP TABLE IF EXISTS author_name_blocks"))
    database.execute(log_sql(table[0].table_schema()))
    set_fast_writing(database)
    ensure_table_exists(database, "work_authors")
    # perf.log("author_blocks table created")

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

        if not normalized_name  and not normalized_family:
            continue
        elif not normalized_name and normalized_family:
            block_key = normalized_family + "_" + normalized_family[0]
        elif normalized_name and not normalized_family:
            block_key = normalized_name + "_" + normalized_name[0]
        else: 
            block_key = normalized_family + "_" + normalized_name[0]  # last name + initial

        insert_cursor.execute(
            "INSERT INTO author_name_blocks VALUES (?, ?, ?, ?, ?) ",
            (author_id, normalized_name, normalized_family, work_id, block_key),
            prepare_flags=apsw.SQLITE_PREPARE_PERSISTENT,
        )
    select_cursor.close()
    insert_cursor.close()
    # perf.log("filled author_blocks table")
    database.execute(
        log_sql(
            "CREATE INDEX IF NOT EXISTS idx_block_key ON author_name_blocks(block_key)"
        )
    )
    database.execute(
        log_sql(
            "CREATE INDEX IF NOT EXISTS idx_work_author_id ON author_name_blocks(work_author_id)"
        )
    )
    database.execute(
        log_sql("CREATE INDEX IF NOT EXISTS idx_work_id ON author_name_blocks(work_id)")
    )
    # perf.log("created author_blocks indexes")


def process(database_path):
    """
    Process creates and links the author_blocks_table with the populated dataset
    Table consists of (work_author_id, normalised_name, normalised_family_name, work_id, block_key)
    For each author in the database, his name will be passed through a name-normalization function,
    based on that output each author will be put into a block with that id,
    reducing comparisons to just each authors in the same block to distinguish.
    block_key is consisted of the normalised_family_name + first inital of normalised name"""

    create_author_blocks_table(database_path)
    print("Created author_blocks table")
