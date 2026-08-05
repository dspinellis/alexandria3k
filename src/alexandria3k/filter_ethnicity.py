"""
Script to filter and populate database with authors from a specific ethnicity
Currently name-ethinicity-classifier is being used and needs to be installed
for it to work
https://github.com/name-ethnicity-classifier
Note that this specific classifier works only with .csv files

Script takes arguments <ethnicity> <path to compressed files> [--rebuild]
 - "ethnicity" is the particular ethnicity filtered, provided by the model
 - "path to compressed files" is the path consisting the compressed jsonl
   files you want to filter
 - "--rebuild" drops classifications.db so every name is classified again

You dont need to populate the database into tables to use this script,
works on compressed files to save disk space

Classifications are kept in classifications.db which holds every name that
has been classified and every compressed file that has been read, so adding
files to the dataset only classifies the names that are new

Script calls a3k --attach-databases so filtered database can be populated
and used
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
CLASSIFICATIONS_DB = "classifications.db"
CONFIDENCE = 95
MIN_CONFIDENCE = 50


def create_databases():
    """Opens classifications.db and creates its tables when missing"""
    database = apsw.Connection(CLASSIFICATIONS_DB)
    database.execute(
        "CREATE TABLE IF NOT EXISTS classified_names "
        "(given, family, ethnicity, confidence)"
    )
    database.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_classified_name "
        "ON classified_names(given, family)"
    )
    database.execute("CREATE TABLE IF NOT EXISTS processed_files (file_name)")
    return database


def processed_files(database):
    """Returns the names of the compressed files already read"""
    return {
        row[0]
        for row in database.execute("SELECT file_name FROM processed_files")
    }


def extract_names(path, database):
    """
    Extracts author names from the compressed files that have not been read
    Returns the names and the files they were read from
    """
    names = set()
    files = [
        file
        for file in os.scandir(path)
        if file.name.endswith(".jsonl.gz")
        and file.name not in processed_files(database)
    ]

    read_files = []
    for i, file in enumerate(files, start=1):
        try:
            with gzip.open(file.path, "rt", encoding="utf-8") as f:
                for jsonl in f:
                    work = json.loads(jsonl)
                    for author in work.get("author", []):
                        given = author.get("given")
                        family = author.get("family")
                        if not given or not family:
                            continue
                        names.add((given, family))
        except (gzip.BadGzipFile, EOFError) as error:
            print(f"\nskipping {file.name}: {error}")
            continue

        read_files.append(file.name)
        print(f"\r{i}/{len(files)} files loaded", end="", flush=True)

    print("\nextracted names")
    return names, read_files


def unclassified(database, names):
    """Returns the names that are not in classified_names yet"""
    return [
        (given, family)
        for given, family in names
        if not list(
            database.execute(
                "SELECT 1 FROM classified_names WHERE given = ? AND family = ?",
                (given, family),
            )
        )
    ]


def classify_names(database, names):
    """
    Runs name-ethnicity-classifier on the given names
    Processes one chunk at a time to prevent out of memory errors
    Predictions keep the order of the names given to the classifier
    """
    start = time.time()
    print("running classifier")
    names = list(names)

    for i in range(0, len(names), CHUNK_SIZE):
        chunk_names = names[i : i + CHUNK_SIZE]

        with open(CHUNK_IN_P, "w", newline="", encoding="utf-8") as chunk:
            writer = csv.writer(chunk)
            writer.writerow(["names"])
            for given, family in chunk_names:
                writer.writerow([f"{given} {family}"])

        classifier = subprocess.run(
            [
                "python3",
                "predict_ethnicity.py",
                "-i",
                CHUNK_IN_P,
                "-o",
                CHUNK_OUT_P,
                "-m",
                MODEL,
                "-d",
                "gpu",
                "-b",
                "1024",
            ],
            cwd=CLASSIFIER,
            check=False,
        )

        if classifier.returncode != 0:
            print(f"\nchunk at {i} failed, skipping")
            continue

        with open(CHUNK_OUT_P, newline="", encoding="utf-8") as chunk_out:
            classifications = list(csv.reader(chunk_out))[1:]

        with database:
            for (given, family), classification in zip(
                chunk_names, classifications
            ):
                if float(classification[2]) < MIN_CONFIDENCE:
                    continue
                database.execute(
                    "INSERT OR IGNORE INTO classified_names VALUES (?, ?, ?, ?)",
                    (
                        given,
                        family,
                        classification[1],
                        float(classification[2]),
                    ),
                )

        print(
            f"\r{i + CHUNK_SIZE}/{len(names)} classified "
            f"{time.time() - start:.2f}s",
            end="",
            flush=True,
        )

    print(f"\n{time.time() - start:.2f}s")


def mark_processed(database, files):
    """Stores the compressed files whose names have been classified"""
    with database:
        for name in files:
            database.execute("INSERT INTO processed_files VALUES (?)", (name,))


def filter_names(database, ethnicity):
    """Returns the names classified as the given ethnicity"""
    return list(
        database.execute(
            "SELECT given, family FROM classified_names "
            "WHERE ethnicity = ? AND confidence >= ?",
            (ethnicity, CONFIDENCE),
        )
    )


def populate_database(ethnicity, path):
    """Attaches the database and populates it with works of the ethnicity"""
    subprocess.run(
        [
            "a3k",
            "populate",
            f"{ethnicity}.db",
            "crossref",
            path,
            "--attach-databases",
            f"attached:{CLASSIFICATIONS_DB}",
            "--row-selection",
            "EXISTS (SELECT 1 FROM attached.classified_names "
            "WHERE classified_names.given IS work_authors.given "
            "AND classified_names.family IS work_authors.family "
            f"AND classified_names.ethnicity = '{ethnicity}' "
            f"AND classified_names.confidence >= {CONFIDENCE})",
        ],
        check=True,
    )


def main():
    """
    Takes arguments <ethnicity> <path of compressed files> [--rebuild]
    Classifier used is name-ethnicity-classifier
    Names and their predicted ethnicity are stored in classifications.db
    together with the compressed files they were read from
    --rebuild drops classifications.db so every name is classified again
    Attach and populate the database using a3k --attach-databases
    Script produces populated tables which can be used for other processes
    """
    arguments = [
        argument for argument in sys.argv[1:] if argument != "--rebuild"
    ]
    rebuild = "--rebuild" in sys.argv

    if len(arguments) < 2:
        sys.exit(
            "usage: filter_ethnicity.py <ethnicity> "
            "<path containing compressed files> [--rebuild]"
        )

    ethnicity, path = arguments[0], arguments[1]

    with open(
        f"{CLASSIFIER}/model_configurations/{MODEL}/nationalities.json",
        encoding="utf-8",
    ) as f:
        nationalities = json.load(f)

    if ethnicity not in nationalities:
        sys.exit(
            f"unknown ethnicity '{ethnicity}'\n"
            f"supported: {', '.join(nationalities)}"
        )

    if rebuild and os.path.exists(CLASSIFICATIONS_DB):
        os.remove(CLASSIFICATIONS_DB)

    database = create_databases()

    names, read_files = extract_names(path, database)
    names = unclassified(database, names)
    if names:
        classify_names(database, names)
    mark_processed(database, read_files)

    print(f"{len(filter_names(database, ethnicity))} {ethnicity} names")
    print("populating names using a3k")
    populate_database(ethnicity, path)


if __name__ == "__main__":
    main()
