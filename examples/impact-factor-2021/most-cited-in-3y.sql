-- Find the most cited articles in the period 2019-2021
-- published within that period

SELECT works.doi, Count(*) FROM work_references
  LEFT JOIN works ON work_references.doi = works.doi
  WHERE published_year BETWEEN 2019 AND 2021
  GROUP BY works.doi
  ORDER BY Count(*) DESC
  LIMIT 10;
