-- Number of author records and those with ORCID each year

CREATE INDEX IF NOT EXISTS work_authors_work_id_idx ON work_authors(work_id);
CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

SELECT published_year, Count(*) AS total, Count(orcid) AS orcid
  FROM works
  INNER JOIN work_authors ON work_authors.work_id = works.id
  WHERE published_year is not null
  GROUP BY published_year
  ORDER BY published_year;
