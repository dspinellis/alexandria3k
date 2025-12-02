#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2023-2024  Dibyendu Gupta
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
""""This process is used to distinguish the affiliations mentioned in the crossref dataset."""
import sys
import time

import Levenshtein
import openai
import apsw
from openai import OpenAI
from alexandria3k.common import (
    ensure_table_exists,
    log_sql,
    set_fast_writing,
)
from alexandria3k import perf
from alexandria3k.db_schema import ColumnMeta, TableMeta

tables = [
    TableMeta(
        "distinct_affiliations",
        columns=[
            ColumnMeta("id"),
            ColumnMeta("mentioned_name"),
            ColumnMeta("gpt_name"),
            ColumnMeta("city"),
            ColumnMeta("ror_id"),
        ],
    ),
]

GPT_PROMPT = """From the given textual piece, identify ONLY the university/research organization and
              city mentioned. The response should be (organization, city). DO NOT produce any
              other textual information. Ignore all other information mentioned in the textual
              piece. If organization or city is not recognized, then return ( , )"""
GPT_MODEL = "gpt-4-1106-preview"


def process(database_path):
    """
    Distinguishes the affiliations mentioned in the crossref dataset. It uses the GPT-4 model to
    extract the affiliation and city from the affiliation text and match it to the ROR database
    based on Levenshtein distance.

    The distinguished affiliations is used by link_aa_llm.py to link authors to their lowest-level
    research organization.

    :param database_path: The path to the database
    """
    database = apsw.Connection(database_path)
    client = OpenAI()
    database.execute(log_sql("DROP TABLE IF EXISTS distinct_affiliations"))
    database.execute(log_sql(tables[0].table_schema()))
    set_fast_writing(database)
    ensure_table_exists(database, "distinct_affiliations")
    ensure_table_exists(database, "research_organizations")

    affiliation_select_cursor = database.cursor()
    ror_cursor = database.cursor()
    affiliation_insert_cursor = database.cursor()

    distinct_affiliations_number = 0
    time_start = time.time()
    # Iterate over all the affiliations mentioned in crossref
    for mentioned_name in affiliation_select_cursor.execute(
        """
        SELECT DISTINCT name FROM distinct_affiliations
        """
    ):
        affiliation_name = mentioned_name[0]
        if not mentioned_name:
            continue
        # Prompt for the GPT-4 model to extract the affiliation and city from the affiliation text
        prompt = GPT_PROMPT + str(mentioned_name)

        completion = query_response(client, prompt)

        gpt_city, gpt_org = format_result(completion)

        best_ror_id = find_best_ror(gpt_org, ror_cursor)
        # Insert the best affiliation match into the distinct_affiliations table (if found)
        if best_ror_id != -1:
            affiliation_insert_cursor.execute(
                "INSERT INTO distinct_affiliations VALUES (?, ?, ?, ?, ?)",
                (
                    distinct_affiliations_number,
                    affiliation_name,
                    gpt_org,
                    gpt_city,
                    best_ror_id,
                ),
            )
        distinct_affiliations_number += 1

    affiliation_select_cursor.close()
    ror_cursor.close()
    affiliation_insert_cursor.close()
    print(f"llm_process_valid_authors took {time.time() - time_start} seconds")
    perf.log(
        f"link_aa_llm added {distinct_affiliations_number} distinct affiliations"
    )


def find_best_ror(gpt_org, ror_cursor):
    """
    Finds the best affiliation match based on levenshtein distance.

    :param gpt_org: The organization name extracted from the GPT-4 model
    :param ror_cursor: The cursor to execute the query
    """
    # Calculate the Levenshtein distance btw gpt_org and ror_org and choose the best match
    # (narrow the search by only comparing organizations from the same city)
    best_ror_id = -1
    best_length = sys.maxsize
    for ror_id, ror_org in ror_cursor.execute(
        """
                    SELECT id, name FROM research_organizations
                    """,
    ):
        if not ror_org:
            continue
        if Levenshtein.distance(gpt_org, ror_org) < best_length:
            best_length = Levenshtein.distance(gpt_org, ror_org)
            best_ror_id = ror_id
    return best_ror_id


def format_result(completion):
    """
    Formats the result of the query response to remove brackets.

    :param completion: The response from the GPT-4 model
    """
    # only extract the "content" field of the response, we only consider the first affiliation
    response = str(completion.choices[0].message.content)
    response_split = response.split(",")
    gpt_org = response_split[0].replace("(", "")
    gpt_city = ""
    if len(response_split) > 1:
        gpt_city = response_split[1].replace(")", "")
    return gpt_city, gpt_org


def query_response(client, prompt):
    """
    Queries the GPT-4 model to extract the affiliation and city from the affiliation text. It
    loops and resets the API if the rate limit is exceeded.

    The querying of the prompt is done through the OpenAI API. The limit of number and amount of
    queries depends on the users plan. This could affect the time taken to run the process. Often
    the API might need to reset due to rate limiting. It is expensive to run the process multiple
    times, so we wait for the reset and continue the process.

    :param client: The OpenAI client
    :param prompt: The prompt to query the GPT-4 model
    """
    try:
        # Extract the affiliation and city from the provided textual affiliation
        completion = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        return completion
    except openai.RateLimitError:
        # if the error is due to rate limiting, wait for 60 seconds
        print("Rate limit exceeded. Waiting for reset...")
        time.sleep(60)
        return query_response(client, prompt)  # Retry the request
    except openai.OpenAIError as e:
        print(e)
        return e
