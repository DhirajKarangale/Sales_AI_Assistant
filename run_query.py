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
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Query_Pipeline.workflow import run_pipeline


def main():
    # --- Hardcoded test inputs ---
    # Kurt's salesperson ID (from salespersons table sample data)
    SALESPERSON_ID = "ec37371f-22f8-4cec-bbd0-74d162bfe67c"

    # Example query combining multiple sub-questions
    USER_QUERY = "What's the latest update on the AI Analytics Platform and which meetings happened last week?"

    print("\n" + "=" * 70)
    print("  SALES AI ASSISTANT — Query Pipeline Test")
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
