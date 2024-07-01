#
# Calculate software used in PubMed articles
# Filtered for 1997, 2007, 2017
#

export MAINDB?=pubmed_software
export DEPENDENCIES=populate

include ../common/Makefile

# Populate database with required details for the specified years
populate: $(PUBMED_DIR)
	# Populate database with pubmed articles and abstracts
	$(TIME) $(A3K) --progress \
	  populate "$(MAINDB).db" pubmed "$(PUBMED_DIR)" \
	  --columns pubmed_articles.id \
	    pubmed_articles.pubmed_id \
	    pubmed_articles.completed_year \
	    pubmed_articles.journal_year \
	    pubmed_articles.title \
	    pubmed_abstracts.article_id \
	    pubmed_abstracts.text \
	  --row-selection 'COALESCE(pubmed_articles.completed_year, pubmed_articles.journal_year) IN (1997, 2007, 2017)'
	touch $@

software_usage_total.svg: tables/fts_abstracts software.py
	python software.py
