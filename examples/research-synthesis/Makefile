#
# Output types of research synthesis studies over the years
#

export DEPENDENCIES=research-synthesis.txt

include ../common/Makefile

reports/research-synthesis.txt: $(CROSSREF_DIR)
	mkdir -p reports
	alexandria3k --data-source Crossref "$(CROSSREF_DIR)" \
	  --query-file research-synthesis.sql >$@
