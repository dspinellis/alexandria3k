#!/bin/sh
#
# Calculate the h5-index of journals
#

# Download, if needed the Crossref data through the DOI torrent link
if ! [ -d 'April 2022 Public Data File from Crossref' ] ; then
  aria2c https://doi.org/10.13003/83b2gq
fi

# Populate database with DOIs of works and their references
alexandria3k --crossref-directory 'April 2022 Public Data File from Crossref'  \
  --populate-db-path 5y.db --debug progress \
  --columns works.doi works.issn_print works.issn_electronic \
    work_references.doi \
  --row-selection 'works.published_year BETWEEN 2017 AND 2021'

# Add journal names
alexandria3k --journal-names --populate-db-path 5y.db

# Calculate journal h5-index
sqlite3 5y.db <journal-h5.sql
