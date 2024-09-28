-- Calculate average CD-5 index per year

CREATE INDEX IF NOT EXISTS rolap.cdindex_doi_idx ON cdindex(doi);
CREATE INDEX IF NOT EXISTS works_doi_idx ON works(doi);

SELECT published_year AS year, Avg(cdindex) AS cdindex
  FROM rolap.cdindex
  INNER JOIN works ON works.doi = cdindex.doi
  WHERE cdindex is not null AND published_year is not null
  GROUP BY year
  -- Years to 2023 are needed for calculating CD5
  HAVING year <= 2018;
