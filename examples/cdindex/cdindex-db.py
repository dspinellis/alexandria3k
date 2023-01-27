#!/usr/bin/env python
#
# Calculate the CD5 index of Crossref works published 1945-2021
# from a previously populated database
#

import concurrent.futures
import datetime
from more_itertools import chunked
import sqlite3
import sys
from threading import Lock

from alexandria3k import perf, debug
from fast_cdindex import cdindex, timestamp_from_datetime

# Five years, for calculating the CD_5 index
DELTA = int(datetime.timedelta(days=365 * 5).total_seconds())

BATCH_SIZE = 10000

RANGE = "published_year BETWEEN 1945 and 2021"

graph = cdindex.Graph()

db = sqlite3.connect(sys.argv[1])

debug.set_flags(["perf"])
debug.set_output(sys.stderr)

db.execute("CREATE INDEX IF NOT EXISTS works_id_idx")
perf.log("CREATE INDEX works_id_idx ON works(id)")

db.execute("""CREATE INDEX IF NOT EXISTS works_published_year_idx
  ON works(published_year)""")
perf.log("CREATE INDEX works_published_year_idx")

db.execute("""CREATE INDEX IF NOT EXISTS work_references_work_id_idx
  ON work_references(work_id)""")
perf.log("CREATE INDEX work_references_work_id_idx")


def progress_output(phase, counter):
    """Report the progress of the specified phase and count"""
    timestamp = datetime.datetime.now().isoformat()
    print(f"{timestamp} {phase} {counter}", file=sys.stderr, flush=True)

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
    if counter % 100000 == 0:
        progress_output("E", counter);
    counter += 1
perf.log("Create edges")
db.close()

db = sqlite3.connect(sys.argv[2], check_same_thread=False)
# Calculate and add to the database the CD5 index for all works in the graph
db.execute("DROP TABLE IF EXISTS cdindex")
db.execute("CREATE TABLE cdindex(doi, timestamp, cdindex)")

lock = Lock()

def process_batch(doi_list):
    results = []
    for doi in doi_list:
        results.append((doi, graph.timestamp(doi), graph.cdindex(doi, DELTA)))
    with lock:
        try:
            db.execute("BEGIN EXCLUSIVE")
            db.executemany("INSERT INTO cdindex VALUES(?, ?, ?)", results)
            db.commit()
        except Exception as e:
            print(e)
    progress_output("C", "");


with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(process_batch, chunked(graph.vertices(), BATCH_SIZE))

perf.log("Calculate CD index")
db.close()
