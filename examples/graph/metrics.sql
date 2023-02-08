-- Metrics of the graph view

CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

CREATE INDEX IF NOT EXISTS work_authors_id_idx ON work_authors(id);
CREATE INDEX IF NOT EXISTS work_authors_work_id_idx ON work_authors(work_id);

CREATE INDEX IF NOT EXISTS author_affiliations_author_id_idx
  ON author_affiliations(author_id);

CREATE INDEX IF NOT EXISTS work_authors_rors_work_author_id_idx
  ON work_authors_rors(work_author_id);

.print Works
SELECT Count(*) FROM works;
.print Works with a text mining link
SELECT Count(DISTINCT work_id) FROM work_links;
.print Works with subject
SELECT Count(DISTINCT work_id) FROM work_subjects;
.print Works with references
SELECT Count(DISTINCT work_id) FROM work_references;

.print Works with affiliation
SELECT Count(DISTINCT work_id)
  FROM works
  INNER JOIN work_authors on work_authors.work_id = works.id
  INNER JOIN author_affiliations
    ON author_affiliations.author_id = work_authors.id;

-- .print Works with an abstract
-- SELECT count(*) FROM works WHERE abstract is not null;

.print Works with funders
SELECT Count(DISTINCT work_id) FROM work_funders;

.print Author records
SELECT Count(*) FROM work_authors;
.print Author records with ORCID
SELECT Count(*) FROM work_authors WHERE orcid is not null;
.print Distinct authors with ORCID
SELECT Count(DISTINCT orcid) FROM work_authors;

.print Author affiliation records
SELECT Count(*) FROM author_affiliations;

.print Author records with research organization records matches
SELECT Count(*) FROM work_authors_rors;

.print Distinct affiliation names
SELECT Count(DISTINCT name) FROM author_affiliations;

.print Author records matched with research organization records
SELECT Count(DISTINCT work_author_id) FROM work_authors_rors;

.print Distinct matched research organization records
SELECT Count(DISTINCT ror_id) FROM work_authors_rors;

.print Works with a research organization record match
SELECT Count(*) FROM (
  SELECT DISTINCT work_authors.work_id
  FROM works
  INNER JOIN work_authors on work_authors.work_id = works.id
  INNER JOIN work_authors_rors
    ON work_authors_rors.work_author_id = work_authors.id
);

.print Work subject records
SELECT Count(*) FROM work_subjects;

.print Work funders
SELECT Count(*) FROM work_funders;
.print Funder records with DOI
SELECT Count(*) FROM work_funders where doi is not null;
.print Distinct funder DOIs
SELECT Count(DISTINCT doi) FROM work_funders WHERE doi is not null;
.print Funder awards
SELECT Count(*) FROM funder_awards;

.print References
SELECT Count(*) FROM work_references;
.print References with DOIs
SELECT Count(*) FROM work_references WHERE doi is not null OR isbn is not null;
.print Distinct reference DOIs
SELECT Count(DISTINCT doi) FROM work_references WHERE doi is not null;
