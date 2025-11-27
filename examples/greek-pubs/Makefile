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

export CROSSREF_DIR
report.html: populate populate-greek-issns report.sh
	./report.sh >$@

populate-greek-issns: greek-periodicals.csv greek-periodicals.sql
	sqlite3 $(MAINDB).db <greek-periodicals.sql
	touch $@

# 1. Obtain periodicals from the Greek National Scientific Journal Catalogue
# https://eskep.ekt.gr/.
# Inspecting HTTP requests for a query for for Greek language periodicals
# gives the following URL, which may need adjustment.
greek-periodicals-raw.json:
	curl 'https://eskep.ekt.gr/eskep/journal/page?sEcho=10&iColumns=4&sColumns=&iDisplayStart=0&iDisplayLength=5000&mDataProp_0=0&mDataProp_1=1&mDataProp_2=2&mDataProp_3=3&prefix=&type=LANGUAGE&showAll=&identity=17&_=1764229079680' >$@

# 2. Clean up raw file
greek-periodicals.json: greek-periodicals-raw.json
	jq '.aaData | map({ id: (.DT_RowId | tonumber), title: .["0"], issn: .["1"] })' $? >$@

# 3. Convert raw file into CSV format
greek-periodicals.csv: greek-periodicals.json
	jq -r '.  | map(select(.issn != null)) | (.[] | [.id, .issn, .title]) | @csv' <$? >$@
