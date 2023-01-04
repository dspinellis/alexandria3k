#
# Calculate ORCID table metrics
#

export MAINDB?=orcid
export DEPENDENCIES=populate

include ../common/Makefile

# Populate database with ORCID data
populate: $(ORCID_SUMMARIES)
	$(TIME) alexandria3k --data-source ORCID "$(ORCID_SUMMARIES)" \
	  --populate "$(MAINDB).db" \
	  --debug progress
	touch $@
