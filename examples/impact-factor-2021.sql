-- Calculate the 2021 journal impact factor

ATTACH 'impact_data.db' AS impact_data;

CREATE TABLE works_issn AS
  SELECT doi AS doi,
    Coalesce(issn_print, issn_electronic) AS issn, published_year
  FROM impact_data.works
  WHERE issn is not null;

CREATE INDEX works_issn_doi_idx ON works_issn(doi);

CREATE TABLE citations AS
  SELECT cited_work.issn, COUNT(*) AS citations_number
  FROM impact_data.work_references
  INNER JOIN works_issn AS published_work
    ON work_references.work_doi = published_work.doi
  INNER JOIN works_issn AS cited_work
    ON work_references.doi = cited_work.doi
  WHERE published_work.published_year = 2021
    AND cited_work.published_year BETWEEN 2019 AND 2020
  GROUP BY cited_work.issn;

CREATE TABLE publications AS
  SELECT issn, COUNT(*) AS publications_number FROM works_issn
  WHERE published_year BETWEEN 2019 AND 2020
  GROUP BY issn;

CREATE TABLE impact_factor AS
  SELECT Replace(publications.issn, '-', '') AS issn,
    citations_number, publications_number,
    Cast(Coalesce(citations_number, 0) AS FLOAT) / publications_number
      AS impact_factor
  FROM publications
  LEFT JOIN citations ON citations.issn = publications.issn
  WHERE publications_number > 0;

UPDATE Journal_data SET issn_print=Replace(issn_print, "-", "");
UPDATE Journal_data SET issn_eprint=Replace(issn_eprint, "-", "");

CREATE INDEX journal_names_issn_print_idx ON journal_names(issn_print);
CREATE INDEX journal_names_issn_eprint_idx ON journal_names(issn_eprint);

SELECT issn, title, impact_factor
  FROM impact_factor
  LEFT JOIN journal_names
    ON impact_factor.issn = journal_names.issn_print
      OR impact_factor.issn = journal_names.issn_eprint
ORDER BY impact_factor DESC LIMIT 30;
