#!/usr/bin/env python

import sqlite3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SOFTWARE_LIST = {
    "SPSS": {
        "name": "SPSS",
        "synonyms": [
            "Statistical Package for the Social Sciences",
            "Statistical Product and Service Solutions",
        ],
        "original": {"total": 51.1, "1997": 27.9, "2007": 59.7, "2017": 51.3},
    },
    "SAS": {
        "name": "SAS",
        "synonyms": ["Statistical Analysis System"],
        "original": {"total": 12.9, "1997": 25.6, "2007": 24.6, "2017": 10.1},
    },
    "Stata": {
        "name": "Stata",
        "synonyms": [],
        "original": {"total": 12.6, "1997": 1.2, "2007": 1.8, "2017": 15.1},
    },
    "R": {
        "name": "R project",
        "synonyms": [
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
        "original": {"total": 9.7, "1997": 2.3, "2007": 0.4, "2017": 11.4},
    },
    "Excel": {
        "name": "Excel",
        "synonyms": [],
        "original": {"total": 9.4, "1997": 18.6, "2007": 5.6, "2017": 10.3},
    },
    "GraphPad": {
        "name": "GraphPad",
        "synonyms": [],
        "original": {"total": 5.5, "1997": 1.2, "2007": 0.4, "2017": 2.1},
    },
    "Review Manager": {
        "name": "Review Manager",
        "synonyms": ["RevMan"],
        "original": {"total": 3.6, "1997": 0, "2007": 5.4, "2017": 5.7},
    },
    "Epi Info": {
        "name": "Epi Info",
        "synonyms": [],
        "original": {"total": 1.8, "1997": 5.2, "2007": 5.6, "2017": 3.1},
    },
    "Statistica": {
        "name": "Statistica",
        "synonyms": [],
        "original": {"total": 1.7, "1997": 2.9, "2007": 1.9, "2017": 1.6},
    },
    "Lisrel": {
        "name": "Lisrel",
        "synonyms": [],
        "original": {"total": 1.3, "1997": 19.2, "2007": 2.8, "2017": 0.4},
    },
    "JMP": {
        "name": "JMP",
        "synonyms": [],
        "original": {"total": 0.9, "1997": 0.6, "2007": 1, "2017": 0.9},
    },
    "Minitab": {
        "name": "Minitab",
        "synonyms": [],
        "original": {"total": 0.6, "1997": 2.3, "2007": 1.5, "2017": 0.4},
    },
    "WinBUGS": {
        "name": "WinBUGS",
        "synonyms": [],
        "original": {"total": 0.6, "1997": 0, "2007": 1.8, "2017": 0.4},
    },
    "MedCalc": {
        "name": "MedCalc",
        "synonyms": [],
        "original": {"total": 0.6, "1997": 0, "2007": 0.1, "2017": 0.8},
    },
}


conn = sqlite3.connect("rolap.db")
c = conn.cursor()

all_software = [[s["name"]] + s["synonyms"] for s in SOFTWARE_LIST.values()]
software_search = " OR ".join(
    [" OR ".join([f'"{item}"' for item in s]) for s in all_software]
)

c.execute(
    f"""
    SELECT year, COUNT(DISTINCT(article_id)) FROM (
        SELECT article_id, year FROM fts_abstracts
        WHERE text MATCH '{software_search}' or title MATCH '{software_search}'
        GROUP BY article_id, year
    )
    GROUP BY year
    """
)

df_total = pd.DataFrame(c.fetchall(), columns=["Year", "Total count"])


def query_software(software):
    software_search = " OR ".join([f'"{s}"' for s in software])

    c.execute(
        f"""
        SELECT year, COUNT(DISTINCT(article_id)) FROM (
            SELECT article_id, year FROM fts_abstracts
            WHERE text MATCH '{software_search}' or title MATCH '{software_search}'
            GROUP BY article_id, year
        )
        GROUP BY year
        """
    )
    return c.fetchall()


df = pd.DataFrame(columns=["Software", "Year", "Count"])
for software in SOFTWARE_LIST.values():
    results = query_software([software["name"]] + software["synonyms"])
    for year, count in results:
        df = pd.concat(
            [
                df,
                pd.DataFrame(
                    {
                        "Software": software["name"],
                        "Year": year,
                        "Count": count,
                    },
                    index=[0],
                ),
            ],
        )

df = df.merge(df_total, on="Year")

df["Percentage"] = (df["Count"] / df["Total count"]) * 100
df = df.round(1)

original_data = []
for software, details in SOFTWARE_LIST.items():
    for year in ["1997", "2007", "2017", "total"]:
        if year in details["original"]:
            original_data.append(
                {
                    "Software": details["name"],
                    "Year": year,
                    "Original_Percentage": details["original"][year],
                }
            )

df_original = pd.DataFrame(original_data)


def plot_comparison(dataframe, original_df, year=None):
    if year:
        df_plot = dataframe[dataframe["Year"] == int(year)].copy()
        original_plot = original_df[original_df["Year"] == year].copy()
        title = f"Software usage percentage in {year}"
    else:
        df_plot = dataframe.groupby("Software")["Count"].sum().reset_index()
        total_count = df_plot["Count"].sum()
        df_plot["Percentage"] = (df_plot["Count"] / total_count) * 100
        original_plot = original_df[original_df["Year"] == "total"].copy()
        title = "Software usage; all years combined"

    df_plot = df_plot.merge(original_plot, on="Software", how="left")
    df_plot = df_plot.sort_values(by="Original_Percentage", ascending=True)

    max_percentage = max(
        df_plot["Percentage"].max(), df_plot["Original_Percentage"].max()
    )
    max_tick = round(max_percentage)

    fig, ax = plt.subplots(figsize=(12, 8))
    x = np.arange(len(df_plot["Software"]))
    width = 0.35

    ax.barh(
        x - width / 2,
        df_plot["Percentage"],
        width,
        label="Alexandria3K",
        color="darkorange",
    )
    ax.barh(
        x + width / 2,
        df_plot["Original_Percentage"].fillna(0),
        width,
        label="Masuadi et al. (2021)",
        color="green",
    )

    ax.set_xticks(np.arange(0, max_tick + 1, 5))
    plt.grid(axis="x", linestyle="--", alpha=0.6)

    ax.set_xlabel("Percentage")
    ax.set_title(title)
    ax.set_yticks(x)
    ax.set_yticklabels(df_plot["Software"])
    ax.legend()

    fig = plt.gcf()
    fig.set_size_inches(6, 6)
    fig.set_facecolor("w")
    if not year:
        fig.savefig("software_usage_total.svg", bbox_inches="tight")
    else:
        fig.savefig(f"sotware_usage_{year}.svg", bbox_inches="tight")

plot_comparison(df, df_original)

for year in ["1997", "2007", "2017"]:
    plot_comparison(df, df_original, year=year)
