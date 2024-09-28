#
# Calculate the 2021 journal impact factor
#

export MAINDB?=if-2021
export DEPENDENCIES=populate journal-names

include ../common/Makefile

# Populate database with rows and columns needed to calculate IF
populate: $(CROSSREF_DIR)
	$(TIME) $(A3K) --progress \
	  populate "$(MAINDB).db" crossref "$(CROSSREF_DIR)" \
	  --columns works.doi \
	   works.id \
	   works.issn_print \
	   works.issn_electronic \
	   works.page \
	   works.published_year \
	   work_references.work_id \
	   work_references.doi \
	  --row-selection 'works.published_year between 2019 and 2021'
	touch $@
