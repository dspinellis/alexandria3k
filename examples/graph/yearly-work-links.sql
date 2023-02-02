-- Number of works each year having a text mining link

CREATE INDEX IF NOT EXISTS work_links_work_id_idx ON work_links(work_id);
CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

SELECT published_year, Count(DISTINCT works.id) n
  FROM works
  INNER JOIN work_links ON work_links.work_id = works.id
  WHERE published_year is not null
  GROUP BY published_year
  ORDER BY published_year;
