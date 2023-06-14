#
# Analyze COVID-related research
#

export MAINDB?=covid
export DEPENDENCIES=populate asjcs link-works-asjcs rors link-aa-top-ror

include ../common/Makefile

# Populate database with COVID publications
populate: $(CROSSREF_DIR)
	$(TIME) $(A3K) --debug progress \
	  populate "$(MAINDB).db" crossref "$(CROSSREF_DIR)" \
	  --row-selection "title like '%COVID%' OR abstract like '%COVID%'"
	touch $@
