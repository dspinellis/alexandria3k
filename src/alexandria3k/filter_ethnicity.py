"""
Script to filter and populate database with authors from a specific ethnicity
Currently name-ethinicity-classifier is being used and needs to be installed for it to work 
https://github.com/name-ethnicity-classifier
Note that this specific classifier works only with .csv files

Script takes arguments <ethnicity> <path to compressed files 
 - "ethnicity" is the particular ethnicity filtered, provided by the specific model
 - "path to compressed files" is the path consisting the compressed jsonl files you want to filter

You dont need to populate the database into tables to use this script, 
works on compressed files to save disk space

Script checks if ethnicities.csv file exists which is the output of the classifier 
else uses classifier to get ethnicities of all the names from the compressed files in arg-path

Then all authors from the chosen ethnicity get added into a database 

Script calls a3k --attach-databases so filtered database can be populated and used
"""

import subprocess
import time
import gzip
import json
import os
import csv
import sys

import apsw

CLASSIFIER = os.path.expanduser("~/name-ethnicity-classifier")
MODEL = "28_nationalities_english_once"
CHUNK_IN_P = os.path.abspath("chunk.csv")
CHUNK_OUT_P = os.path.abspath("chunk_out.csv")
CHUNK_SIZE = 500000

def extract_names(path):
    """Extracts every author name from the compressed jsonl files in path"""
    names = set()
    files_count = len(list(os.scandir(path)))
    for i , file in enumerate(os.scandir(path), 1):
        if not file.name.endswith(".jsonl.gz"):
            continue
        try:
            with gzip.open(file.path, "rt", encoding="utf-8") as f:
                for jsonl in f:
                    work = json.loads(jsonl)
                    for author in work.get("author", []):
                        given = author.get("given")
                        family = author.get("family")
                        if not given or not family:
                            continue
                        names.add(f"{given} {family}")
            print(f"\r{i}/{files_count} files loaded", end="", flush=True)
        except (gzip.BadGzipFile, EOFError) as error:
            print(f"\nskipping {file.name}: {error}")
            continue

    print("\nextracted names")
    return names


def classify_names(names):
    """
    Runs name-ethnicity-classifier on the extracted names
    Processes one chunk at a time to prevent out of memory errors
    """
    start = time.time()
    print("running classifier")
    names = sorted(names, key=len)
    with open("ethnicities.csv", "w", encoding="utf-8"):
        pass

    for i in range(0, len(names), CHUNK_SIZE):

        with open("chunk.csv", "w", newline="", encoding="utf-8") as chunk:
            writer = csv.writer(chunk)
            writer.writerow(["names"])
            for name in names[i:i + CHUNK_SIZE]:
                writer.writerow([name])

        classifier = subprocess.run(
            [
                "python3", "predict_ethnicity.py",
                "-i", CHUNK_IN_P,
                "-o", CHUNK_OUT_P,
                "-m", MODEL,
                "-d", "gpu",
                "-b", "1024",
            ],
            cwd=CLASSIFIER,
            check=False,
        )

        if classifier.returncode != 0:
            print(f"chunk at {i} failed, skipping")
            continue

        with open('chunk_out.csv', newline='', encoding="utf-8") as chunk_out:
            rows = list(csv.reader(chunk_out))[1:]

        with open('ethnicities.csv', 'a', newline='', encoding="utf-8") as ethnicities:
            csv.writer(ethnicities).writerows(rows)

        print(
            f"\r{i + CHUNK_SIZE}/{len(names)} classified {time.time() - start:.2f}s",
            end="" ,
            flush=True
        )

    print(f"\n{time.time() - start:.2f}s")

def filter_names(ethnicity):
    """Returns a list of all authors of a specific ethnicity"""
    with open('ethnicities.csv', newline='', encoding="utf-8") as ethnicities:
        names = [row for row in csv.reader(ethnicities)
                 if row[1] == ethnicity and float(row[2]) >= 95]

    names.sort(key=lambda row: float(row[2]), reverse=True)

    return names


def save_to_database(ethnicity, names):
    """Stores the filtered names in a database based of their ethnicity"""
    names_db = apsw.Connection(f"{ethnicity}_names.db")
    names_db.execute(f"DROP TABLE IF EXISTS {ethnicity}_names")
    names_db.execute(f"CREATE TABLE {ethnicity}_names (name, ethnicity, confidence)")
    names_db.execute(f"CREATE INDEX idx_{ethnicity}_name ON {ethnicity}_names(name)")


    for row in names:
        names_db.execute(f"INSERT INTO {ethnicity}_names VALUES (?, ?, ?)", row)


def populate_database(ethnicity, path):
    """Attaches the database and populates it only with the authors of the ethnicity"""
    subprocess.run(
        [
            "a3k", "populate", f"{ethnicity}.db", "crossref", path,
            "--attach-databases", f"attached:{ethnicity}_names.db",
            "--row-selection",
            f"EXISTS (SELECT 1 FROM attached.{ethnicity}_names "
            f"WHERE {ethnicity}_names.name = "
            f"work_authors.given || ' ' || work_authors.family)",
        ],
        check=True,
    )


def main():
    """
    Takes arguments <enthnicity> <path of comporessed files>
    Classifier used is name-ethnicity-classifier
    Classifier produces ethnicities.csv which contain the names and their predicted ethnicity
    From ethnicities.csv we extract all the names and add them into a database
    Attach and populate the database using a3k --attach-database based on names
    Script produces populated tables which can be used for other processes
    """
    if len(sys.argv) < 3:
        sys.exit("usage: filter_names.py <ethnicity> <path containing compressed files>")

    ethnicity = sys.argv[1]
    path = sys.argv[2]

    with open(
        f"{CLASSIFIER}/model_configurations/{MODEL}/nationalities.json",
        encoding="utf-8",
    ) as f:
        nationalities = json.load(f)

    if ethnicity not in nationalities:
        sys.exit(f"unknown ethnicity '{ethnicity}'\nsupported: {', '.join(nationalities)}")

    if not os.path.exists("ethnicities.csv"):
        classify_names(extract_names(path))

    names = filter_names(ethnicity)
    save_to_database(ethnicity, names)
    populate_database(ethnicity, path)


if __name__ == "__main__":
    main()
