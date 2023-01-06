-- Indexes required by citation-graph.py

CREATE INDEX IF NOT EXISTS work_references_doi_idx ON work_references(doi);
CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);
CREATE INDEX IF NOT EXISTS works_doi_idx ON works(doi);
CREATE INDEX IF NOT EXISTS work_references_work_id_idx
  ON work_references(work_id);


SELECT 1;
