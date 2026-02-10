#
# Calculate journal impact metrics
#

# The year for which impact is calculated
export YEAR=2024

export MAINDB?=/tmp/impact
export DEPENDENCIES=populate journal-names

include ../common/Makefile

# Populate database
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

# Create a test file
test: journal-impact-report-test.sql

journal-impact-report-test.sql: journal-impact-report.sql
	printf ".mode tabs\n.headers on\n" >$@
	grep -v '^\.' $? >>$@

# Calculate Journal Network Centrality
tables/network_centrality: tables/citation_network tables/publications5 journal_network_metrics.py
	./journal_network_metrics.py --metric network_centrality --db "$(MAINDB).db" --rolap-db "$(MAINDB).db"
	touch $@

# Calculate Prestige Weighted Rank
tables/prestige_rank: tables/citation_network3 tables/publications3 journal_network_metrics.py
	./journal_network_metrics.py --metric prestige_rank --db "$(MAINDB).db" --rolap-db "$(MAINDB).db"
	touch $@

# Calculate Mean Article Network Score
tables/mean_article_score: tables/citation_network tables/publications5 journal_network_metrics.py
	./journal_network_metrics.py --metric mean_article_score --db "$(MAINDB).db" --rolap-db "$(MAINDB).db"
	touch $@

# Calculate Context Normalized Impact
tables/context_impact: tables/bibliographic_coupling tables/publications3 tables/citation_network3 tables/journal_reference_density context_normalized_impact.py
	./context_normalized_impact.py --db "$(MAINDB).db" --rolap-db "$(MAINDB).db"
	touch $@
