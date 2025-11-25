-- Key dataset metrics
-- Metric|Value
-- Note: The quality of metadata is low.  Particularly problematic elements are ORCIDs, affiliations, funders, and awards.  Works with references — a mark of scholarly work — appear to be very few.

CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

CREATE INDEX IF NOT EXISTS work_authors_id_idx ON work_authors(id);
CREATE INDEX IF NOT EXISTS work_authors_work_id_idx ON work_authors(work_id);

CREATE INDEX IF NOT EXISTS author_affiliations_author_id_idx
  ON author_affiliations(author_id);

CREATE INDEX IF NOT EXISTS work_authors_rors_work_author_id_idx
  ON work_authors_rors(work_author_id);

SELECT 'Works' AS metric, (
  SELECT Count(*) FROM works) AS value UNION ALL
SELECT 'Works with a text mining link' AS metric, (
  SELECT Count(DISTINCT work_id) FROM work_links) AS value UNION ALL
SELECT 'Works with references' AS metric, (
  SELECT Count(DISTINCT work_id) FROM work_references) AS value UNION ALL

SELECT 'Works with affiliation' AS metric, (
  SELECT Count(DISTINCT work_id)
  FROM works
  INNER JOIN work_authors on work_authors.work_id = works.id
  INNER JOIN author_affiliations
    ON author_affiliations.author_id = work_authors.id) AS value UNION ALL

SELECT 'Works with an abstract' AS metric, (
  SELECT count(*) FROM works WHERE abstract is not null) AS value UNION ALL

SELECT 'Works with publication year' AS metric, (
  SELECT count(*) FROM works WHERE published_year is not null) AS value UNION ALL

SELECT 'Works with authors' AS metric, (
  SELECT Count(DISTINCT work_id) FROM work_authors) AS value UNION ALL

SELECT 'Works with funders' AS metric, (
  SELECT Count(DISTINCT work_id) FROM work_funders) AS value UNION ALL

SELECT 'Author records' AS metric, (
  SELECT Count(*) FROM work_authors) AS value UNION ALL
SELECT 'Author records with ORCID' AS metric, (
  SELECT Count(*) FROM work_authors WHERE orcid is not null) AS value UNION ALL
SELECT 'Distinct authors with ORCID' AS metric, (
  SELECT Count(DISTINCT orcid) FROM work_authors) AS value UNION ALL

SELECT 'Author affiliation records' AS metric, (
  SELECT Count(*) FROM author_affiliations) AS value UNION ALL

SELECT 'Author records with research organization records matches' AS metric, (
  SELECT Count(*) FROM work_authors_rors) AS value UNION ALL

SELECT 'Distinct affiliation names' AS metric, (
  SELECT Count(DISTINCT name) FROM author_affiliations) AS value UNION ALL

SELECT 'Author records matched with research organization records' AS metric, (
  SELECT Count(DISTINCT work_author_id) FROM work_authors_rors) AS value UNION ALL

SELECT 'Distinct matched research organization records' AS metric, (
  SELECT Count(DISTINCT ror_id) FROM work_authors_rors) AS value UNION ALL

SELECT 'Works with a research organization record match' AS metric, (
  SELECT Count(*) FROM (
  SELECT DISTINCT work_authors.work_id
  FROM works
  INNER JOIN work_authors on work_authors.work_id = works.id
  INNER JOIN work_authors_rors
    ON work_authors_rors.work_author_id = work_authors.id
)) AS value UNION ALL

SELECT 'Work funders' AS metric, (
  SELECT Count(*) FROM work_funders) AS value UNION ALL
SELECT 'Funder records with DOI' AS metric, (
  SELECT Count(*) FROM work_funders where doi is not null) AS value UNION ALL
SELECT 'Distinct funder DOIs' AS metric, (
  SELECT Count(DISTINCT doi) FROM work_funders WHERE doi is not null) AS value UNION ALL
SELECT 'Funder awards' AS metric, (
  SELECT Count(*) FROM funder_awards) AS value UNION ALL

SELECT 'References' AS metric, (
  SELECT Count(*) FROM work_references) AS value UNION ALL
SELECT 'References with DOIs' AS metric, (
  SELECT Count(*) FROM work_references WHERE doi is not null OR isbn is not null) AS value UNION ALL
SELECT 'Distinct reference DOIs' AS metric, (
  SELECT Count(DISTINCT doi) FROM work_references WHERE doi is not null) AS value;
