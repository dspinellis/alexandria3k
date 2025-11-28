-- Top ten author affiliations
-- Affiliation|Publications
SELECT  aa.name, Count(*) FROM rolap.cleaned_works AS works
  LEFT JOIN work_authors ON work_authors.work_id = works.id
  LEFT JOIN author_affiliations AS aa ON work_authors.id = aa.author_id
  WHERE aa.name IS NOT null
  GROUP BY aa.name
  ORDER BY Count(*) DESC
  LIMIT 10;
