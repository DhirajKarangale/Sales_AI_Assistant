# Sales AI Assistant — System Design & Architecture Specification

This document provides the complete, structured architectural design for the Sales AI Assistant, consolidating and refining the specifications outlined in the project requirements.

---

## 1. System Overview & Problem Statement

### 1.1 Objective
The system is an AI assistant for salespersons who manage specific customers and end-to-end deals. The assistant answers natural language questions using business data while enforcing data isolation so that each salesperson can only access information related to their assigned customers, projects, and deals.

### 1.2 Example Salesperson Queries
* *"I'm prepping for a call with Acme Corp. Can you summarize our last meeting about the CRM Migration and tell me who was on it?"*
* *"What's the current status of the Data Warehouse deal? When was the last time we actually had a touchpoint with them?"*
* *"Did anyone ever reply to my email regarding the implementation timeline for the ERP Integration?"*
* *"Pull up the latest emails and meeting notes for the Marketing Automation project so I can get up to speed on where we left off."*
* *"Can you give me a quick rundown of all the active accounts I am handling right now?"*

### 1.3 Core Division
The system is divided into two decoupled subsystems:
1. **Data Storage & Knowledge Base Pipeline**: Asynchronously ingests raw communication data and maintains structured databases, Open Knowledge Framework (OKF) LLM wikis, and a knowledge graph.
2. **User Query & Response Pipeline**: Optimizes rep queries, verifies data access permissions, retrieves data via a Multi-Agent Database Agent and Knowledge Graph/Wikis, and generates grounded responses.

---

## 2. Architecture Diagram

```
========================================================================================
PART 1: DATA INGESTION & KNOWLEDGE BASE PIPELINE
========================================================================================

 [Outlook: Emails & Calendar]    [Teams: Meeting Transcripts]
               │                              │
               └──────────────┬───────────────┘
                              ▼
                [1. Webhook Ingestion Worker]
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
       [SQL Database]                 [Redis Stream]
   (Raw meetings, users,                     │
     email/transcript links)                 ▼
                              [2. Data Extraction Agent]
                                 - Python Text Cleaning
                                 - Normalization & Entity Extraction
                                             │
                                             ▼
                                     [NoSQL Database]
                               (Structured cleaned events)
                                             │
                                             ▼
                              [3. Wiki Generation Service]
                                 - Change Data Polling / Listener
                                 - LLM Wikis with OKF (.md)
                                 - Knowledge Graph Updates
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
             [LLM Wikis (OKF .md)]                         [Knowledge Graph]
        (Customer, Project, Rep Wikis)                  (Entity & Relationship Graph)

 [Database Schema (One-Time / Migration)]
               │
               ▼
   [DB Schema Wikis & Graph]
   - Root Wiki
   - Table Wikis (Cols, Keys, Samples)
   - Schema Relation Graph (up to 4 hops)


========================================================================================
PART 2: USER QUERY & RESPONSE PIPELINE
========================================================================================

                    [Salesperson User Query + UserID]
                                   │
                                   ▼
                       [1. Local Text Cleanup]
                     (Lowercase, strip spaces/chars)
                                   │
                                   ▼
                    [2. Redis Cache Lookup]
                     (Key: userid + cleaned_query)
                                   │
                 ┌─────────────────┴─────────────────┐
                 ▼ (Cache Hit)                       ▼ (Cache Miss)
          [Return Cached Response]           [Push Job to Redis Stream]
                                                     │
                                                     ▼
                                          [3. Query Optimizer Worker]
                                             - Fetch rep projects/status/role from SQL
                                             - LLM clean: fix dates, SI/global units
                                             - Extract & sequence ordered questions
                                                     │
                                                     ▼
                                          [4. Protection / Access Check]
                                             - Verify salesperson scope against data
                                                     │
                                                     ▼
                                          [5. DB Dependency Detection]
                                             - Check if question requires SQL DB
                                                     │
                             ┌───────────────────────┴───────────────────────┐
                             ▼ (needs_db = true)                             ▼ (needs_db = false)
                      [6. DB Agent]                                          │
                   - Navigator (Tables)                                      │
                   - Planner (Join Path)                                     │
                   - Writer (SQL Query)                                      │
                   - Validator (Read-only check, execute)                    │
                             │                                               │
                             └───────────────────────┬───────────────────────┘
                                                     ▼
                                         [7. Response Generator]
                                            - Context Graph (depth & breadth)
                                            - Select relevant wikis
                                            - Synthesize answers
                                                     │
                                                     ▼
                                         [8. Cache in Redis (TTL: 5m)]
                                                     │
                                                     ▼
                                              [Return Response]
```

---

## 3. Part 1: Data Storage & Knowledge Base Pipeline

### 3.1 Data Sources
* **Outlook**: Incoming and outgoing emails, calendar events.
* **Microsoft Teams**: Meeting transcripts and recordings metadata.
* Delivered via webhooks to the ingestion service.

---

### 3.2 Storage Layers

#### A. Raw SQL Database
Stores the baseline relational entities:
* Meeting metadata (timestamps, scheduled time, duration, status: scheduled/happened/canceled).
* User records and salesperson assignments.
* Direct resource links (transcript storage URLs, email thread IDs/links).

#### B. Redis Stream
* Acts as the ingestion message queue.
* The ingestion worker collects raw webhook payloads and enqueues them for asynchronous extraction.

#### C. Data Extraction & Cleaning Agent
Pulls raw items from the Redis Stream and processes them in two stages:

1. **Python Rule-Based Text Cleaning**:
   * Whitespace and empty line reduction.
   * Transcripts: Strip timestamps, line numbers, and caption formatting.
   * Emails: Remove email signatures, disclaimer text, headers, and quote chains.
   * Calendar events: Strip extraneous platform metadata.

2. **Semantic Standardization & Structuring**:
   * Noise Removal & Semantic Normalization.
   * Vocabulary Standardization & Canonicalization (standard naming for customers and projects).
   * Ambiguity Reduction & Context Preservation.
   * Output format:
     * **Event Type**: `email`, `calendar_event`, or `meeting`
     * **Participants**: List of attendee/sender/recipient names and emails
     * **Customer**: Identified customer organization
     * **Projects**: Associated project/deal names
     * **Salesperson Involved**: Sales representative handling the event
     * **Summary**: Concise description of what occurred
     * **Clean Data**: Cleaned body of the transcript or email

#### D. NoSQL Database
Stores the structured, cleaned event documents output by the Data Extraction Agent.

---

### 3.3 Wiki Generation Service & Knowledge Graph

A dedicated service continuously monitors the NoSQL database for new or modified records, then updates both the LLM Wikis and the Knowledge Graph.

#### A. LLM Wikis (Open Knowledge Framework - OKF)
Structured Markdown files capturing living business context:
* **Customer Wikis**: Customer background, assigned salesperson, and overall status.
* **Project Wikis**:
  * Assigned salesperson and customer stakeholders.
  * Current project status (ongoing, completed, canceled) and active stage.
  * Meeting history: all meetings scheduled, completed, and canceled, with what happened in each meeting.
  * Email history: summarized thread topics, pending responses, and decisions.
  * Latest touchpoint timestamps and audit trail (`created_at`, `updated_at`).

#### B. Knowledge Graph
Maintains an interconnected entity network:
* **Entities**: `Salesperson`, `Customer`, `Project`, `Customer Contact`, `Meeting`, `Email`.
* **Relationships**:
  * Which salesperson handles which project and customer.
  * How projects relate to customers and customer contacts.
  * Meeting and email linkages to projects and participants.
* **Synchronization**: Updated immediately after the corresponding wikis are updated to reflect the latest status, touchpoints, and connections.

---

### 3.4 Database Schema Knowledge Base (One-Time / On Schema Update)

A pre-computed knowledge base describing the SQL database to enable safe Text-to-SQL generation.

1. **Root Schema Wiki**:
   * Global table inventory.
   * High-level business purpose and functional overview of what each table stores.
2. **Per-Table Wikis**:
   * Table name and detailed business description.
   * Column definitions: column name, data type, business purpose, and impact on the record.
   * Primary key specifications.
   * Foreign keys and detailed relationship descriptions.
   * Representative data samples: up to 5 sample values per column.
3. **Database Relationship Graph**:
   * Graph representation mapping how tables connect through foreign keys.
   * Explicitly documents multi-hop join paths up to **4 hops** deep.

---

## 4. Part 2: User Query & Response Pipeline

### 4.1 Ingestion, Local Cleaning & Caching
1. System receives `salesperson_user_id` and raw natural language `query`.
2. **Local String Normalization**:
   * Convert text to lowercase.
   * Strip redundant whitespace, punctuation, and special characters.
3. **Cache Check**:
   * Construct cache key: `userid + cleaned_query`.
   * Check key in Redis cache.
   * **If present (Hit)**: Immediately return cached response.
   * **If absent (Miss)**: Wrap `(userid, query)` into a job and push to the query Redis Stream.

---

### 4.2 Query Optimizer Worker
Consumes jobs from the Redis Stream and prepares the query for execution:

1. **Salesperson Context Hydration**:
   * Queries SQL DB to load the salesperson’s active portfolio: assigned projects, project statuses (`ongoing`, `completed`, `canceled`), and assigned customer accounts.
2. **LLM Query Cleanup & Normalization**:
   * Eliminates filler words and colloquialisms.
   * Normalizes counts, currencies (converts to standard currency), and units (weights to pounds, lengths to meters, speeds to m/s, or SI standard units).
   * **Date & Time Calculation**: Resolves relative dates to explicit calendar ranges using the current system date (e.g., *"deals closed last week"* $\rightarrow$ *"deals closed by salesperson from 1 Sept 2026 to 7 Sept 2026"*).
3. **Question Extraction & Decomposition**:
   * Splits multi-part questions into an ordered sequence of discrete sub-questions where sequence is preserved.
   * *Example*: *"What happened in the last meeting, and why did the deal fail?"*
     * `Sub-Question 1`: *"What happened in the last meeting?"*
     * `Sub-Question 2`: *"Why did the deal fail?"*
4. **Job Payload Object**:
   * Produces an internal state object holding `salesperson_id`, context metadata, and the ordered question list.

---

### 4.3 Protection (Access Control Check)
1. For each extracted sub-question, inspect the target entities against the salesperson's authorized portfolio retrieved from the DB.
2. Verification Rule: A salesperson is **only allowed** to access data, projects, and customer information assigned to them.
3. If an unauthorized entity is targeted, the question is flagged as restricted/forbidden and filtered out of data retrieval.

---

### 4.4 Database Dependency Detection
1. Iterates through each authorized sub-question to determine whether it requires data from the SQL database.
   * *Example*: Questions asking for meeting dates, deal amounts, lists of closed deals, or aggregations return `needs_db = true`.
   * *Example*: Questions asking for meeting discussion content, sentiment, or email details return `needs_db = false`.
2. Updates each question in the object with a boolean `needs_db` flag.

---

### 4.5 DB Agent (Multi-Agent Text-to-SQL)
Triggered for any sub-question where `needs_db == true`. The DB Agent uses the Schema Wikis and Schema Relationship Graph:

```
[User Sub-Question]
         │
         ▼
 1. [Navigator] ──► Reads Root Schema Wiki ──► Selects Target Tables + Relational Neighbors
         │
         ▼
  2. [Planner]  ──► Plans join strategy (up to 4 hops, prevents circular loops)
         │
         ▼
  3. [Writer]   ──► Writes valid SQL query
         │
         ▼
 4. [Validator] ──► Python check:
                     - Read-only enforcement (no UPDATE, INSERT, DELETE, TRUNCATE, DROP)
                     - Query syntax & execution validation
                     │
         ┌───────────┴───────────┐
         ▼ (Invalid)             ▼ (Valid)
   [Feedback to Planner]    [Execute SQL & Return Data]
```

1. **Navigator**: Takes the user query and root schema wiki; identifies which primary tables are relevant and expands to their related tables using unique sets to prevent circular loops.
2. **Planner**: Evaluates the candidate tables and relationship graph up to 4 hops to construct the join plan and filtering criteria.
3. **Writer**: Translates the plan into an executable SQL query.
4. **Validator**:
   * Programmatic Python gatekeeper: strictly enforces that the query is read-only.
   * Blocks any `UPDATE`, `INSERT`, `DELETE`, `TRUNCATE`, or `DROP` statements.
   * Validates query syntax; if an error occurs, feeds the error back to the Planner for correction.
   * Executes the verified query on the SQL database and attaches the resulting data to the question object.

---

### 4.6 Response Generator
1. **Context Assembly**:
   * Gathers all inputs: user query, decomposed sub-questions, SQL query outputs, and salesperson context.
2. **Graph & Wiki Retrieval**:
   * Uses the query and known entities to construct a relevant **context graph** from the Knowledge Graph using a specified depth and breadth.
   * Uses the context graph to select the corresponding relevant OKF Markdown wikis (customer overviews, project meeting notes, email summaries).
3. **Answer Generation**:
   * Answers each sub-question sequentially using the combined database results, wiki notes, and knowledge graph relationships.
4. **Caching & Delivery**:
   * Stores the final answer in Redis with a **5-minute TTL** under the key `userid + cleaned_query`.
   * Returns the final response to the user.

---

## 5. Summary of Data Structures & State Objects

### 5.1 Cleaned Event Document (NoSQL)
```json
{
  "event_id": "evt_109283",
  "source": "meeting",
  "timestamp": "2026-09-02T14:30:00Z",
  "customer": "Acme Corp",
  "projects": ["CRM Migration"],
  "salesperson": "Brock",
  "participants": [
    {"name": "Brock", "role": "Salesperson"},
    {"name": "John Doe", "role": "Customer VP Eng"}
  ],
  "summary": "Reviewed CRM migration architecture and discussed API rate limits.",
  "clean_data": "Full sanitized transcript text without timestamps or formatting noise..."
}
```

### 5.2 Query Pipeline State Object
```json
{
  "salesperson_id": "sp_brock_01",
  "raw_query": "What happened in the last meeting, and why did the deal fail?",
  "cleaned_query": "what happened in the last meeting and why did the deal fail",
  "salesperson_context": {
    "assigned_projects": ["CRM Migration", "Marketing Automation"],
    "assigned_customers": ["Acme Corp", "Wayne Enterprises"],
    "role": "Senior Account Executive"
  },
  "questions": [
    {
      "index": 1,
      "text": "What happened in the last meeting for CRM Migration?",
      "allowed": true,
      "needs_db": true,
      "db_result": [
        {"meeting_id": "m_991", "date": "2026-09-02", "status": "completed"}
      ]
    },
    {
      "index": 2,
      "text": "Why did the deal fail for CRM Migration?",
      "allowed": true,
      "needs_db": false,
      "db_result": null
    }
  ],
  "final_response": "In the last meeting on September 2, 2026, the team reviewed the technical architecture..."
}
```
