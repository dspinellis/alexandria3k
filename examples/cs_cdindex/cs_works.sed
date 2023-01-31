#!/usr/bin/env -S sed -nf
#
# Convert DBLP dump into SQL statements to create and populate table
# with CS DOIs
#

1i\
DROP TABLE IF EXISTS dois;\
CREATE TABLE dois(doi);

# Create indices
$a\
CREATE INDEX IF NOT EXISTS dois_doi_idx ON dois(doi);

# Isolate DOI
s/^.*<ee>https:\/\/doi.org\/\([^<]*\)<\/ee>.*/INSERT INTO dois VALUES("\1");/
T

# For to lowercase
y/ABCDEFGHIJKLMNOPQRSTUVWXYZ/abcdefghijklmnopqrstuvwxyz/

# Replace common escapes
s/&amp;/\&/g
s/&lt;/</g
s/&gt;/>/g
s/&ndash;/-/g
s/&#x003c;/</g
s/&#x003e;/>/g
s/&#60;/</g
s/&#62;/>/g
p

