-- Works published each year

CREATE TABLE rolap.yearly_works AS
  SELECT published_year AS year, Count(*) AS n
  FROM works
  GROUP BY published_year;
