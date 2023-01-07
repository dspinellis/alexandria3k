CREATE INDEX IF NOT EXISTS author_affiliations_author_id_idx
  ON author_affiliations(author_id);
CREATE INDEX IF NOT EXISTS work_authors_id_idx ON work_authors(id);
CREATE INDEX IF NOT EXISTS work_authors_orcid_idx ON work_authors(orcid);
CREATE INDEX IF NOT EXISTS work_authors_work_id_idx ON work_authors(work_id);
CREATE INDEX IF NOT EXISTS work_references_doi_idx ON work_references(doi);
CREATE INDEX IF NOT EXISTS work_references_work_id_idx
  ON work_references(work_id);
CREATE INDEX IF NOT EXISTS works_doi_idx ON works(doi);
CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);
CREATE INDEX IF NOT EXISTS works_issn_print_idx ON works(issn_print);
CREATE INDEX IF NOT EXISTS works_published_year_idx ON works(published_year);

-- Dummy selection to have the statements executed
SELECT 1;
