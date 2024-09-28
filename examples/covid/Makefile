#
# Analyze COVID-related research
#

export MAINDB?=covid
export DEPENDENCIES=populate asjcs link-works-asjcs rors link-aa-top-ror

include ../common/Makefile

# Populate database with COVID publications
populate: $(CROSSREF_DIR)
	$(TIME) $(A3K) --progress \
	  populate "$(MAINDB).db" crossref "$(CROSSREF_DIR)" \
	  --row-selection "title like '%COVID%' OR abstract like '%COVID%'"
	touch $@

reports/period-works-by-type.txt: period-works-by-type.sql $(CROSSREF_DIR)
	mkdir -p reports
	$(TIME) $(A3K) query crossref $(CROSSREF_DIR) \
	  --query-file period-works-by-type.sql >$@
