-- Number of funder records having an award each year

CREATE INDEX IF NOT EXISTS work_funders_work_id_idx ON work_funders(work_id);
CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

CREATE INDEX IF NOT EXISTS funder_awards_funder_id_idx
  ON funder_awards(funder_id);

SELECT published_year, Count(DISTINCT work_funders.id) n
  FROM works
  INNER JOIN work_funders
    ON work_funders.work_id = works.id
  INNER JOIN funder_awards
    ON funder_awards.funder_id = work_funders.id
  WHERE published_year is not null
  GROUP BY published_year
  ORDER BY published_year;
