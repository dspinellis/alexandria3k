-- Create a table containing a window of works published in the past ten years
CREATE TABLE rolap.ten_year_publications AS
  SELECT published_year AS year, Coalesce(
    Sum(n) OVER (
      ORDER BY published_year ROWS BETWEEN 11 PRECEDING AND 1 PRECEDING
    ), 0) AS n
  FROM yearly_works_all;
