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

import time
from itertools import combinations , groupby

import apsw
import igraph as ig
import leidenalg

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
            ColumnMeta("community_id")
        ],
    ),
]

DEFAULT_RESOLUTION = 1.0

def build_graph(database):
    """Build an igraph graph from the coupling work refrences."""

    graph_cursor = database.cursor()

    journals = [row[0] for row in database.execute(
    "SELECT DISTINCT container_title FROM works WHERE container_title IS NOT NULL"
    )]

    query = """
        SELECT work_references.doi, works.container_title
        FROM work_references
        JOIN works ON works.id = work_references.work_id
        WHERE works.container_title IS NOT NULL
        AND work_references.doi IS NOT NULL
        ORDER BY work_references.doi
    """

    edges = []
    for _ , journal_doi_groups in groupby(graph_cursor.execute(query), key=lambda row: row[0]):
        journal_list = {group[1] for group in journal_doi_groups}
        edges.extend(combinations(journal_list, 2))

    g = ig.Graph()
    g.add_vertices(journals)
    g.add_edges(edges)

    return g


def run_leiden_clustering(g, resolution=DEFAULT_RESOLUTION):
    """Run Leiden clustering and return the partition."""
    leiden_start = time.perf_counter()
    partition = leidenalg.find_partition(
        g,
        leidenalg.RBConfigurationVertexPartition,
        resolution_parameter=resolution,
        n_iterations=-1,
        seed=42,
    )
    leiden_end = time.perf_counter()
    n_communities = len(partition)
    print(f"Found {n_communities} communities in {leiden_end - leiden_start:.2f}s.")

    community_map = dict(zip(g.vs["name"], partition.membership))
    return community_map

def get_journal_communities(database):
    """
    Gets author communities based on bibliographic coupling
    Builds igraph, vertices = journals, edges = journals citing the same doi
    If 2 works from different journals cite the same doi then they are connected
    Runs leiden clustering algorithm to get the communities
    Returns a dictionary of key = journal , value = community_id
    """
    g = build_graph(database)
    community_map = run_leiden_clustering(g)
    return community_map

def normalized_block(given, family_name):
    """
    Normalizes given and family name and creates authors block key
    If given is missing, block_key = family + initial_family
    If family is missing, block_key = given + initial_given 
    Returns a set of (normalized given, normalized_family, block_key) 
    """
    normalized_name = normalized(given)
    normalized_family = normalized(family_name)

    if not normalized_name and not normalized_family:
        return None

    if not normalized_name and normalized_family:
        block_key = normalized_family + "_" + normalized_family[0]
    elif normalized_name and not normalized_family:
        block_key = normalized_name + "_" + normalized_name[0]
    else:
        block_key = (
            normalized_family + "_" + normalized_name[0]
        )  # last name + initial

    return (normalized_name, normalized_family, block_key)


def create_author_blocks_table(database_path):
    """Creates the author_blocks_table from the populated dataset.
    Procedure is mentioned in the comment of the process below"""

    database = apsw.Connection(database_path)
    database.execute(log_sql("DROP TABLE IF EXISTS author_name_blocks"))
    database.execute(log_sql(table[0].table_schema()))
    set_fast_writing(database)
    ensure_table_exists(database, "work_authors")
    ensure_table_exists(database, "work_references")
    ensure_table_exists(database, "works")
    # perf.log("author_blocks table created")

    select_cursor = database.cursor()
    insert_cursor = database.cursor()
    # perf.log("author_blocks SELECT")

    community_map = get_journal_communities(database)
    for author_id, given, family_name, work_id, journal in select_cursor.execute(
        """
        SELECT work_authors.id,
               work_authors.given, 
               work_authors.family, 
               work_authors.work_id, 
               works.container_title  
        FROM work_authors
        LEFT JOIN works ON works.id = work_authors.work_id
        """
    ):
        if not given or not family_name:
            continue

        names = normalized_block(given, family_name)
        if not names:
            continue
        normalized_name, normalized_family, block_key = names
        community_id = community_map.get(journal)

        insert_cursor.execute(
            "INSERT INTO author_name_blocks VALUES (?, ?, ?, ?, ?, ?) ",
            (author_id, normalized_name, normalized_family, work_id, block_key, community_id),
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
