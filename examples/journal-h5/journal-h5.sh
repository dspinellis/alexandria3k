#!/bin/sh
#
# Calculate the h5-index of journals
#

CROSSREF_DIR="${CROSSREF_DIR:-'April 2022 Public Data File from Crossref'}"
DB_FILE="${DB_FILE:-5y.db}"
TIME="${TIME:-time}"
SQL_SCRIPT=$(dirname "$0")/journal-h5.sql

# Download, if needed the Crossref data through the DOI torrent link
if ! [ -d "$CROSSREF_DIR" ] ; then
  aria2c https://doi.org/10.13003/83b2gq
fi

# Populate database with DOIs of works and their references
$TIME alexandria3k --data-source Crossref "$CROSSREF_DIR"  \
  --populate-db-path "$DB_FILE" --debug progress \
  --columns works.doi works.issn_print works.issn_electronic \
    work_references.doi \
  --row-selection 'works.published_year BETWEEN 2017 AND 2021'

# Add journal names
$TIME alexandria3k --data-source journal-names --populate-db-path "$DB_FILE"

# Calculate journal h5-index
$TIME sqlite3 "$DB_FILE" <$SQL_SCRIPT
