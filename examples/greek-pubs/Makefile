#
# Analyze research written in Greek
#

export MAINDB?=greek
export ROLAPDB?=rolap
export DEPENDENCIES=populate rors link-aa-top-ror

ALL=report.html

include ../common/Makefile

# Populate database with Greek publications
populate: $(CROSSREF_DIR)
	$(TIME) $(A3K) --progress \
	  populate "$(MAINDB).db" crossref "$(CROSSREF_DIR)" \
	  --row-selection  "title GLOB '*[α-ω][α-ω][α-ω]*'"
	touch $@

export CROSSREF_DIR
report.html: populate populate-greek-periodicals report.sh \
  $(shell sed -n '/\.sql/s/ \\//p' report.sh)
	./report.sh >$@

populate-greek-periodicals: greek-periodicals.csv greek-periodicals.sql
	sqlite3 $(MAINDB).db <greek-periodicals.sql
	touch $@

tables/represented-periodicals tables/lib_issns: populate-greek-periodicals

# Obtain periodicals from the Greek National Scientific Journal Catalogue
# https://eskep.ekt.gr/.
# Inspecting HTTP requests for a query for for Greek language periodicals
# gives the following URL, which may need adjustment.
greek-language-periodicals.csv:
	./periodicals-csv.sh 'https://eskep.ekt.gr/eskep/journal/page?sEcho=10&iColumns=4&sColumns=&iDisplayStart=0&iDisplayLength=5000&mDataProp_0=0&mDataProp_1=1&mDataProp_2=2&mDataProp_3=3&prefix=&type=LANGUAGE&showAll=&identity=17&_=1764229079680' >$@

greek-country-periodicals.csv:
	./periodicals-csv.sh 'https://eskep.ekt.gr/eskep/journal/page?sEcho=1&iColumns=4&sColumns=&iDisplayStart=0&iDisplayLength=5000&mDataProp_0=0&mDataProp_1=1&mDataProp_2=2&mDataProp_3=3&prefix=&type=COUNTRY&showAll=&identity=83&_=1764319469382' >$@

greek-periodicals.csv: greek-language-periodicals.csv greek-country-periodicals.csv
	sort -u $^ >$@
