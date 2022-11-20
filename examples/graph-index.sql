-- Create indexes for all (normalized) tables

CREATE INDEX works_doi_idx ON works(doi);
CREATE INDEX work_references_doi_idx ON work_references(doi);
CREATE INDEX work_references_work_doi_idx ON work_references(work_doi);
CREATE INDEX work_funders_id_idx ON work_funders(id);
CREATE INDEX work_funders_work_doi_idx ON work_funders(work_doi);
CREATE INDEX work_funders_doi_idx ON work_funders(doi);
CREATE INDEX funder_awards_funder_id_idx ON funder_awards(funder_id);
CREATE INDEX author_affiliations_author_id_idx ON author_affiliations(author_id);
CREATE INDEX work_subjects_work_doi_idx ON work_subjects(work_doi);
CREATE INDEX work_authors_work_doi_idx ON work_authors(work_doi);
CREATE INDEX work_authors_id_idx ON work_authors(id);
CREATE INDEX work_authors_orcid_idx ON work_authors(orcid);
CREATE INDEX affiliation_names_id_idx ON affiliation_names(id);
CREATE INDEX authors_affiliations_affiliation_id_idx ON authors_affiliations(affiliation_id);
CREATE INDEX authors_affiliations_author_id_idx ON authors_affiliations(author_id);
