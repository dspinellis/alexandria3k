-- Create a table of publications for which a valid CD5 index can be calculated

CREATE INDEX IF NOT EXISTS rolap.cdindex_doi_idx ON cdindex(doi);

CREATE TABLE rolap.valid_cd5index AS
  SELECT cdindex.doi FROM rolap.cdindex
      INNER JOIN works USING(doi)
      WHERE works.published_year <= 2018 AND
      (SELECT 1 FROM work_references WHERE work_id == works.id);
