#!/usr/bin/env python
#
# Calculate the CD5 index of Crossref works published 1945-2010
# As an example of how Alexandria3k processing can be performed
# without an intermediate database, the calculation is performed
# on the fly, by iterating twice over the Crossref data set.
#

import csv
import datetime
from random import random, seed
import sys

from alexandria3k.crossref import Crossref
import cdindex

# Five years, for calculating the CD_5 index
DELTA = int(datetime.timedelta(days=365 * 5).total_seconds())

# Random sample of five containers for testing
seed("alexandria3k")
# crossref_instance = Crossref(sys.argv[1], lambda _name: random() < 0.0002)

crossref_instance = Crossref(sys.argv[1])

graph = cdindex.Graph()

container = None


def report_progress(i):
    """Report when the program progresses to a new container"""
    global container
    if container != i:
        print(f"Container {i}", file=sys.stderr)
        container = i


for (doi, year, month, day, i) in crossref_instance.query(
    """
        SELECT doi, published_year,
          Coalesce(published_month, 1),
          Coalesce(published_day, 1),
          container_id
        FROM works WHERE published_year BETWEEN 1945 and 2010"""
):
    report_progress(i)
    dt = datetime.datetime(year, month, day)
    graph.add_vertex(doi, cdindex.timestamp_from_datetime(dt))

for (source_doi, target_doi, i) in crossref_instance.query(
    """
    SELECT works.doi, work_references.doi, works.container_id
      FROM works
      INNER JOIN work_references on works.id = work_references.work_id
      WHERE work_references.doi is not null""",
    partition=True,
):
    report_progress(i)
    try:
        graph.add_edge(source_doi, target_doi)
    except ValueError:
        # It can happen that an unknown DOI is cited
        pass

# Calculate and output the CD5 index for all works in the graph
csv_writer = csv.writer(sys.stdout)
for doi in graph.vertices():
    csv_writer.writerow((doi, graph.timestamp(doi), graph.cdindex(doi, DELTA)))
