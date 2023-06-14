#
# Run standalone Crossref queries, without populating a database or
# using simple-rolap for running the queries.
#

include ../common/Makefile

all: reports/work-metrics.txt reports/yearly-journals.txt \
  reports/yearly-abstracts.txt

reports/work-metrics.txt: work-metrics.sql $(CROSSREF_DIR)
	mkdir -p reports
	$(TIME) $(A3K) query crossref $(CROSSREF_DIR) \
	  --query-file work-metrics.sql >$@

reports/yearly-journals.txt: yearly-journals.sql $(CROSSREF_DIR)
	mkdir -p reports
	$(TIME) $(A3K) query crossref $(CROSSREF_DIR) \
	  --field-separator '|' \
	  --query-file yearly-journals.sql >$@

reports/yearly-abstracts.txt: yearly-abstracts.sql $(CROSSREF_DIR)
	mkdir -p reports
	$(TIME) $(A3K) query crossref $(CROSSREF_DIR) \
	  --field-separator '|' \
	  --query-file yearly-abstracts.sql >$@
