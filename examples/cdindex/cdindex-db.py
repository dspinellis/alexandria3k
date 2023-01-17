#!/usr/bin/env python
#
# Calculate the CD5 index of Crossref works published 1945-2010
# from a previously populated database
#

import csv
import datetime
import sqlite3
import sys

import cdindex

# Five years, for calculating the CD_5 index
DELTA = int(datetime.timedelta(days=365 * 5).total_seconds())

graph = cdindex.Graph()

db = sqlite3.connect(sys.argv[1])

for (doi, year, month, day) in db.execute(
    """
        SELECT doi, published_year,
          Coalesce(published_month, 1),
          Coalesce(published_day, 1)
        FROM works WHERE published_year BETWEEN 1945 and 2010"""
):
    dt = datetime.datetime(year, month, day)
    graph.add_vertex(doi, cdindex.timestamp_from_datetime(dt))

for (source_doi, target_doi) in db.execute(
    """
    SELECT works.doi, work_references.doi
      FROM works
      INNER JOIN work_references on works.id = work_references.work_id
      WHERE work_references.doi is not null"""
):
    try:
        graph.add_edge(source_doi, target_doi)
    except ValueError:
        # It can happen that an unknown DOI is cited
        pass

# Calculate and output the CD5 index for all works in the graph
csv_writer = csv.writer(sys.stdout)
for doi in graph.vertices():
    csv_writer.writerow((doi, graph.timestamp(doi), graph.cdindex(doi, DELTA)))
