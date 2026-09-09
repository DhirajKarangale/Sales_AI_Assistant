"""
Sales AI Assistant — Query Pipeline Entry Point

Run this script to execute the complete query-response pipeline.
Directly passes a hardcoded salesperson user ID and query into the pipeline.

Usage:
    python run_query.py
"""

import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

# Ensure project root is on the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Query_Pipeline.workflow import run_pipeline


def main():
    # --- Test Queries ---
    TEST_QUERIES = [
        {
            "name": "Roman",
            "salesperson_id": "ec37371f-22f8-4cec-bbd0-74d162bfe67c",
            "query": "I'm prepping for a call with Acme Corp. Can you summarize our last meeting about the CRM Migration and tell me who was on it?"
        },
        {
            "name": "Brock",
            "salesperson_id": "710c8ecf-6340-4edf-a4e9-06513d500a59",
            "query": "What's the current status of the Data Warehouse deal? When was the last time we actually had a touchpoint with them?"
        },
        {
            "name": "Steve",
            "salesperson_id": "f52f2cff-2e14-4da5-9c85-3f8114d0d5d6",
            "query": "Did anyone ever reply to my email regarding the implementation timeline for the ERP Integration?"
        },
        {
            "name": "Kurt",
            "salesperson_id": "09cfdc46-a939-4899-8a40-17cda3f97786",
            "query": "Pull up the latest emails and meeting notes for the Marketing Automation project so I can get up to speed on where we left off."
        },
        {
            "name": "John",
            "salesperson_id": "99ff091f-bf2c-429d-a556-22f59525412f",
            "query": "Can you give me a quick rundown of all the active accounts I am handling right now?"
        }
    ]

    # Select the query to run (0 to 4)
    selected = TEST_QUERIES[0]
    SALESPERSON_ID = selected["salesperson_id"]
    USER_QUERY = selected["query"]

    print("=" * 70)
    print(f"  Salesperson ID : {SALESPERSON_ID}")
    print(f"  Query          : {USER_QUERY}")
    print("=" * 70 + "\n")

    try:
        response = run_pipeline(SALESPERSON_ID, USER_QUERY)

        print("\n" + "=" * 70)
        print("  FINAL RESPONSE")
        print("=" * 70)
        print(response)
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n[FATAL ERROR] Pipeline failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
