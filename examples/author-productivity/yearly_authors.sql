-- Number of authors publishing each year

CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

CREATE INDEX IF NOT EXISTS work_authors_work_id_idx ON work_authors(work_id);

CREATE TABLE rolap.yearly_authors AS
  WITH
    author_activity AS (
      SELECT published_year,
        CASE
          WHEN given is null or length(given) < 1 THEN family
          ELSE Substr(given, 1, 1) || '. ' || family
        END name
      FROM work_authors
      INNER JOIN works on work_authors.work_id = works.id
      WHERE published_year BETWEEN 1945 and 2021
    ),
    distinct_author_activity AS (
      SELECT DISTINCT * FROM author_activity
    )
  SELECT published_year AS year, Count(*) AS n
  FROM distinct_author_activity
  GROUP BY year;
