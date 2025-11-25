-- Top ten funders
-- Organization name|Funded works
SELECT name, Count(*)
  FROM work_funders
  GROUP BY name
  ORDER by count(*) DESC
  LIMIT 10;
