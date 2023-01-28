#!/usr/bin/env python
#
# Calculate the CD5 index of Crossref works published 1945-2021
# from a previously populated database
#

import concurrent.futures
import datetime
from more_itertools import chunked
import multiprocessing as mp
import random
import sqlite3
import sys

from alexandria3k import perf, debug
from fast_cdindex import cdindex, timestamp_from_datetime

# Five years, for calculating the CD_5 index
DELTA = int(datetime.timedelta(days=365 * 5).total_seconds())

BATCH_SIZE = 10000

RANGE = "published_year BETWEEN 1945 and 2021"

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


def add_random_vertices(db, graph):
    for i in range(1, 100000):
        graph.add_vertex(i, i)
    return


def add_vertices(db, graph):
    counter = 0
    for (doi, year, month, day) in db.execute(
        f"""
            SELECT doi, published_year,
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


def add_random_edges(db, graph):
    for i in range(1, 500000):
        graph.add_edge(random.randint(1, 100000 - 1), random.randint(1, 100000 - 1))
    return


def add_edges(db, graph):
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


def process_batch(doi_list):
    results = []
    for doi in doi_list:
        results.append((doi, graph.timestamp(doi), graph.cdindex(doi, DELTA)))
    return results


if __name__ == '__main__':
    db = sqlite3.connect(sys.argv[1])
    create_indexes(db)
    global graph
    graph = cdindex.Graph()
    add_vertices(db, graph)
    add_edges(db, graph)
    db.close()

    graph.prepare_for_searching()
    perf.log("Prepare graph for searching")

    # Calculate and add to the database the CD5 index for all works in the graph
    db = sqlite3.connect(sys.argv[2], check_same_thread=False)
    db.execute("DROP TABLE IF EXISTS cdindex")
    db.execute("CREATE TABLE cdindex(doi, timestamp, cdindex)")

    counter = 0
    with concurrent.futures.ProcessPoolExecutor(mp_context=mp.get_context('fork')) as executor:
        futures = []
        for chunk in chunked(graph.vertices(), BATCH_SIZE):
            future = executor.submit(process_batch, chunk)
            futures += [future]
            progress_output("S", counter);
            counter += 1
    perf.log("Submit work")

    counter = 0
    for future in concurrent.futures.as_completed(futures):
        results = future.result()
        db.executemany("INSERT INTO cdindex VALUES(?, ?, ?)", results)
        progress_output("R", counter);
        counter += 1
    perf.log("Calculate CD index")

    db.close()
