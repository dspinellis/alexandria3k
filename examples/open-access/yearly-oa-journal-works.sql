-- Number of open access journal papers per year

CREATE INDEX IF NOT EXISTS works_id_idx on works(id);
CREATE INDEX IF NOT EXISTS rolap.oa_works_work_id_idx on oa_works(work_id);

SELECT published_year, Count(*) AS n
  FROM works
  INNER JOIN rolap.oa_works ON works.id = oa_works.work_id
  WHERE published_year between 1945 and 2021
  GROUP BY published_year;
