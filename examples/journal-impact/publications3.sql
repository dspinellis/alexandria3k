-- Calculate number of publications in a 3-year SJR period

CREATE INDEX IF NOT EXISTS rolap.citable_works_published_year_idx
  ON citable_works(published_year);

CREATE TABLE rolap.publications3 AS
  SELECT journal_id, COUNT(*) AS publications_number
  FROM rolap.citable_works
  WHERE published_year BETWEEN
    ((SELECT year FROM rolap.reference) - 3)
    AND ((SELECT year FROM rolap.reference) - 1)
  GROUP BY journal_id;
