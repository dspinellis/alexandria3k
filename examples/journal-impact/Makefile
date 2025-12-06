#
# Calculate journal impact metrics
#

# The year for which impact is calculated
export YEAR=2024

export MAINDB?=/tmp/impact
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
	  --row-selection "works.published_year between $$(expr $(YEAR) - 5)  and $(YEAR)"
	touch $@

# Create a test file without the headers and CSV format directives.
test: journal-impact-report-test.sql

journal-impact-report-test.sql: journal-impact-report.sql
	grep -v '^\.' $? >$@
