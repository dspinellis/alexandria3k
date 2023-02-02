-- Number of funder records and those with DOI each year

CREATE INDEX IF NOT EXISTS work_funders_work_id_idx ON work_funders(work_id);

CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

SELECT published_year, Count(*) AS total, Count(work_funders.doi) AS doi
  FROM works
  INNER JOIN work_funders ON work_funders.work_id = works.id
  WHERE published_year is not null
  GROUP BY published_year
  ORDER BY published_year;
