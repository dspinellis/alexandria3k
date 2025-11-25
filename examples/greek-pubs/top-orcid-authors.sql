-- Top ten ORCID-identified authors
-- Author|ORCID|Publications
SELECT  au.family || ", " || au.given, orcid, Count(*) FROM works
LEFT JOIN work_authors AS au ON au.work_id = works.id
WHERE orcid is not null
GROUP BY orcid
ORDER BY Count(*) DESC
LIMIT 10;
