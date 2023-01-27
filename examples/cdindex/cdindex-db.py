#!/usr/bin/env python
#
# Calculate the CD5 index of Crossref works published 1945-2010
# from a previously populated database
#

import datetime
import sqlite3
import sys

from fast_cdindex import cdindex, timestamp_from_datetime

# Five years, for calculating the CD_5 index
DELTA = int(datetime.timedelta(days=365 * 5).total_seconds())

graph = cdindex.Graph()

db = sqlite3.connect(sys.argv[1])

RANGE = "published_year BETWEEN 1945 and 2021"

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

counter = 0
for (source_doi, target_doi) in db.execute(
    f"""
    SELECT works.doi, work_references.doi
      FROM works
      INNER JOIN work_references on works.id = work_references.work_id
      WHERE work_references.doi is not null AND {RANGE}"""
):
    try:
        graph.add_edge(source_doi, target_doi)
    except ValueError:
        # It can happen that an unknown DOI is cited
        pass
    if counter % 100000 == 0:
        progress_output("E", counter);
    counter += 1
db.close()

db = sqlite3.connect(sys.argv[2])
# Calculate and add to the database the CD5 index for all works in the graph
db.execute("DROP TABLE IF EXISTS cdindex")
db.execute("CREATE TABLE cdindex(doi, timestamp, cdindex)")
cursor = db.cursor()
counter = 0
for doi in graph.vertices():
    cursor.execute(
        "INSERT INTO cdindex VALUES(?, ?, ?)",
        (doi, graph.timestamp(doi), graph.cdindex(doi, DELTA)),
    )
    if counter % 1000 == 0:
        progress_output("C", counter);
    counter += 1
db.commit()
db.close()
