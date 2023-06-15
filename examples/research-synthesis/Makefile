#
# Output types of research synthesis studies over the years
#

ALL=reports/research-synthesis.txt reports/total.txt reports/first-year.txt

include ../common/Makefile

reports/research-synthesis.txt: $(CROSSREF_DIR) a3k-queries/research-synthesis.sql
	mkdir -p reports
	$(TIME) $(A3K) query crossref "$(CROSSREF_DIR)" \
	  --query-file a3k-queries/research-synthesis.sql >$@

reports/early-studies.txt: $(CROSSREF_DIR) a3k-queries/early-studies.sql
	mkdir -p reports
	$(TIME) $(A3K) query crossref "$(CROSSREF_DIR)" \
	  --query-file a3k-queries/early-studies.sql >$@

reports/total.txt: reports/research-synthesis.txt
	awk -F, '{ s += $$1 } END {print s}' $? >$@

reports/first-year.txt: reports/research-synthesis.txt
	 sort -t, -k2n $? | head -1 >$@
