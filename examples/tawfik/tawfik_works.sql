-- Populate a table with the hand-cleaned works of D. Tawfik

CREATE TABLE tawfik_works(doi, given, family, published_year, issn_print);

.import --csv tawfik-works.txt tawfik_works

CREATE INDEX tawfik_works_doi_idx ON tawfik_works(doi);
CREATE INDEX tawfik_works_issn_print_idx ON tawfik_works(issn_print);
CREATE INDEX tawfik_works_published_year_idx ON tawfik_works(published_year);
