-- Calculate number of publications in the IF period

CREATE INDEX IF NOT EXISTS rolap.citable_works_published_year_idx
  ON citable_works(published_year);

CREATE TABLE rolap.publications AS
  SELECT issn, COUNT(*) AS publications_number
  FROM rolap.citable_works
  WHERE published_year BETWEEN 2019 AND 2020
  GROUP BY issn;
