-- ORCIDs associated with each work

CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);
CREATE INDEX IF NOT EXISTS work_authors_work_id_idx ON work_authors(work_id);

CREATE TABLE rolap.works_orcid AS
  SELECT doi, orcid
  FROM works
  INNER JOIN work_authors ON works.id = work_authors.work_id
  WHERE orcid is not null;
