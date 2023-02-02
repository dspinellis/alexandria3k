-- Number of works each year having a subject

CREATE INDEX IF NOT EXISTS work_subjects_work_id_idx ON work_subjects(work_id);
CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

SELECT published_year, Count(DISTINCT works.id) n
  FROM works
  INNER JOIN work_subjects ON work_subjects.work_id = works.id
  WHERE published_year is not null
  GROUP BY published_year
  ORDER BY published_year;
