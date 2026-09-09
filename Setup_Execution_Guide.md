# Sales AI Assistant — Setup & Execution Guide

## 1. LLM Setup: HuggingFace vs. Ollama
You must first choose an LLM provider and configure your `.env` file (`e:\FullStack\Sales_AI_Assistant\.env`). 

**Option A: HuggingFace (Cloud)**
Set the provider and add your API tokens (comma-separated for rate-limit failover).
```env
LLM_PROVIDER=huggingface
HF_TOKENS="hf_xxxx1, hf_xxxx2"
```

**Option B: Ollama (Local)**
1. Install [Ollama](https://ollama.com/) on your machine.
2. Pull the required model via terminal: `ollama pull deepseek-r1:8b`
3. Set the provider in your `.env`:
```env
LLM_PROVIDER=ollama
```

**Complete your `.env` file** by adding the remaining database configurations:
```env
EXPONENTIAL_BACKOFF_MAX_RETRIES=3
EXPONENTIAL_BACKOFF_BASE_TIME=2

DB_HOST=ep-sparkling-dream-a1qpient-pooler.ap-southeast-1.aws.neon.tech
DB_NAME=neondb
DB_USER=neondb_owner
DB_PASSWORD=your_db_password
DB_PORT=5432
```

---

## 2. Core Concept: Generation vs. Querying
It is important to understand that **Knowledge Base Generation** and **Running the Query Pipeline** are completely different things:

1. **Knowledge Base Generation (Creating the Data):** This parses raw datasets into searchable bases. **These are already generated** and present in the `Knowledge_Bases/` directory. 
   * *You do not need to run this to use the assistant.* However, if you update the raw data and need to generate them again, you can check with these commands:
     ```bash
     python Knowledge_Base_Generation/Business_Knowledge_Generation/main.py
     python Knowledge_Base_Generation/Database_Knowledge_Generation/main.py
     ```
2. **Query Pipeline (Getting Answers):** This is the actual engine that takes a user query, searches the generated knowledge bases, and returns a response. 

---

## 3. Running the Query Pipeline
To get a response to a user query, simply run the pipeline:
```bash
python Query_Pipeline/main.py
```

**Testing Different Salespersons:**
Test queries are pre-configured inside `Query_Pipeline/main.py`. You can switch between different user profiles (Roman, Brock, Steve, Kurt, or John) by changing the index on **line 47**:
```python
# Select 0 for Roman, 1 for Brock, 2 for Steve, etc.
selected = TEST_QUERIES[0] 
```

---

## 4. Data & Schema Reference
If you need to inspect how the raw data or databases are structured:
* **PostgreSQL Schemas:** See `datasets/schema.txt` (includes `salespersons`, `projects`, `events`, etc.)
* **Raw JSON Data:** Check the `datasets/` folder for calendars, emails, and meeting notes.
