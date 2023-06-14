#!/usr/bin/env python
#
# Test whether the distribution of citation numbers is normally distributed
#

import numpy as np
from scipy.stats import shapiro
import sqlite3

conn = sqlite3.connect('oa.db')
c = conn.cursor()
c.execute('SELECT Coalesce(is_referenced_by_count, 0) FROM works')
data = c.fetchall()
conn.close()

# Convert list of tuples to a numpy array
data_array = np.array(data)
stat, p = shapiro(data_array)
print(f"Statistic={stat} p={p}")
