#!/bin/bash

# downloads all MEDLINE/Pubmed citations in the annual baseline.
mkdir pubmed-data
cd pubmed-data

# each year the file names change, so we need to get the current year
year=$(date +'%y')

for i in $(seq 1 972); do
    if ((i < 10)); then
        fname="ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/pubmed${year}n000$i.xml.gz"
    elif ((i < 100)); then
        fname="ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/pubmed${year}n00$i.xml.gz"
    else
        fname="ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/pubmed${year}n0$i.xml.gz"
    fi
    echo "Downloading: $fname"
    wget $fname
    sleep 2
done