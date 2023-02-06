-- Create a table containing a window of works published in the past 20 years
CREATE TABLE rolap.twenty_year_publications AS
  SELECT published_year AS year, Coalesce(
    Sum(n) OVER (
      ORDER BY published_year ROWS BETWEEN 21 PRECEDING AND 1 PRECEDING
    ), 0) AS n
  FROM rolap.yearly_works_all;
