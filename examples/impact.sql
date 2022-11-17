ATTACH 'impact_data.db' AS impact_data;

CREATE TABLE works_issn AS
  SELECT Lower(doi) AS doi,
    Coalesce(issn_print, issn_electronic) AS issn, published_year
  FROM impact_data.works
  WHERE issn is not null;

CREATE index works_issn_doi_idx ON works_issn(doi);

CREATE TABLE citations AS
  SELECT cited_work.issn, COUNT(*) AS citations_number
  FROM impact_data.work_references
  INNER JOIN works_issn AS published_work
    ON Lower(work_references.work_doi) = published_work.doi
  INNER JOIN works_issn AS cited_work
    ON Lower(work_references.doi) = cited_work.doi
  WHERE published_work.published_year = 2021
    AND cited_work.published_year BETWEEN 2019 AND 2020
  GROUP BY cited_work.issn;

CREATE TABLE publications AS
  SELECT issn, COUNT(*) AS publications_number FROM works_issn
  WHERE published_year BETWEEN 2019 AND 2020
  GROUP BY issn;

CREATE TABLE impact_factor AS
  SELECT publications.issn, citations_number, publications_number,
    Cast(Coalesce(citations_number, 0) AS FLOAT) / publications_number
      AS impact_factor
  FROM publications
  LEFT JOIN citations ON citations.issn = publications.issn
  WHERE publications_number > 0;
