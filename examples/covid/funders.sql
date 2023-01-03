-- Funders of COVID research by number of papers referencing them

SELECT rank() OVER (ORDER BY count(*) DESC) AS rank, count(*) AS number, name
  FROM work_funders GROUP BY name
  LIMIT 20;
