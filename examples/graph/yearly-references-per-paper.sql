-- Average number of references each paper contains per year

CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

CREATE INDEX IF NOT EXISTS work_references_doi_idx ON work_references(doi);

WITH
  works_references AS (
    SELECT id, published_year
    FROM works
    INNER JOIN work_references ON works.id = work_references.work_id
    WHERE published_year BETWEEN 1945 and 2021
  ),
  papers_with_references AS (
    SELECT DISTINCT id, published_year
    FROM works_references
  ),
  yearly_papers_with_references AS (
    SELECT published_year, Count(*) AS n
    FROM papers_with_references
    GROUP BY published_year
  ),
  yearly_references AS (
    SELECT published_year, Count(*) AS n
    FROM works_references
    GROUP BY published_year
  )
SELECT yearly_papers_with_references.published_year,
  Cast(yearly_references.n AS float) / yearly_papers_with_references.n
FROM yearly_references
INNER JOIN yearly_papers_with_references
  ON yearly_references.published_year
    = yearly_papers_with_references.published_year
ORDER BY yearly_papers_with_references.published_year;
