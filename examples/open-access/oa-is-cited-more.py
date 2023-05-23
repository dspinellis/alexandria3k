#!/usr/bin/env python
#
# Test whether citations to OA papers are higher than those to non-OA ones
#

import numpy as np
from scipy.stats import mannwhitneyu
from cliffs_delta import cliffs_delta
import sqlite3

def describe(title, a):
    print(f"{title} count: {len(a)} mean: {np.mean(a)} median: {np.median(a)} max: {np.max(a)} SD: {np.std(a)}")


def cohen_d(group1, group2):
    diff = np.mean(group1) - np.mean(group2)
    n1, n2 = len(group1), len(group2)
    var1 = np.var(group1)
    var2 = np.var(group2)
    pooled_var = (n1 * var1 + n2 * var2) / (n1 + n2)
    d = diff / np.sqrt(pooled_var)
    return d

conn = sqlite3.connect('oa.db')
c = conn.cursor()
c.execute("ATTACH 'rolap.db' AS rolap");

c.execute(f"""
  SELECT Coalesce(is_referenced_by_count, 0) FROM works
  INNER JOIN rolap.oa_works ON works.id = oa_works.work_id
  WHERE published_year >= 2011
""")
oa_references = c.fetchall()
describe(f"References to OA", oa_references)

c.execute(f"""
  SELECT Coalesce(is_referenced_by_count, 0) FROM works
  LEFT JOIN rolap.oa_works ON works.id = oa_works.work_id
  WHERE oa_works.work_id is null AND published_year >= 2011
""")
non_oa_references = c.fetchall()
describe(f"References to non-OA", non_oa_references)

# Do not use this, because the data are not normally distributed
# res = mannwhitneyu(oa_references, non_oa_references, alternative='greater')
# print(f"Mann-Whitney U rank test: {res}")

d, res = cliffs_delta(oa_references, non_oa_references)
print(f"Cliff's Delta: {d=} {res=}")

d = cohen_d(oa_references, non_oa_references)
print(f"Cohen's d: {d}")

conn.close()
