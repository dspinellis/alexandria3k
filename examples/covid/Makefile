#
# Analyze COVID-related research
#

export MAINDB?=covid
export DEPENDENCIES=populate asjcs link-works-asjcs rors link-aa-top-ror

include ../common/Makefile

# Populate database with COVID publications
populate: $(CROSSREF_DIR)
	$(TIME) alexandria3k --data-source Crossref "$(CROSSREF_DIR)"  \
	  --populate-db-path "$(MAINDB).db" --debug progress \
	  --row-selection "title like '%COVID%' OR abstract like '%COVID%'"
	touch $@
