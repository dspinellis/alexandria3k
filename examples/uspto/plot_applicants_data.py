#
# Alexandria3k Patent grant bibliographic metadata processing
# Copyright (C) 2023  Aggelos Margkas
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
"""Plot applicants population by country and year for the top 5 countries of 2022"""


import pandas as pd
import matplotlib.pyplot as plt

# Read the CSV file into a Pandas DataFrame
data = pd.read_csv("top5applicantcountries.csv")

# Pivot the DataFrame to have years as columns and countries as index
pivot_data = data.pivot(index="Country", columns="Year", values="Applicants")

# Plot the data
ax = pivot_data.T.plot(kind="line", marker="o")

# Customize the plot
plt.xlabel("Year")
plt.ylabel("Applicants")
plt.title("Applicants by Year and Country")
plt.legend(title="Country", bbox_to_anchor=(1.05, 1), loc="upper left")

# Set the x-axis ticks to display each year
plt.xticks(pivot_data.columns)

plt.setp(ax.get_xticklabels(), rotation=0, fontsize="x-small")

plt.savefig("top5applicantcountries.svg", bbox_inches="tight")

# Show the plot
plt.grid(True)
plt.tight_layout()
plt.show()
