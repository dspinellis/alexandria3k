-- Populate a table with Greek periodical edition ISSNs

DROP TABLE IF EXISTS greek_periodicals;

CREATE TABLE greek_periodicals(id PRIMARY KEY, issn, title);

.mode csv
.import greek-periodicals.csv greek_periodicals
