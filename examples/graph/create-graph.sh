#!/bin/sh
#
# Create a graph of interconnected indexed nodes of the Crossref database
# Omit leaf text elements
#

CROSSREF_DIR="${CROSSREF_DIR:-'April 2022 Public Data File from Crossref'}"
DB_FILE="${DB_FILE:-graph.db}"
TIME="${TIME:-time}"
INDEX_NORMALIZE=$(dirname "$0")/../common/index-normalize.sql

# Download, if needed, the Crossref data through the DOI torrent link
if ! [ -d "$CROSSREF_DIR" ] ; then
  aria2c https://doi.org/10.13003/83b2gq
fi

# Populate the database
$TIME alexandria3k --crossref-directory "$CROSSREF_DIR" \
 --populate "$DB_FILE" \
  --debug progress \
  --columns works.id \
  works.doi \
  works.published_year \
  work_references.work_id \
  work_references.doi \
  work_references.isbn \
  work_funders.id \
  work_funders.work_id \
  work_funders.doi \
  funder_awards.funder_id \
  funder_awards.name \
  author_affiliations.author_id \
  author_affiliations.name \
  work_links.work_id \
  work_subjects.work_id \
  work_subjects.name \
  work_authors.id \
  work_authors.work_id \
  work_authors.orcid

# Normalize tables and index
$TIME sqlite3 "$DB_FILE" <"$INDEX_NORMALIZE"
