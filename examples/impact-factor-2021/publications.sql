CREATE INDEX IF NOT EXISTS rolap.works_issn_published_year_idx
  ON works_issn(published_year);

CREATE TABLE IF NOT EXISTS rolap.publications AS
  SELECT issn, COUNT(*) AS publications_number
  FROM rolap.works_issn
  WHERE published_year BETWEEN 2019 AND 2020
  GROUP BY issn;

