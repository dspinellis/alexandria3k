-- Affiliations associated with works on COVID research

CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);
CREATE INDEX IF NOT EXISTS work_authors_rors_work_author_id_idx
  ON work_authors_rors(work_author_id);
CREATE INDEX IF NOT EXISTS work_authors_id_idx ON work_authors(id);

-- Match works with identified authors' affiliations
WITH work_rors AS (
  -- Works and participating RORs
  SELECT DISTINCT work_id, ror_id
  FROM work_authors_rors
  LEFT JOIN work_authors
    ON work_authors_rors.work_author_id = work_authors.id
),

-- Count works by research organization (ROR)
ror_work_counts AS (
  SELECT ror_id, Count(*) AS number FROM work_rors GROUP BY ror_id
),

-- Add ROR names
ror_name_work_counts AS (
  SELECT name, number from ror_work_counts
  INNER JOIN research_organizations
    ON ror_work_counts.ror_id = research_organizations.id
),

-- Match works with unidentified author affiliations
unmatched_work_affiliations AS (
  SELECT DISTINCT work_id, author_affiliations.name
  FROM work_authors
  INNER JOIN author_affiliations
    ON work_authors.id = author_affiliations.author_id
  LEFT JOIN work_authors_rors
    ON work_authors_rors.work_author_id = work_authors.id
  WHERE work_authors_rors.ror_id is null
),

-- Count works by unidentified author affiliations
unmatched_affiliation_work_counts AS (
  SELECT name, Count(*) AS number FROM unmatched_work_affiliations
  GROUP BY name
),

-- Merge the two groups together
all_work_counts AS (
  SELECT * FROM ror_name_work_counts
  UNION
  SELECT * FROM unmatched_affiliation_work_counts
)

-- Output the top-20 affiliations according to number of published works
SELECT Rank() OVER (ORDER BY number DESC) AS rank, number, name
FROM all_work_counts
LIMIT 20;
