-- Count number of citations to each work in the last 5 years
CREATE INDEX IF NOT EXISTS work_references_doi_idx ON work_references(doi);
CREATE INDEX IF NOT EXISTS works_doi_idx ON works(doi);

CREATE TABLE rolap.work_citations AS
  SELECT work_references.doi,
      Coalesce(Count(work_references.doi), 0) AS citations_number
    FROM works AS cited_work
    LEFT JOIN work_references USING(doi)
    WHERE work_references.doi is not null
      AND cited_work.published_year BETWEEN
        ((SELECT year FROM rolap.reference) - 4)
          AND (SELECT year FROM rolap.reference)
    GROUP BY doi;
