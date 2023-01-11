-- Create a report with average number of authors per decade
SELECT Cast(published_year / 10 AS int) * 10 AS decade, Avg(num_authors) AS avg_num_authors
  FROM rolap.num_work_authors
  INNER JOIN works on num_work_authors.work_id = works.id
  GROUP BY decade
  ORDER BY decade;
