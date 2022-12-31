#
# Create a chart of hierarchy relationships between subjects
#

export RDBMS?=sqlite
export MAINDB?=graph
# Subject-hierarchy
export ROLAPDB?=sh
export DEPENDENCIES=populate asjcs link-works-asjcs

CROSSREF_DIR?=../common/Crossref-April-2022
TIME?=time
export SQLITE_TMPDIR=.


include simple-rolap/Makefile

reports/subject_hierarchy.svg: reports/subject_hierarchy.txt
	head -30 $< | ./hierarchy2dot.awk | dot -Tsvg >$@

$(CROSSREF_DIR):
	cd ../common && \
	aria2c https://doi.org/10.13003/83b2gq && \
	mv 'April 2022 Public Data File from Crossref' Crossref-April-2022

# Populate database with DOIs of works and their references
populate: $(CROSSREF_DIR)
	$(TIME) alexandria3k --data-source Crossref "$(CROSSREF_DIR)" \
	 --populate "$(MAINDB).db" \
	  --debug progress \
	  --columns works.id \
	  works.doi \
	  works.published_year \
	  work_references.work_id \
	  work_references.doi \
	  work_references.isbn \
	  work_funders.id \
	  work_funders.work_id \
	  work_funders.doi \
	  funder_awards.funder_id \
	  funder_awards.name \
	  author_affiliations.author_id \
	  author_affiliations.name \
	  work_links.work_id \
	  work_subjects.work_id \
	  work_subjects.name \
	  work_authors.id \
	  work_authors.work_id \
	  work_authors.orcid
	touch $@

asjcs: populate
	$(TIME) alexandria3k --data-source ASJC --populate "$(MAINDB).db"
	touch $@

link-works-asjcs: asjcs populate
	$(TIME) alexandria3k --execute link-works-asjcs \
	  --populate "$(MAINDB).db"
	touch $@

simple-rolap/Makefile:
	git clone https://github.com/dspinellis/simple-rolap
