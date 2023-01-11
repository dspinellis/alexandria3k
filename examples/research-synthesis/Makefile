#
# Output types of research synthesis studies over the years
#

ALL=reports/research-synthesis.txt reports/total.txt reports/first-year.txt

include ../common/Makefile

reports/research-synthesis.txt: $(CROSSREF_DIR) research-synthesis.sql
	mkdir -p reports
	alexandria3k --data-source Crossref "$(CROSSREF_DIR)" \
	  --query-file research-synthesis.sql >$@

reports/total.txt: reports/research-synthesis.txt
	awk -F, '{ s += $$1 } END {print s}' $? >$@

reports/first-year.txt: reports/research-synthesis.txt
	 sort -t, -k2n $? | head -1 >$@
