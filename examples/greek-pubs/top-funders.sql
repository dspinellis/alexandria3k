-- Top ten funders
-- Organization name|Funded works
SELECT name, Count(*)
  FROM work_funders
  INNER JOIN rolap.cleaned_works ON work_funders.work_id = cleaned_works.id
  GROUP BY name
  ORDER by count(*) DESC
  LIMIT 10;
