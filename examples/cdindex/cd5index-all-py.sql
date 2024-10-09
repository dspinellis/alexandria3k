-- Export the CD5 index for works where one can be calculated

CREATE INDEX IF NOT EXISTS rolap.valid_cd5index_doi_idx ON valid_cd5index(doi);

SELECT doi, cdindex FROM rolap.cdindex
  INNER JOIN rolap.valid_cd5index USING(doi);;
