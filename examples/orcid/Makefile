#
# Calculate ORCID table metrics
#

export MAINDB?=orcid
export DEPENDENCIES=populate

include ../common/Makefile

# Populate database with ORCID data
populate: $(ORCID_SUMMARIES)
	$(TIME) $(A3K) --progress \
	  populate "$(MAINDB).db" orcid "$(ORCID_SUMMARIES)"
	touch $@
