-- Top 20 affiliations of Greek-named authors, by unique orcid
SELECT
  author_affiliations.name AS affiliation,
  COUNT(DISTINCT work_authors.orcid) AS authors
FROM author_affiliations
JOIN work_authors ON work_authors.id = author_affiliations.author_id
JOIN author_ethnicities ON author_ethnicities.work_author_id = work_authors.id
WHERE author_ethnicities.ethnicity = 'greek'
  AND work_authors.orcid IS NOT NULL
GROUP BY affiliation
ORDER BY authors DESC
LIMIT 20
