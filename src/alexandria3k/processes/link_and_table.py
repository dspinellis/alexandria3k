"""Cluster authors into disambiguated identities based on shared signals."""

from math import floor
from itertools import groupby

import apsw

# import jellyfish

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


"""Algorithm taken from GeeksforGeeks"""


def jaro_distance(s1, s2):

    # If the s are equal
    if s1 == s2:
        return 1.0

    # Length of two s
    len1 = len(s1)
    len2 = len(s2)

    # Maximum distance upto which matching
    # is allowed
    max_dist = floor(max(len1, len2) / 2) - 1

    # Count of matches
    match = 0

    # Hash for matches
    hash_s1 = [0] * len(s1)
    hash_s2 = [0] * len(s2)

    # Traverse through the first
    for i in range(len1):

        # Check if there is any matches
        for j in range(max(0, i - max_dist), min(len2, i + max_dist + 1)):

            # If there is a match
            if s1[i] == s2[j] and hash_s2[j] == 0:
                hash_s1[i] = 1
                hash_s2[j] = 1
                match += 1
                break

    # If there is no match
    if match == 0:
        return 0.0

    # Number of transpositions
    t = 0
    point = 0

    # Count number of occurrences
    # where two characters match but
    # there is a third matched character
    # in between the indices
    for i in range(len1):
        if hash_s1[i]:

            # Find the next matched character
            # in second
            while hash_s2[point] == 0:
                point += 1

            if s1[i] != s2[point]:
                t += 1
            point += 1
    t = t // 2

    # Return the Jaro Similarity
    return (match / len1 + match / len2 + (match - t) / match) / 3.0


def jaro_Winkler(s1, s2):

    jaro_dist = jaro_distance(s1, s2)

    # If the jaro Similarity is above a threshold
    if jaro_dist > 0.7:

        # Find the length of common prefix
        prefix = 0

        for i in range(min(len(s1), len(s2))):

            # If the characters match
            if s1[i] == s2[i]:
                prefix += 1

            # Else break
            else:
                break

        # Maximum of 4 characters are allowed in prefix
        prefix = min(4, prefix)

        # Calculate jaro winkler Similarity
        jaro_dist += 0.1 * prefix * (1 - jaro_dist)

    return jaro_dist


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

    id_a, name_a = auth1
    id_b, name_b = auth2

    jaro_w = jaro_Winkler(name_a, name_b)
    # jaro_w = jellyfish.jaro_winkler_similarity(name_a , name_b)  //if we choose to add the dependency , with sample it saves one second

    co_authors_a = co_authors_map.get(id_a, set())
    co_authors_b = co_authors_map.get(id_b, set())

    jaccard = jaccard_similarity(co_authors_a, co_authors_b)

    if (jaccard + jaro_w) / 2 > 0.7:
        return True

    return False


def create_author_clusters(database_path):

    """creates the final table mentioned below"""

    database = apsw.Connection(database_path)
    database.execute(log_sql("DROP TABLE IF EXISTS author_clusters"))
    database.execute(log_sql(table[0].table_schema()))
    set_fast_writing(database)
    ensure_table_exists(database, "author_name_blocks")
    # perf.log("author_clusters table created")

    block_cursor = database.cursor()

    query = "SELECT block_key , work_author_id , normalized_name FROM author_name_blocks ORDER BY block_key"
    c = "a"
    count = 0
    total = 0
    for block_key, grouped_authors in groupby(
        block_cursor.execute(query), key=lambda row: row[0]
    ):

        if c != block_key[0]:
            c = block_key[0]
            print(c, count)
            total += count
            count = 0
            # perf.log(f"finished letter {c}")

        authors = [(row[1], row[2]) for row in grouped_authors]
        if len(authors) < 2:
            continue
        co_authors = get_co_authors(block_key, database)
        for i in range(len(authors)):
            for j in range(i + 1, len(authors)):
                if compare_authors(authors[i], authors[j], co_authors):
                    count += 1
    print(total)
    # perf.log("finished comparing all blocks")


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
