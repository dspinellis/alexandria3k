-- Top ten author research organizations
-- Organization name|Authorships
SELECT  ror.name, Count(*) FROM work_authors_rors AS war
LEFT JOIN research_organizations AS ror ON war.ror_id = ror.id
GROUP BY ror.id
ORDER BY Count(*) DESC
LIMIT 10;
