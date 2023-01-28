#!/usr/bin/env -S sed -nf
1i\
DROP TABLE IF EXISTS cs_works;\
CREATE TABLE cs_works(doi);
s/^.*<ee>\(https:\/\/doi.org\/[^<]*\)<\/ee>.*/INSERT INTO cs_works VALUES("\1");/p
