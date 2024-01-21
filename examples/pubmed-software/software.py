#!/usr/bin/env python
#
#
#
import sqlite3

import numpy as np
import pandas as pd

SOFTWARE_LIST = [
    [
        "SPSS",
        "Statistical Package for the Social Sciences",
        "Statistical Product and Service Solutions",
    ],
    ["SAS", "Statistical Analysis System"],
    ["Stata"],
    [
        "R project",
        "R software",
        "R language",
        "R Programming Language",
        "Statistical Analysis with R",
        "R programming",
        "R statistical software",
        "R statistical package",
        "R statistical computing",
        "R statistical programming language",
        "R package",
        "CRAN",
    ],
    ["Excel"],
    ["GraphPad"],
    ["Review Manager", "RevMan"],
    ["Epi Info"],
    ["Statistica"],
    ["Lisrel"],
    ["JMP"],
    ["Minitab"],
    ["WinBUGS"],
    ["MedCalc"],
]

conn = sqlite3.connect("fts.db")
c = conn.cursor()
c.execute("ATTACH 'pubmed.db' AS pubmed")


def query_software(software):
    software = " OR ".join([f'"{s}"' for s in software])

    c.execute(
        f"""
        SELECT completed_year, COUNT(distinct(article_id)) FROM (
            SELECT article_id, completed_year FROM data
            WHERE (text MATCH '{software}' or title match '{software}') AND completed_year in (1997, 2007, 2017)
            GROUP BY article_id, completed_year
        )
        GROUP BY completed_year
        """
    )
    return c.fetchall()

df = pd.DataFrame(columns=["Software", "Year", "Count"])

for software in SOFTWARE_LIST:
    results = query_software(software)
    for year, count in results:
        print(software, year, count)
        software_name = software[0]
        df = pd.concat(
            [
                df,
                pd.DataFrame(
                    {"Software": software_name, "Year": year, "Count": count}, index=[0]
                ),
            ],
        )


software_search_string = " OR ".join(
    [" OR ".join([f'"{item}"' for item in s]) for s in SOFTWARE_LIST]
)

c.execute(
    f"""
    SELECT completed_year, COUNT(DISTINCT article_id) FROM (
        SELECT article_id, completed_year FROM data
        WHERE (text MATCH '{software_search_string}' OR title match '{software_search_string}') AND completed_year in (1997, 2007, 2017)
        GROUP BY article_id, completed_year
    )
    GROUP BY completed_year
    """
)

results = c.fetchall()

# Convert results to DataFrame
df_total = pd.DataFrame(results, columns=["Year", "Count"])

df.to_csv("software_counts_per_year.csv", index=False)
df_total.to_csv("software_counts_per_year_total.csv", index=False)

total_counts_df = df.groupby("Software")["Count"].sum().reset_index()

# Rename the columns for clarity
total_counts_df.columns = ["Software", "Total Count"]

print(total_counts_df)
