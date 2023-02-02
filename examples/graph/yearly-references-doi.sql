-- Number of reference records and those with DOI each year

CREATE INDEX IF NOT EXISTS work_references_work_id_idx
  ON work_references(work_id);

CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

SELECT published_year, Count(*) AS total, Count(work_references.doi) AS doi
  FROM works
  INNER JOIN work_references ON work_references.work_id = works.id
  WHERE published_year is not null
  GROUP BY published_year
  ORDER BY published_year;
