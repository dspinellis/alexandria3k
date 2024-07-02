#
# Calculate DataCite table metrics
#

export MAINDB?=datacite
export DEPENDENCIES=populate

include ../common/Makefile

# Populate database with DataCite data
populate: $(DATACITE)
	$(TIME) $(A3K) --progress \
	  populate "$(MAINDB).db" datacite "$(DATACITE)"
	touch $@
