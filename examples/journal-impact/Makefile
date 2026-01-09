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

# Calculate Eigenfactor scores
tables/eigenfactor: tables/citation_network tables/publications5 eigenfactor.py
	./eigenfactor.py --metric eigenfactor --db "$(MAINDB).db" --rolap-db "$(MAINDB).db"
	touch $@

# Calculate SJR (SCImago Journal Rank) scores
tables/sjr: tables/citation_network3 tables/publications3 eigenfactor.py
	./eigenfactor.py --metric sjr --db "$(MAINDB).db" --rolap-db "$(MAINDB).db"
	touch $@

# Calculate AIS (Article Influence Score)
tables/ais: tables/citation_network tables/publications5 eigenfactor.py
	./eigenfactor.py --metric ais --db "$(MAINDB).db" --rolap-db "$(MAINDB).db"
	touch $@

# Calculate SNIP (Source Normalized Impact per Paper) using Leiden clustering
# Requires: leidenalg, python-igraph
tables/snip: tables/bibliographic_coupling tables/publications3 tables/citation_network3 tables/journal_reference_density snip.py
	./snip.py --db "$(MAINDB).db" --rolap-db "$(MAINDB).db"
	touch $@
