#!/usr/bin/env -S sed -nf
#
# Convert DBLP dump into SQL statements to create and populate table
# with CS DOIs
#

1i\
DROP TABLE IF EXISTS cs_works;\
CREATE TABLE cs_works(doi);
s/^.*<ee>\(https:\/\/doi.org\/[^<]*\)<\/ee>.*/INSERT INTO cs_works VALUES("\1");/p
