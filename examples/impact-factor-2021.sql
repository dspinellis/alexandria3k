-- Calculate the 2021 journal impact factor

.print CREATE TABLE works_issn
CREATE TABLE IF NOT EXISTS works_issn AS
  SELECT id, doi,
    Coalesce(issn_print, issn_electronic) AS issn, published_year
  FROM works
  WHERE issn is not null
    -- To avoid news articles, book reviews, etc. include works longer than
    -- two pages
    AND Substr(page, Instr(page, "-") + 1)
      - Substr(page, 0, Instr(page, "-")) > 1;

.print CREATE INDEX EXISTS works_issn_doi_idx
CREATE INDEX IF NOT EXISTS works_issn_doi_idx ON works_issn(doi);

.print CREATE TABLE citations
CREATE TABLE IF NOT EXISTS citations AS
  SELECT cited_work.issn, COUNT(*) AS citations_number
  FROM work_references
  INNER JOIN works_issn AS published_work
    ON work_references.work_id = published_work.id
  INNER JOIN works_issn AS cited_work
    ON work_references.doi = cited_work.doi
  WHERE published_work.published_year = 2021
    AND cited_work.published_year BETWEEN 2019 AND 2020
  GROUP BY cited_work.issn;

.print CREATE TABLE publications
CREATE TABLE IF NOT EXISTS publications AS
  SELECT issn, COUNT(*) AS publications_number FROM works_issn
  WHERE published_year BETWEEN 2019 AND 2020
  GROUP BY issn;

.print CREATE TABLE impact_factor
CREATE TABLE IF NOT EXISTS impact_factor AS
  SELECT Replace(publications.issn, '-', '') AS issn,
    citations_number, publications_number,
    Cast(Coalesce(citations_number, 0) AS FLOAT) / publications_number
      AS impact_factor
  FROM publications
  LEFT JOIN citations ON citations.issn = publications.issn
  WHERE publications_number > 0;

/*
 * Some journals, e.g. Nature Reviews Immunology are identified through
 * their additional ISSN (14741733)
 * In other cases the same ISSN appears as an additional one for older
 * names of the journal, e.g. 00284793 for
 * Boston Medical and Surgical Journal, The New England Journal of Medicine
 * and Surgery and the Collateral Branches of Science, The New-England Medical
 * Review and Journal, New England Journal of Medicine
 * Use only one record, starting from Print and ending in Additional
 */
CREATE TABLE IF NOT EXISTS impact_factor_titles AS 
  WITH multiple_titles AS (
    SELECT impact_factor.issn, issn_type, title, impact_factor
      FROM impact_factor
      LEFT JOIN journals_issns
        ON impact_factor.issn = journals_issns.issn
      LEFT JOIN journal_names
        ON journals_issns.journal_id = journal_names.id
  ),
  prioritized_titles AS (
    SELECT *,
      Row_number() OVER (PARTITION BY issn ORDER BY issn_type DESC) AS priority
    FROM multiple_titles
  )
  SELECT issn, title, impact_factor FROM prioritized_titles
    WHERE priority = 1;

.print Top-10 impact factor journals
SELECT * FROM impact_factor_titles
  ORDER BY impact_factor DESC LIMIT 10;

.print Top-10 impact factor (non-review) journals
SELECT * FROM impact_factor_titles
  WHERE NOT title LIKE '%reviews%'
  ORDER BY impact_factor DESC LIMIT 10;
