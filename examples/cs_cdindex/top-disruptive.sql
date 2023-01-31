-- List the most disruptive papers
CREATE INDEX IF NOT EXISTS rolap.cdindex_work_id_idx ON cdindex(work_id);
CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);
CREATE INDEX IF NOT EXISTS rolap.cdindex_cdindex_idx ON cdindex(cdindex);

CREATE INDEX IF NOT EXISTS rolap.citations_number_work_id_idx
  ON citations_number(work_id);

CREATE INDEX IF NOT EXISTS rolap.references_number_work_id_idx
  ON references_number(work_id);

CREATE INDEX IF NOT EXISTS rolap.citations_number_n_idx
  ON citations_number(n);

CREATE INDEX IF NOT EXISTS rolap.references_number_n_idx
  ON references_number(n);

SELECT doi, cdindex, citations_number.n, references_number.n, title FROM works
  INNER JOIN rolap.cdindex ON works.id = cdindex.work_id
  INNER JOIN rolap.citations_number ON works.id = citations_number.work_id
  INNER JOIN rolap.references_number ON works.id = references_number.work_id
  WHERE references_number.n > 1
  ORDER BY cdindex DESC, citations_number.n DESC
  LIMIT 10;
