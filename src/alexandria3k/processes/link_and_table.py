"""Cluster authors into disambiguated identities based on shared signals."""

# from math import floor
from itertools import groupby

import apsw

from alexandria3k.common import ensure_table_exists, log_sql, set_fast_writing

# from alexandria3k import perf
from alexandria3k.db_schema import ColumnMeta, TableMeta


table = [
    TableMeta(
        "author_clusters",
        columns=[
            ColumnMeta("work_author_id"),
            ColumnMeta("cluster_id"),
            ColumnMeta("confidence_score"),
        ],
    )
]


def jaccard_similarity(set_a, set_b):
    if set_a and set_b:
        union = set_a | set_b
        jaccard = len(set_a & set_b) / len(union)
    else:
        jaccard = 0

    return jaccard


def get_co_authors(key, database):
    """Gets all the co-authors of a specific work of an author"""

    co_authors_cursor = database.cursor()

    coauthor_map = {}
    for work_author_id, coauthor_block_key in co_authors_cursor.execute(
        """
        SELECT a.work_author_id, b.block_key 
        FROM author_name_blocks a
        JOIN work_authors wa ON wa.work_id = a.work_id
        JOIN author_name_blocks b ON b.work_author_id = wa.id
        WHERE a.block_key = ?
        AND b.work_author_id != a.work_author_id
    """,
        (key,),
    ):

        if work_author_id not in coauthor_map:
            coauthor_map[work_author_id] = set()
        coauthor_map[work_author_id].add(coauthor_block_key)

    return coauthor_map


def compare_authors(auth1, auth2, co_authors_map):

    """This will serve as the scoring function to determine if 2 authors are the same person.
    The scoring function will be calculated based on a couple of criteria:
    - Jaccard similarity on co-author sets of each author (how many co-authors they have in common)
    - Jaro Winkler score , comparing the normalized names
    - Affiliation/venue overlap
    - Year gap
    - Topic overlap using Leiden clustering"""

    id_a = auth1
    id_b = auth2

    co_authors_a = co_authors_map.get(id_a, set())
    co_authors_b = co_authors_map.get(id_b, set())

    jaccard = jaccard_similarity(co_authors_a, co_authors_b)

    if (jaccard) > 0.8:
        return True

    return False


def create_author_clusters(database_path):

    """creates the final table mentioned below"""

    database = apsw.Connection(database_path)
    database.execute(log_sql("DROP TABLE IF EXISTS author_clusters"))
    database.execute(log_sql(table[0].table_schema()))
    set_fast_writing(database)
    ensure_table_exists(database, "author_name_blocks")

    block_cursor = database.cursor()

    query = "SELECT block_key , work_author_id FROM author_name_blocks ORDER BY block_key"
    c = 'a'
    count = 0
    for block_key, grouped_authors in groupby(block_cursor.execute(query), key=lambda row: row[0]):
        if (c != block_key[0]): 
            c = block_key[0]
            print(c , count)
            count = 0
        authors = [row[1] for row in grouped_authors]
        if len(authors) < 2:
            continue
        co_authors = get_co_authors(block_key , database)

        for i in range(len(authors)):
            for j in range(i+1 , len(authors)):
                if compare_authors(authors[i] , authors[j] , co_authors):
                    count += 1
       
       
        
        


def process(database_path):
    """Process creates the clusters table for the author name disambiguation pipeline.
    Input will be the author_names_block table created in
    /alexandria3k/src/alexandria3k/processes/link_author_blocks.py for less comparisons.
    For every entry in a block , compares every pair of authors and decides if they are the same person
    To calculate that , each pair will go through a scoring function,
    which they will be compared by some criteria (for more details on the criteria check the compare_authors comment)
    Process will return a table that contains work_author_id , cluster_id , confidence_score
    where cluster_id is the id of the merged author"""

    create_author_clusters(database_path)
