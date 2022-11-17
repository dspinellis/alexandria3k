CREATE TABLE works_issn AS
  SELECT doi, Coalesce(issn_print, issn_electronic) AS issn, published_year
  FROM works
  WHERE issn is not null;

CREATE index works_issn_doi_idx ON works_issn(doi);

CREATE TABLE citations AS
  SELECT cited_work.issn, COUNT(*) AS citations_number
  FROM work_references
  INNER JOIN works_issn AS published_work
    ON work_references.work_doi = published_work.doi
  INNER JOIN works_issn AS cited_work
    ON work_references.doi = cited_work.doi
  WHERE published_work.published_year = 2021
  GROUP BY cited_work.issn;

CREATE TABLE publications AS
  SELECT issn, COUNT(*) AS publications_number FROM works_issn
  WHERE published_year BETWEEN 2019 AND 2020
  GROUP BY issn;

CREATE TABLE impact_factor AS
  SELECT publications.issn,
    Coalesce(citations_number, 0) / publications_number AS impact_factor
  FROM publications
  LEFT JOIN citations ON citations.issn = publications.issn
  WHERE publications_number > 0;
