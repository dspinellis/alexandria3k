-- Affiliations associated with works on COVID research

WITH work_rors AS (
  -- Works and participating RORs
  SELECT DISTINCT work_id, ror_id
  FROM work_authors_rors
  LEFT JOIN work_authors
    ON work_authors_rors.work_author_id = work_authors.id
),
ror_work_counts AS (
  SELECT ror_id, Count(*) AS number FROM work_rors GROUP BY ror_id
),
ror_name_work_counts AS (
  SELECT * from ror_work_counts
  INNER JOIN research_organizations
    ON ror_work_counts.ror_id = research_organizations.id
)
SELECT Rank() OVER (ORDER BY number DESC) AS rank, number, name
FROM ror_name_work_counts
LIMIT 20;
