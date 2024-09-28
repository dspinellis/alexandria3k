#
# Calculate h5-index of authors
#

export MAINDB?=h5
export DEPENDENCIES=populate

include ../common/Makefile

# Populate database with required details for past five years
populate: $(CROSSREF_DIR)
	# Populate database with DOIs of works and their references
	$(TIME) $(A3K) --progress \
	  populate "$(MAINDB).db" crossref "$(CROSSREF_DIR)" \
	  --columns works.id \
	    works.doi \
	    work_references.doi \
	    work_references.work_id \
	    work_authors.work_id \
	    work_authors.orcid \
	  --row-selection 'works.published_year BETWEEN 2017 AND 2021'
	touch $@
