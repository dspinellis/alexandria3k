-- Number of author records having an affiliation each year

CREATE INDEX IF NOT EXISTS work_authors_work_id_idx ON work_authors(work_id);
CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

CREATE INDEX IF NOT EXISTS author_affiliations_author_id_idx
  ON author_affiliations(author_id);

SELECT published_year, Count(DISTINCT work_authors.id) n
  FROM works
  INNER JOIN work_authors
    ON work_authors.work_id = works.id
  INNER JOIN author_affiliations
    ON author_affiliations.author_id = work_authors.id
  WHERE published_year is not null
  GROUP BY published_year
  ORDER BY published_year;
