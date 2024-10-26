-- Number of pages in an article per year

CREATE TABLE rolap.works_pages AS
  WITH page_data AS (
    SELECT published_year, page,
      Cast(Substr(page, Instr(page, '-') + 1) AS int) AS last_page,
      Cast(Substr(page, 0, Instr(page, '-')) AS int) AS first_page
    FROM works
    WHERE published_year BETWEEN 1945 and 2021
  )
  SELECT published_year AS year, page, last_page - first_page + 1 AS num_pages
  FROM page_data
  WHERE first_page != 0
    AND last_page != 0
    AND num_pages > 0;
