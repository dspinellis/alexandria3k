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
from multiprocessing import Pool
import time

import apsw

from rapidfuzz.distance import JaroWinkler

from alexandria3k.common import ensure_table_exists, log_sql, set_fast_writing

from alexandria3k.author_name_disambiguation_utils import (
    Author,
    UnionFind,
    jaccard_similarity,
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
        if not affiliation_name:
            continue
        if author_id not in affiliations_map:
            affiliations_map[author_id] = set()
        affiliations_map[author_id].update(get_ngrams(affiliation_name))
    return affiliations_map


def get_publication_years_per_block(block_key, database):
    """
    Queries the database for publication year of a work of an author
    """

    cursor = database.cursor()

    # Key: author_id, Value: publication_year
    publication_year_map: dict[int, int] = {}

    for author_id, published_year in cursor.execute(
        """
    SELECT work_author_id ,published_year  FROM works
    JOIN author_name_blocks ON author_name_blocks.work_id = works.id
    WHERE author_name_blocks.block_key = ? """,
        (block_key,),
    ):
        publication_year_map[author_id] = published_year

    return publication_year_map


def score_year_gap(auth1, auth2, publication_year, max_gap=40):
    """
    Get year gaps where authors made publications
    If there is a big gap between them they are probably not the same person
    """

    year1 = publication_year.get(auth1.id)
    year2 = publication_year.get(auth2.id)

    if year1 is None or year2 is None:
        return None

    gap = abs(year1 - year2)
    return max(0, 1 - gap / max_gap)


def score_affiliations(auth1, auth2, affiliations_map):
    """
    1-3 word n-gram Jaccard similarity of two authors normalized affiliation strings
    auth = set(author_id, author_name, author_work_id )
    """

    author_1_affiliations = affiliations_map.get(auth1.id, set())
    author_2_affiliations = affiliations_map.get(auth2.id, set())

    if not author_1_affiliations and not author_2_affiliations:
        return None

    return jaccard_similarity(author_1_affiliations, author_2_affiliations)


def score_coauthors(auth1, auth2, co_authors_map, weight=1.5):
    """Jaccard similarity of two authors' co-author block-key sets"""

    author_1_coauthors = co_authors_map.get(auth1.id, set())
    author_2_coauthors = co_authors_map.get(auth2.id, set())

    if not author_1_coauthors and not author_2_coauthors:
        return None

    return min(1.0, weight * jaccard_similarity(author_1_coauthors, author_2_coauthors))


def score_name_similarity(auth1, auth2, threshold=0.75):
    """
    Score the name similarity of 2 authors normalised_name
    If the name is the same return 1
    If name1 != name2 find jaroWinkler similarity
    if jarowinkler < threshold return 0
    """

    if auth1.name == auth2.name:
        return 1.0
    name_similarity = JaroWinkler.similarity(auth1.name, auth2.name)

    return 0 if name_similarity < threshold else name_similarity


def check_if_co_authors(auth1, auth2):
    """
    Checks if 2 authors are co_authors by comparing if work_id is the same
    """

    return auth1.work_id == auth2.work_id


def compare_authors(
    auth1, auth2, co_authors_map, affiliations_map, publication_year, threashold=0.75
):

    """This will serve as the scoring function to determine if 2 authors are the same person.
    The scoring function will be calculated based on a couple of criteria:
    - Jaccard similarity on co-author sets of each author (how many co-authors they have in common)
    - Jaro Winkler score , comparing the normalized names
    - Affiliation/venue overlap
    - Year gap
    - Topic overlap using Leiden clustering
    """

    # if they are co authors then they are surely different authors
    if auth1.work_id == auth2.work_id:
        return 0

    name_similarity = score_name_similarity(auth1, auth2)
    jaccard_affiliations = score_affiliations(auth1, auth2, affiliations_map)
    jaccard_coauthors = score_coauthors(auth1, auth2, co_authors_map)
    year_gap = score_year_gap(auth1, auth2, publication_year)

    # calculate confidence score
    scores = [name_similarity, jaccard_affiliations, jaccard_coauthors, year_gap]
    valid_scores = [s for s in scores if s is not None]
    avg = sum(valid_scores) / len(valid_scores)

    return avg if avg >= threashold else 0


def group_by_signature(authors, co_authors, affiliations, publication_year):
    """Groups authors by their (name, co-authors, affiliations, year) signature."""
    groups = {}
    for author in authors:
        signature = (
            author.name,
            frozenset(co_authors.get(author.id, set())),
            frozenset(affiliations.get(author.id, set())),
            publication_year.get(author.id),
        )
        if signature not in groups:
            groups[signature] = []
        groups[signature].append(author)
    return groups


def process_block(block_key, grouped_authors, database_path, database=None):
    """
    Main loop for comparing each author with every other in the block
    Returns a list of each author entry in the database
    entry = tuple(work_author_id, merged_id, confidence_score)
    for comparison details check compare_authors
    """
    if database is None:
        database = apsw.Connection(database_path)

    author_block_list: list[tuple] = []
    # uses custom Author class for explicitness, set(id , name, work_id)
    authors = [Author(row[1], row[2], row[3]) for row in grouped_authors]

    # if block only has one author, skip
    if len(authors) < 2:
        author_id = authors[0].id
        merged_author_id = author_id
        confidence_score = 1.0
        
        merged_authors_entry = (author_id, merged_author_id, confidence_score)
        author_block_list.append(merged_authors_entry)
        return author_block_list

    # computes everything once per-block for lower query counts
    co_authors = get_co_authors(block_key, database)
    affiliations = get_affiliations_per_block(block_key, database)
    publication_year = get_publication_years_per_block(block_key, database)

    # Groups authors by signature, every author sharing a signature is the same person.
    # Comparisons happen between representatives of each group
    groups = group_by_signature(authors, co_authors, affiliations, publication_year)

    # representative is the first person of each group
    representatives = [groups[sign][0] for sign in groups.keys()]

    # Use unionfind dataset for merging
    union_find = UnionFind(len(groups))
    scores = [0.0] * len(groups)

    # score = 1 for authors in the same group
    for i, signature in enumerate(groups.keys()):
        if len(groups[signature]) > 1:
            scores[i] = 1.0

    for i, representative_1 in enumerate(representatives):
        for j, representative_2 in enumerate(representatives):

            if representative_1 == representative_2:
                continue

            if score := compare_authors(
                representative_1,
                representative_2,
                co_authors,
                affiliations,
                publication_year,
            ):
                union_find.union(i, j)
                scores[i] = max(scores[i], score)
                scores[j] = max(scores[j], score)

    for i, signature in enumerate(groups.keys()):
        root = union_find.find(i)
        merged_author_id = representatives[root].id
        confidence_score = scores[i]
        for author in groups[signature]:
            merged_authors_entry = (author.id, merged_author_id, confidence_score)
            author_block_list.append(merged_authors_entry)

    return author_block_list


def process_blocks_parallel(
    block_cursor, query, database_path, database, big_block_threashold
):
    """
    Function is called when create_merged_authors_table "parallelised" flag = True
    Processes blocks in parallel rather than sequencially
    Bigger blocks over a threashold are processed in parallel
    Smaller blocks are processed seriliazed after bigger blocks finish
    Concurrency occurs with processes not threads
    Returns a list of block entries in form of a list of tuples
    """

    start_time = time.perf_counter()
    big_block_args = []
    small_block_args = []
    for block_key, grouped_authors in groupby(
        block_cursor.execute(query), key=lambda row: row[0]
    ):
        grouped_authors = list(grouped_authors)
        if len(grouped_authors) > big_block_threashold:
            big_block_args.append((block_key, grouped_authors, database_path))
        else:
            small_block_args.append((block_key, grouped_authors, database_path))

    args_built_time = time.perf_counter()
    print(f"populated args {args_built_time - start_time:.2f}s")

    with Pool() as pool:
        big_block_args.sort(key=lambda args: len(args[1]), reverse=True)
        results_big = pool.starmap(process_block, big_block_args, chunksize=1)

    big_blocks_done_time = time.perf_counter()
    print(f"big blocks {big_blocks_done_time - args_built_time:.2f}s ")
    results_small = []
    for block_key, grouped_authors, path in small_block_args:
        results_small.append(
            process_block(block_key, grouped_authors, path, database=database)
        )

    small_blocks_done_time = time.perf_counter()
    print(f"small blocks {small_blocks_done_time - big_blocks_done_time:.2f}s ")
    results = results_big + results_small
    return results


def process_blocks_sequential(block_cursor, query, database_path, database):

    """
    Function is called when create_merged_authors_table "parallelised" flag = False
    Processes blocks sequencially rather than in parallel
    Returns a list of block entries in form of a list of tuples
    """
    args = []
    for block_key, grouped_authors in groupby(
        block_cursor.execute(query), key=lambda row: row[0]
    ):
        grouped_authors = list(grouped_authors)
        args.append((block_key, grouped_authors, database_path))

    results = []
    for block_key, grouped_authors, path in args:
        results.append(
            process_block(block_key, grouped_authors, path, database=database)
        )

    return results


def create_merged_authors_table(
    database_path, big_block_threashold=50, parallelised=True
):

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
    database.execute(
        log_sql(
            """
            CREATE INDEX IF NOT EXISTS idx_author_affiliations_author_id
            ON author_affiliations(author_id)
            """
        )
    )
    # perf.log("created works/work_authors indexes")

    block_cursor = database.cursor()
    insert_cursor = database.cursor()

    query = """SELECT block_key , work_author_id , normalized_name, work_id
               FROM author_name_blocks
               ORDER BY block_key
            """
    # perf.log("starting block comparison loop")

    if parallelised:
        results = process_blocks_parallel(
            block_cursor, query, database_path, database, big_block_threashold
        )
    else:
        results = process_blocks_sequential(
            block_cursor, query, database_path, database
        )

    for rows in results:
        for row in rows:
            insert_cursor.execute(
                "INSERT INTO merged_authors VALUES (?, ?, ?)",
                row,
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
