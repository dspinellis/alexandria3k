#
# Analyze open access availability of journal publications
#

export MAINDB?=oa
export DEPENDENCIES=populate asjcs doaj link-works-asjcs rors link-aa-base-ror

ALL=reports/oa-is-cited-more.txt reports/is-cited-by-is-normal.txt

include ../common/Makefile

# Populate database with DOIs of works and their references
populate: $(CROSSREF_DIR)
	$(TIME) $(A3K) --progress \
	  populate "$(MAINDB).db" crossref "$(CROSSREF_DIR)" \
	  --row-selection 'works.issn_print is not null OR works.issn_electronic is not null' \
	  --columns works.id \
	  works.doi \
	  works.published_year \
	  works.issn_print \
	  works.issn_electronic \
	  works.references_count \
	  works.is_referenced_by_count \
	  work_references.work_id \
	  work_references.doi \
	  work_funders.id \
	  work_funders.work_id \
	  work_funders.doi \
	  funder_awards.funder_id \
	  funder_awards.name \
	  author_affiliations.author_id \
	  author_affiliations.name \
	  work_links.work_id \
	  work_links.url \
	  work_links.content_type \
	  work_subjects.work_id \
	  work_subjects.name \
	  work_authors.id \
	  work_authors.work_id \
	  work_authors.orcid
	touch $@

reports/oa-is-cited-more.txt: oa-is-cited-more.py tables/oa_works
	$(EXPENSIVE_DEPENDENCIES) $(TIME) ./oa-is-cited-more.py >$@

reports/is-cited-by-is-normal.txt: is-cited-by-is-normal.py populate
	$(EXPENSIVE_DEPENDENCIES) $(TIME) ./is-cited-by-is-normal.py >$@
