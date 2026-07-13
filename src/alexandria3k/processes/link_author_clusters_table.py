"""
Cluster authors into disambiguated identities based on shared signals.
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

from alexandria3k.author_name_disambiguation_utils import UnionFind , jaccard_similarity , normalized

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

    coauthor_map = {}
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

def get_author_affiliation(auth_id , database):
    """
    Get list of author affiliations from the populated database 
    (author_affiliations table)
    affiliation names get normalized for better matches
    normalization occurs with custom function normalized() in author_names_disambiguation_utils
    TO DO: create the affiliation disambiguation layer and use that instead
    """


    affiliations_cursor = database.cursor()

    affiliations = set()
    for (affilitiation_name,) in affiliations_cursor.execute("""
    SELECT name FROM author_affiliations WHERE author_id = ? """, (auth_id,)):
        affiliations.add(normalized(affilitiation_name))
    return affiliations
        

def get_publication_year(auth_id , database):
    """
    Queries the database for publication year of a work of an author
    """

    cursor = database.cursor()
    year = cursor.execute("""
    SELECT published_year FROM works
    JOIN work_authors ON work_authors.work_id = works.id
    WHERE work_authors.id = ? """, (auth_id,)).fetchone()
    return year[0] if year else None

def compare_year_gaps(auth1_id, auth2_id, database , max_gap=40):
    """
    Get year gaps where authors made publications
    If there is a big gap between them they are probably not the same person
    """

    year1 = get_publication_year(auth1_id , database)
    year2 = get_publication_year(auth2_id , database)

    if year1 is None or year2 is None:   
        return 0

    gap = abs(year1 - year2)
    return max(0 , 1 - gap/max_gap)

def compare_authors(auth1, auth2, co_authors_map, database):

    """This will serve as the scoring function to determine if 2 authors are the same person.
    The scoring function will be calculated based on a couple of criteria:
    - Jaccard similarity on co-author sets of each author (how many co-authors they have in common)
    - Jaro Winkler score , comparing the normalized names
    - Affiliation/venue overlap
    - Year gap
    - Topic overlap using Leiden clustering
    """

    author_1_id, author_1_name = auth1
    author_2_id, author_2_name = auth2

    #Jaro winkler for name similarity
    jaro_winkler_names = JaroWinkler.similarity(author_1_name, author_2_name)
    
    if jaro_winkler_names < 0.6: 
        return 0

    #jaccard for affiliation similarity
    author_1_affiliations = get_author_affiliation(author_1_id , database) 
    author_2_affiliations = get_author_affiliation(author_2_id , database) 

    jaccard_affiliations = jaccard_similarity(author_1_affiliations, author_2_affiliations)


    #jaccard for co_author similarity
    author_a_coauthors = co_authors_map.get(author_1_id, set())
    author_b_coauthors = co_authors_map.get(author_2_id, set())

    jaccard_coauthors = jaccard_similarity(author_a_coauthors, author_b_coauthors)


    #check year_gap of publication, if really big probably not the same person

    year_gap = compare_year_gaps(author_1_id , author_2_id , database)


    #calculate confidence score
    score = (jaccard_coauthors + jaro_winkler_names + year_gap + jaccard_affiliations) / 4
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
    # perf.log("merged_authors table created")

    database.execute(
        log_sql(
            "CREATE INDEX IF NOT EXISTS idx_works_id ON works(id)"
        )
    )
    database.execute(
        log_sql(
            "CREATE INDEX IF NOT EXISTS idx_work_authors_id ON work_authors(id)"
        )
    )


    block_cursor = database.cursor()
    insert_cursor = database.cursor()

    query = "SELECT block_key , work_author_id , normalized_name FROM author_name_blocks ORDER BY block_key"

    for block_key, grouped_authors in groupby(block_cursor.execute(query), key=lambda row: row[0]):

        #sets of author name and id
        authors = [(row[1], row[2]) for row in grouped_authors]
        scores  = [0.0] * len(authors)  
        co_authors = get_co_authors(block_key, database)

        #if block only has one author, skip
        if len(authors) < 2:
            insert_cursor.execute(
                "INSERT INTO merged_authors VALUES (?, ?, ?)",
                (authors[0][0], authors[0][0], 1.0), #is the same author for sure
                prepare_flags=apsw.SQLITE_PREPARE_PERSISTENT,
            )
            continue

        uf = UnionFind(len(authors))
        for i in range(len(authors)):
            for j in range(i + 1, len(authors)):
                if s := compare_authors(authors[i], authors[j], co_authors , database):
                    uf.union(i , j)
                    scores[i] = max(scores[i] , s)
                    scores[j] = max(scores[j] , s)

        for i, (author_id, _) in enumerate(authors):
            root = uf.find(i)
            cluster_id = authors[root][0]  # translate the root index back to a real work_author_id
            insert_cursor.execute(
                "INSERT INTO merged_authors VALUES (?, ?, ?)",
                (author_id, cluster_id, scores[i]),
                prepare_flags=apsw.SQLITE_PREPARE_PERSISTENT,
            )

    # perf.log("finished comparing all blocks")


def process(database_path):
    """Process creates the clusters table for the author name disambiguation pipeline.
    Input will be the author_names_block table created in
    /alexandria3k/src/alexandria3k/processes/link_author_blocks.py for less comparisons.
    For every entry in a block , compares every pair of authors and decides if they are the same person
    To calculate that , each pair will go through a scoring function,
    which they will be compared by some criteria mentioned in compare_authors
    Process will return a table that contains work_author_id , cluster_id , confidence_score
    where cluster_id is the id of the merged author"""

    create_merged_authors_table(database_path)
