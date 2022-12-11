#!/bin/sh
#
# Output types of research synthesis studies over the years
#

alexandria3k --crossref-directory 'April 2022 Public Data File from Crossref' \
  -query-file research-synthesis.sql
