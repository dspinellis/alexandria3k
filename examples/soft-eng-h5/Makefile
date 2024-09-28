#
# Calculate h5-index of authors
#

export MAINDB?=se-h5
export DEPENDENCIES=populate journal-names tables/se-5y.txt

include ../common/Makefile

# Populate database with required details for past five years
populate: $(CROSSREF_DIR)
	# Populate database with DOIs of works and their references
	$(TIME) $(A3K) --progress \
	  populate "$(MAINDB).db" crossref "$(CROSSREF_DIR)" \
	  --row-selection-file se-5y.sql
	touch $@

# Dummy rule to avoid simple-rolap using the query
tables/se-5y.txt: se-5y.sql
	mkdir -p tables
	touch $@
