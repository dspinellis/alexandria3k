#
# Calculate software used in PubMed articles
# Filtered for 1997, 2007, 2017
#

export MAINDB?=pubmed_software
export DEPENDENCIES=populate

include ../common/Makefile

# Populate database with required details for past five years
populate: $(PUBMED_DIR)
	# Populate database with pubmed articles and abstracts
	$(TIME) $(A3K) --debug progress_bar \
	  populate "$(MAINDB).db" pubmed "$(PUBMED_DIR)" \
	  --columns pubmed_articles.id \
	    pubmed_articles.pubmed_id \
	    pubmed_articles.completed_year \
	    pubmed_articles.title \
	    pubmed_abstracts.article_id \
	    pubmed_abstracts.text \
		pubmed_keywords.article_id \
		pubmed_keywords.keyword \
	  --row-selection 'pubmed_articles.completed_year IN (1997, 2007, 2017)'
	touch $@
