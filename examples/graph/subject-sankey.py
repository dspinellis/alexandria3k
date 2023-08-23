#!/usr/bin/env python
#
# Draw the Sankey diagram associated with dependencies between subjects
#

import pandas as pd
import matplotlib.pyplot as plt

# Import the sankey function from the sankey module within pySankey
from pySankey.sankey import sankey

df = pd.read_csv("reports/subject-hierarchy-list.txt", sep="|", header=None)
df.columns = [
    "citing_name",
    "citing_asjc",
    "citing_citations",
    "cited_name",
    "cited_asjc",
    "cited_citations",
    "fundamentalness",
    "strenght",
]

scale = sum(df["citing_citations"]) / sum(df["cited_citations"])
print(f"scale={scale}")

sankey(
    left=df["citing_name"], right=df["cited_name"],
    leftWeight= df["citing_citations"], rightWeight=df["cited_citations"] * scale,
    aspect=20, fontsize=6
)

# Get current figure
fig = plt.gcf()

# Set size in inches
fig.set_size_inches(6, 6)

# Set the color of the background to white
fig.set_facecolor("w")

# Save the figure
fig.savefig("subject_hierarchy.svg", bbox_inches="tight")
