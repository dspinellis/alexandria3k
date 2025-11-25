#
# Analyze research written in Greek
#

export MAINDB?=greek
export DEPENDENCIES=populate rors link-aa-top-ror

ALL=report.html

include ../common/Makefile

# Populate database with COVID publications
populate: $(CROSSREF_DIR)
	$(TIME) $(A3K) --progress \
	  populate "$(MAINDB).db" crossref "$(CROSSREF_DIR)" \
	  --row-selection  "title GLOB '*[α-ω][α-ω][α-ω]*'"
	touch $@

report.html: populate report.sh
	./report.sh >$@
