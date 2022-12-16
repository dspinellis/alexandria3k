-- Metrics of a normalized (and hopefully indexed) graph view

.print Works
SELECT Count(*) FROM works;
.print Works with a text mining link
SELECT Count(*) FROM (SELECT DISTINCT work_id FROM work_links);
.print Works with subject
SELECT Count(*) FROM (SELECT DISTINCT work_doi FROM works_subjects);
.print Works with references
SELECT Count(*) FROM (SELECT DISTINCT work_doi FROM work_references);
.print Works with affiliation
SELECT Count(*) FROM affiliations_works;
.print Works with an abstract
SELECT count(*) FROM works WHERE abstract is not null;
.print Works with funders
SELECT Count(*) FROM (SELECT DISTINCT work_doi FROM work_funders);

.print Author records
SELECT Count(*) FROM work_authors;
.print Author records with ORCID
SELECT Count(*) FROM work_authors WHERE orcid is not null;
.print Distinct authors with ORCID
SELECT Count(*) FROM (SELECT DISTINCT orcid FROM work_authors);

.print Author affiliation records
SELECT Count(*) FROM authors_affiliations;
.print Distinct affiliation names
SELECT Count(*) FROM affiliation_names;

.print Work subject records
SELECT Count(*) FROM works_subjects;
.print Distinct subject names
SELECT Count(*) FROM subject_names;

.print Work funders
SELECT Count(*) FROM work_funders;
.print Funder records with DOI
SELECT Count(*) FROM work_funders where doi is not null;
.print Distinct funder DOIs
SELECT Count(*) FROM (SELECT DISTINCT doi FROM work_funders WHERE doi is not null);
.print Funder awards
SELECT Count(*) FROM funder_awards;

.print References
SELECT Count(*) FROM work_references;
.print References with DOIs
SELECT Count(*) FROM work_references WHERE doi is not null OR isbn is not null;
.print Distinct reference DOIs
SELECT Count(*) FROM (SELECT DISTINCT doi FROM work_references WHERE doi is not null);
.print Distinct reference ISBNs
SELECT Count(*) FROM (SELECT DISTINCT isbn FROM work_references WHERE isbn is not null);
