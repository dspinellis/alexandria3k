-- Workd of each author by year
CREATE TABLE rolap.author_year_works AS
  SELECT orcid, published_year AS year, Count(*) AS articles
  FROM works
  INNER JOIN work_authors ON work_authors.work_id = works.id
  WHERE orcid is not null AND published_year is not null
  GROUP BY orcid, year;
