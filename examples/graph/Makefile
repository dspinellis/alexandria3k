#
# Create a graph of relationships between Crossref entities
# Based on it:
# - Create a chart of hierarchy relationships between subjects
# - Calculate various metrics
#

export MAINDB?=graph
export DEPENDENCIES=populate asjcs link-works-asjcs rors link-aa-base-ror

include ../common/Makefile

# Populate database with DOIs of works and their references
populate: $(CROSSREF_DIR)
	$(TIME) $(A3K) --progress \
	  populate "$(MAINDB).db" crossref "$(CROSSREF_DIR)" \
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

subject_hierarchy.svg: reports/subject-hierarchy-list.txt  subject-sankey.py
	python subject-sankey.py
