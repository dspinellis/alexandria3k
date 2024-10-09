#!/usr/bin/env python
#
# Calculate the CD5 index based on Crossref works published 1945-2023
# from a previously populated database
#

import datetime
import random
import sqlite3
import sys

from alexandria3k import perf, debug

use_fast_cdindex = True

if use_fast_cdindex:
    from fast_cdindex import cdindex, timestamp_from_datetime
else:
    from cdindex import cdindex, timestamp_from_datetime

# Five years, for calculating the CD_5 index
DELTA = int(datetime.timedelta(days=365 * 5).total_seconds())

BATCH_SIZE = 10000

# Set to true to create a random population (works only with fast_cdindex)
random_population = False
RANDOM_POPULATION_SIZE = 1000000
random.seed("xyzzy")

RANGE = "published_year BETWEEN 1945 and 2023"

debug.set_flags(["perf"])
debug.set_output(sys.stderr)

def create_indexes(db):
    db.execute("CREATE INDEX IF NOT EXISTS works_id_idx ON works(id)")
    perf.log("CREATE INDEX works_id_idx")

    db.execute("""CREATE INDEX IF NOT EXISTS work_references_work_id_idx
      ON work_references(work_id)""")
    perf.log("CREATE INDEX work_references_work_id_idx")


def progress_output(phase, counter):
    """Report the progress of the specified phase and count"""
    timestamp = datetime.datetime.now().isoformat()
    print(f"{timestamp} {phase} {counter}", file=sys.stderr, flush=True)


def add_random_vertices(graph):
    """Add random vertices for testing"""
    for i in range(1, RANDOM_POPULATION_SIZE):
        dt = datetime.datetime(random.randint(1945, 2021), 1, 1)
        graph.add_vertex(i, timestamp_from_datetime(dt))
    return


def add_vertices(db, graph):
    """Add works as vertices"""
    counter = 0
    for (doi, year, month, day) in db.execute(
        f"""
            SELECT DISTINCT doi, published_year,
              Coalesce(published_month, 1),
              Coalesce(published_day, 1)
            FROM works WHERE {RANGE}"""
    ):
        dt = datetime.datetime(year, month, day)
        graph.add_vertex(doi, timestamp_from_datetime(dt))
        if counter % 1000000 == 0:
            progress_output("N", counter);
        counter += 1
    perf.log("Create vertices")


def add_random_edges(graph):
    """Add random edges for testing"""
    for i in range(1, RANDOM_POPULATION_SIZE * 20):
        graph.add_edge(random.randint(1, RANDOM_POPULATION_SIZE - 1), random.randint(1, RANDOM_POPULATION_SIZE - 1))
    return


def add_edges(db, graph):
    """Add the references as edges"""
    counter = 0
    for (source_doi, target_doi) in db.execute(
        f"""
        SELECT works.doi, work_references.doi
          FROM works
          INNER JOIN work_references on works.id = work_references.work_id
          WHERE work_references.doi is not null"""
    ):
        if counter == 0:
            perf.log("Obtain first edge")
        try:
            graph.add_edge(source_doi, target_doi)
        except ValueError:
            # It can happen that an unknown DOI is cited
            pass
        if counter % 1000000 == 0:
            progress_output("E", counter);
        counter += 1
    perf.log("Create edges")


def process_batch(start):
    results = []
    for doi in vertices_list[start:start + BATCH_SIZE]:
        results.append((doi, graph.timestamp(doi), graph.cdindex(doi, DELTA)))
    return results


if __name__ == '__main__':

    global graph
    graph = cdindex.Graph()
    if random_population:
        add_random_vertices(graph)
        add_random_edges(graph)
    else:
        db = sqlite3.connect(sys.argv[1])
        create_indexes(db)
        add_vertices(db, graph)
        add_edges(db, graph)
        db.close()

    if use_fast_cdindex:
        graph.prepare_for_searching()
        perf.log("Prepare graph for searching")

    # Shared between instances as a subscriptable list
    global vertices_list
    vertices_list = list(graph.vertices())

    # Calculate and add to the database the CD5 index for all works in the graph
    db = sqlite3.connect(sys.argv[2])
    db.execute("DROP TABLE IF EXISTS cdindex")
    db.execute("CREATE TABLE cdindex(doi, cdindex)")

    counter = 0
    cursor = db.cursor()
    for doi in graph.vertices():
        cursor.execute(
            "INSERT INTO cdindex VALUES(?, ?)",
            (doi, graph.cdindex(doi, DELTA)),
        )
        if counter % 1000000 == 0:
            progress_output("S", counter);
        counter += 1
    perf.log("Calculate CD index")

    db.commit()

    db.close()
