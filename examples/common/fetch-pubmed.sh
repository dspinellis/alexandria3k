#!/bin/bash

# downloads all MEDLINE/Pubmed citations in the annual baseline.

for i in $(seq 1 972); do
    fname="1"
    if ((i < 10)); then
        fname="ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/pubmed23n000$i.xml.gz"
    elif ((i < 100)); then
        fname="ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/pubmed23n00$i.xml.gz"
    elif ((i < 1000)); then
        fname="ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/pubmed23n0$i.xml.gz"
    fi
    echo $fname;
    wget $fname;
    sleep 2;
done