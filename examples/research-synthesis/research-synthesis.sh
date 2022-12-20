#!/bin/sh
#
# Output types of research synthesis studies over the years
#

# Download, if needed the Crossref data through the DOI torrent link
if ! [ -d 'April 2022 Public Data File from Crossref' ] ; then
  aria2c https://doi.org/10.13003/83b2gq
fi

alexandria3k --data-source Crossref 'April 2022 Public Data File from Crossref' \
  --query-file research-synthesis.sql
