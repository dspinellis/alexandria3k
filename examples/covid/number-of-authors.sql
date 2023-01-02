-- Calculate approximate number of study authors

WITH orcid_authors AS (
  SELECT count(*) AS n FROM (SELECT DISTINCT orcid FROM work_authors)
),
orcid_author_names AS (
  SELECT count(*) AS n FROM (
    SELECT DISTINCT family, given FROM work_authors WHERE orcid is not null
  )
),
all_author_names AS (
  SELECT count(*) AS n FROM (
    SELECT DISTINCT family, given FROM work_authors
  )
)
SELECT
  (SELECT n FROM all_author_names)
    * Cast((SELECT n FROM orcid_author_names) AS float)
      / (SELECT n FROM orcid_authors)
  AS authors;
