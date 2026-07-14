"""
Merges authors into disambiguated identities based on shared signals.
Process takes in populated work_author and author_name_blocks table
Returns and links merged_authors table (work_author_id , merged_author_id , confidence_score)

Confidence score is calculated by comparing all authors in the same block with eachother,
Algorithms used to calculate the the confidence score are:
- Jaccard similarity on co-author sets of each author (how many co-authors they have in common)
- Jaro Winkler score , comparing the normalized names

Merging authors together is implemented with a UnionFind datastructure in memory and afterwards
fills the merged_authors table
"""

from itertools import groupby

import apsw

from rapidfuzz.distance import JaroWinkler

from alexandria3k.common import ensure_table_exists, log_sql, set_fast_writing

from alexandria3k.author_name_disambiguation_utils import (
    UnionFind,
    jaccard_similarity,
    normalized,
    get_ngrams,
)

# from alexandria3k import perf
from alexandria3k.db_schema import ColumnMeta, TableMeta


table = [
    TableMeta(
        "merged_authors",
        columns=[
            ColumnMeta("work_author_id"),
            ColumnMeta("merged_author_id"),
            ColumnMeta("confidence_score"),
        ],
    )
]


def get_co_authors(key, database):
    """
    Gets all the co-authors of a specific work of an author and stores in a set
    Takes everything from the author_names_blocks table
    """

    co_authors_cursor = database.cursor()

    # Key: work_author_id , Value: set of block_keys corresponding to their co_authors
    coauthor_map: dict[int, set[str]] = {}
    for work_author_id, coauthor_block_key in co_authors_cursor.execute(
        """
        SELECT a.work_author_id, b.block_key
        FROM author_name_blocks a
        JOIN author_name_blocks b ON b.work_id = a.work_id
        WHERE a.block_key = ?
        AND b.work_author_id != a.work_author_id
    """,
        (key,),
    ):
        if work_author_id not in coauthor_map:
            coauthor_map[work_author_id] = set()
        coauthor_map[work_author_id].add(coauthor_block_key)

    return coauthor_map


def get_affiliations_per_block(block_key, database):
    """
    Returns a map consisting of all the affiliations of an author_id in a Block,
    affiliations could be more than one so set is needed,
    returns the n-gram of each affiliations for better comparisons
    get_ngrams implemented in author_name_disambiguation_utils.py
    params:
        block_key, the block key that we are taking authors from
        database,  apsw connection of the populated database

    """
    affiliations_cursor = database.cursor()

    # Key: author_id , Value: set of affiliations
    affiliations_map: dict[int, set[str]] = {}

    for author_id, affiliation_name in affiliations_cursor.execute(
        """SELECT author_id, name FROM author_affiliations 
        JOIN author_name_blocks ON  author_id = author_name_blocks.work_author_id
        WHERE author_name_blocks.block_key = ? """,
        (block_key,),
    ):
        if author_id not in affiliations_map:
            affiliations_map[author_id] = set()
        affiliations_map[author_id].update(get_ngrams(normalized(affiliation_name)))
    return affiliations_map


def get_publication_year(auth_id, database):
    """
    Queries the database for publication year of a work of an author
    """

    cursor = database.cursor()
    year = cursor.execute(
        """
    SELECT published_year FROM works
    JOIN work_authors ON work_authors.work_id = works.id
    WHERE work_authors.id = ? """,
        (auth_id,),
    ).fetchone()
    return year[0] if year else None


def score_year_gap(auth1_id, auth2_id, database, max_gap=40):
    """
    Get year gaps where authors made publications
    If there is a big gap between them they are probably not the same person
    """

    year1 = get_publication_year(auth1_id, database)
    year2 = get_publication_year(auth2_id, database)

    if year1 is None or year2 is None:
        return 0

    gap = abs(year1 - year2)
    return max(0, 1 - gap / max_gap)


def score_affiliations(auth1_id, auth2_id, affiliations_map):
    """Jaccard similarity of two authors' normalized affiliation strings"""
    author_1_affiliations = affiliations_map.get(auth1_id, set())
    author_2_affiliations = affiliations_map.get(auth2_id, set())
    return jaccard_similarity(author_1_affiliations, author_2_affiliations)


def score_coauthors(auth1_id, auth2_id, co_authors_map):
    """Jaccard similarity of two authors' co-author block-key sets"""
    author_1_coauthors = co_authors_map.get(auth1_id, set())
    author_2_coauthors = co_authors_map.get(auth2_id, set())
    return jaccard_similarity(author_1_coauthors, author_2_coauthors)


def compare_authors(auth1, auth2, co_authors_map, affiliations_map, database):

    """This will serve as the scoring function to determine if 2 authors are the same person.
    The scoring function will be calculated based on a couple of criteria:
    - Jaccard similarity on co-author sets of each author (how many co-authors they have in common)
    - Jaro Winkler score , comparing the normalized names
    - Affiliation/venue overlap
    - Year gap
    - Topic overlap using Leiden clustering
    """

    author_1_id, author_1_name, author_1_work_id = auth1
    author_2_id, author_2_name, author_2_work_id = auth2

    # if they are co authors then they are surely different authors
    if author_1_work_id == author_2_work_id:
        return 0

    # Jaro winkler for name similarity
    jaro_winkler_names = JaroWinkler.similarity(author_1_name, author_2_name)

    # early cutoff if there is big difference in their names
    if jaro_winkler_names < 0.75:
        return 0

    jaccard_affiliations = score_affiliations(author_1_id, author_2_id, affiliations_map)
    jaccard_coauthors = score_coauthors(author_1_id, author_2_id, co_authors_map)
    year_gap = score_year_gap(author_1_id, author_2_id, database)

    # calculate confidence score
    score = (
        jaccard_coauthors + jaro_winkler_names + year_gap + jaccard_affiliations
    ) / 4
    if score > 0.75:
        return score

    return 0


def create_merged_authors_table(database_path):

    """Creates and links merged_authors table.
    Takes as input the database path and checks if author_name_blocks table exists
    """

    database = apsw.Connection(database_path)
    database.execute(log_sql("DROP TABLE IF EXISTS merged_authors"))
    database.execute(log_sql(table[0].table_schema()))
    set_fast_writing(database)

    ensure_table_exists(database, "author_name_blocks")
    ensure_table_exists(database, "author_affiliations")
    ensure_table_exists(database, "work_authors")
    ensure_table_exists(database, "works")
    # perf.log("merged_authors table created")

    database.execute(log_sql("CREATE INDEX IF NOT EXISTS idx_works_id ON works(id)"))
    database.execute(
        log_sql("CREATE INDEX IF NOT EXISTS idx_work_authors_id ON work_authors(id)")
    )
    # perf.log("created works/work_authors indexes")

    block_cursor = database.cursor()
    insert_cursor = database.cursor()

    query = """SELECT block_key , work_author_id , normalized_name, work_id
               FROM author_name_blocks 
               ORDER BY block_key
            """
    # perf.log("starting block comparison loop")

    for block_key, grouped_authors in groupby(
        block_cursor.execute(query), key=lambda row: row[0]
    ):

        # sets of (work_author_id, normalized_name, work_id) 
        authors = [(row[1], row[2], row[3]) for row in grouped_authors]
        scores = [0.0] * len(authors)
        co_authors = get_co_authors(block_key, database)
        affiliations = get_affiliations_per_block(block_key, database)

        # if block only has one author, skip
        if len(authors) < 2:
            insert_cursor.execute(
                "INSERT INTO merged_authors VALUES (?, ?, ?)",
                # authors[0][0] = first authors work_author_id
                (authors[0][0], authors[0][0], 1.0),  
                prepare_flags=apsw.SQLITE_PREPARE_PERSISTENT,
            )
            continue

        union_find = UnionFind(len(authors))
        for i in range(len(authors)):
            for j in range(i + 1, len(authors)):
                if score := compare_authors(
                    authors[i], authors[j], co_authors, affiliations, database
                ):
                    union_find.union(i, j)
                    scores[i] = max(scores[i], score)
                    scores[j] = max(scores[j], score)

        for i, (author_id, _, _) in enumerate(authors):
            root = union_find.find(i)
            #return merged author work_author_id
            merged_author_id  = authors[root][0]  
            insert_cursor.execute(
                "INSERT INTO merged_authors VALUES (?, ?, ?)",
                (author_id, merged_author_id, scores[i]),
                prepare_flags=apsw.SQLITE_PREPARE_PERSISTENT,
            )

    # perf.log("finished comparing all blocks")


def process(database_path):
    """Process creates the clusters table for the author name disambiguation pipeline.
    Input will be the author_names_block table created in
    /alexandria3k/src/alexandria3k/processes/link_author_blocks.py for less comparisons.
    For every entry in a block , compares every pair of authors through a scoring function
    which they will be compared by some criteria mentioned in compare_authors
    Process will return a table that contains work_author_id , cluster_id , confidence_score
    where cluster_id is the id of the merged author"""

    create_merged_authors_table(database_path)
