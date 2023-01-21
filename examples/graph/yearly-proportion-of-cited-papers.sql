-- Proportion of all papers cited each year

CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

CREATE INDEX IF NOT EXISTS work_references_work_id_idx
  ON work_references(work_id);

CREATE INDEX IF NOT EXISTS works_doi_idx ON works(doi);

CREATE INDEX IF NOT EXISTS work_references_doi_idx ON work_references(doi);

WITH
  total_works_by_year AS (
    SELECT published_year AS year, Sum(n) OVER (ORDER BY published_year) AS n
    FROM rolap.yearly_works_all
  ),
  -- Papers referenced each year
  referenced_papers AS (
    SELECT DISTINCT citing_works.published_year AS year, cited_works.id
    FROM work_references
    INNER JOIN works AS cited_works
      ON cited_works.doi = work_references.doi
    INNER JOIN works AS citing_works
      ON citing_works.id = work_references.work_id
    WHERE citing_works.published_year BETWEEN 1945 and 2021
  ),
  referenced_papers_by_year AS (
    SELECT year, Count(*) AS n
    FROM referenced_papers
    GROUP BY year
  )
SELECT referenced_papers_by_year.year,
  Cast(referenced_papers_by_year.n AS float) / total_works_by_year.n
FROM total_works_by_year
INNER JOIN referenced_papers_by_year
  ON total_works_by_year.year = referenced_papers_by_year.year
ORDER BY referenced_papers_by_year.year;
