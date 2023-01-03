#
# Calculate h5-index of journals
#

export MAINDB?=h5
export DEPENDENCIES=populate journal-names

include ../common/Makefile

# Populate database with required details for past five years
populate: $(CROSSREF_DIR)
	# Populate database with DOIs of works and their references
	$(TIME) alexandria3k --data-source Crossref "$(CROSSREF_DIR)" \
	  --populate "$(MAINDB).db" \
	  --debug progress \
	  --columns works.doi works.issn_print works.issn_electronic \
	    work_references.doi \
	  --row-selection 'works.published_year BETWEEN 2017 AND 2021'
	touch $@
