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

-- Create affiliation_names id-name table and authors_affiliations,
-- works_affiliations many-to-many tables

DROP TABLE IF EXISTS affiliation_names;

.print CREATE TABLE affiliation_names
CREATE TABLE affiliation_names AS
  SELECT row_number() OVER (ORDER BY '') AS id, name
  FROM (SELECT DISTINCT name FROM author_affiliations);

.print CREATE INDEX affiliation_names_id_idx
CREATE INDEX affiliation_names_id_idx ON affiliation_names(id);

DROP TABLE IF EXISTS authors_affiliations;
.print CREATE TABLE authors_affiliations
CREATE TABLE authors_affiliations AS
  SELECT affiliation_names.id AS affiliation_id,
    author_affiliations.author_id
    FROM affiliation_names INNER JOIN author_affiliations
      ON affiliation_names.name = author_affiliations.name;

.print CREATE INDEX authors_affiliations_affiliation_id_idx
CREATE INDEX authors_affiliations_affiliation_id_idx
  ON authors_affiliations(affiliation_id);
.print CREATE INDEX authors_affiliations_author_id_idx
CREATE INDEX authors_affiliations_author_id_idx
  ON authors_affiliations(author_id);

DROP TABLE IF EXISTS works_affiliations;
.print CREATE TABLE works_affiliations
CREATE TABLE works_affiliations AS
  SELECT DISTINCT affiliation_id, work_authors.work_id
    FROM authors_affiliations
    LEFT JOIN work_authors ON authors_affiliations.author_id = work_authors.id;

.print CREATE INDEX works_affiliations_affiliation_id_idx
CREATE INDEX works_affiliations_affiliation_id_idx
  ON works_affiliations(affiliation_id);

.print CREATE INDEX works_affiliations_work_id_idx
CREATE INDEX works_affiliations_work_id_idx
  ON works_affiliations(work_id);

.print DROP TABLE author_affiliations
DROP TABLE author_affiliations;
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
CREATE TABLE works_subjects AS
  SELECT subject_names.subject_id AS subject_id, work_id
    FROM subject_names
    INNER JOIN work_subjects ON subject_names.name = work_subjects.name;

.print CREATE INDEX works_subjects_subject_id_idx
CREATE INDEX works_subjects_subject_id_idx ON works_subjects(subject_id);
.print CREATE INDEX works_subjects_work_id_idx
CREATE INDEX works_subjects_work_id_idx ON works_subjects(work_id);

.print DROP TABLE work_subjects
DROP TABLE work_subjects;
