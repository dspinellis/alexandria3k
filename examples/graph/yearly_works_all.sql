CREATE TABLE rolap.yearly_works_all AS
  SELECT published_year, Count(*) AS n
  FROM works
  GROUP BY published_year;
