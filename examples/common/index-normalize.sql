-- Normalize and index the graph database

.print CREATE INDEX works_doi_idx
CREATE INDEX IF NOT EXISTS works_doi_idx ON works(doi);
.print CREATE INDEX works_id_idx
CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);
.print CREATE INDEX work_references_doi_idx
CREATE INDEX IF NOT EXISTS work_references_doi_idx ON work_references(doi);
.print CREATE INDEX work_references_work_id_idx
CREATE INDEX IF NOT EXISTS work_references_work_id_idx ON work_references(work_id);
.print CREATE INDEX work_funders_id_idx
CREATE INDEX IF NOT EXISTS work_funders_id_idx ON work_funders(id);
.print CREATE INDEX work_funders_work_id_idx
CREATE INDEX IF NOT EXISTS work_funders_work_id_idx ON work_funders(work_id);
.print CREATE INDEX work_funders_doi_idx
CREATE INDEX IF NOT EXISTS work_funders_doi_idx ON work_funders(doi);
.print CREATE INDEX funder_awards_funder_id_idx
CREATE INDEX IF NOT EXISTS funder_awards_funder_id_idx ON funder_awards(funder_id);
.print CREATE INDEX author_affiliations_author_id_idx
CREATE INDEX IF NOT EXISTS author_affiliations_author_id_idx
  ON author_affiliations(author_id);
.print CREATE INDEX work_subjects_work_id_idx
CREATE INDEX IF NOT EXISTS work_subjects_work_id_idx ON work_subjects(work_id);
.print CREATE INDEX work_links_work_id_idx
CREATE INDEX IF NOT EXISTS work_links_work_id_idx ON work_links(work_id);
.print CREATE INDEX work_authors_work_id_idx
CREATE INDEX IF NOT EXISTS work_authors_work_id_idx ON work_authors(work_id);
.print CREATE INDEX work_authors_id_idx
CREATE INDEX IF NOT EXISTS work_authors_id_idx ON work_authors(id);
.print CREATE INDEX work_authors_orcid_idx
CREATE INDEX IF NOT EXISTS work_authors_orcid_idx ON work_authors(orcid);

-- Create subject_names id-name table and works_subjects many-to-many table

DROP TABLE IF EXISTS subject_names;
.print CREATE TABLE subject_names
CREATE TABLE subject_names AS
  SELECT row_number() OVER (ORDER BY '') AS id, name
    FROM (SELECT DISTINCT name FROM work_subjects);

.print CREATE INDEX subject_names_id_idx
CREATE INDEX subject_names_id_idx ON subject_names(id);

DROP TABLE IF EXISTS works_subjects;
.print CREATE TABLE works_subjects

.print CREATE INDEX works_subjects_subject_id_idx
CREATE INDEX works_subjects_subject_id_idx ON works_subjects(subject_id);
.print CREATE INDEX works_subjects_work_id_idx
CREATE INDEX works_subjects_work_id_idx ON works_subjects(work_id);

.print DROP TABLE work_subjects
DROP TABLE work_subjects;
