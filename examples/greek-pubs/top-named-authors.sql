-- Top ten name-identified authors
-- Author|Publications
SELECT  au.family || ", " || au.given AS auname, Count(*) FROM works
LEFT JOIN work_authors AS au ON au.work_id = works.id
WHERE auname IS NOT null
GROUP BY auname
ORDER BY Count(*) DESC
LIMIT 10;
