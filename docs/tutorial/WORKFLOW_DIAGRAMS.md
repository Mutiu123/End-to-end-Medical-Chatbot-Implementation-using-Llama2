# Medical Chatbot - Workflow Diagrams

```
+=======================================================================================+
|                     WHAT IS RAG (RETRIEVAL-AUGMENTED GENERATION)?                     |
+=======================================================================================+

    +-------------+                                              +------------------+
    |   MEDICAL   |     The core idea: Instead of relying       |    ACCURATE      |
    |   QUESTION  | --> solely on LLM's training data,      --> |    MEDICAL       |
    |             |     retrieve relevant documents first        |    ANSWER        |
    +-------------+                                              +------------------+

    WHY RAG?
    +------------------+------------------+------------------+------------------+
    |   GROUNDED       |   UP-TO-DATE     |   REDUCED        |   TRACEABLE      |
    |   RESPONSES      |   KNOWLEDGE      |   HALLUCINATION  |   SOURCES        |
    +------------------+------------------+------------------+------------------+
    | Answers based    | Can update       | LLM answers from | Can show which   |
    | on actual docs   | knowledge base   | context, not     | documents were   |
    | not imagination  | without retrain  | random guesses   | used for answer  |
    +------------------+------------------+------------------+------------------+


+=======================================================================================+
|                          COMPLETE CHAT QUERY WORKFLOW                                  |
+=======================================================================================+

    USER                    API GATEWAY               SERVICE LAYER              AI LAYER
      |                          |                          |                        |
      |  POST /api/v1/chat/query |                          |                        |
      |  {query: "What are      |                          |                        |
      |   diabetes symptoms?"}   |                          |                        |
      |------------------------->|                          |                        |
      |                          |                          |                        |
      |                    +-----v-----+                    |                        |
      |                    | Validate  |                    |                        |
      |                    | JWT Token |                    |                        |
      |                    +-----+-----+                    |                        |
      |                          |                          |                        |
      |                    +-----v-----+                    |                        |
      |                    | Check     |                    |                        |
      |                    | Rate Limit|                    |                        |
      |                    +-----+-----+                    |                        |
      |                          |                          |                        |
      |                    +-----v-----+                    |                        |
      |                    | Sanitize  |                    |                        |
      |                    | Input     |                    |                        |
      |                    +-----+-----+                    |                        |
      |                          |                          |                        |
      |                          |  Validated Request       |                        |
      |                          |------------------------->|                        |
      |                          |                          |                        |
      |                          |                    +-----v-----+                  |
      |                          |                    | Generate  |                  |
      |                          |                    | Request ID|                  |
      |                          |                    +-----+-----+                  |
      |                          |                          |                        |
      |                          |                          |  Process Query         |
      |                          |                          |----------------------->|
      |                          |                          |                        |
      |                          |                          |                  +-----v-----+
      |                          |                          |                  | STEP 1:   |
      |                          |                          |                  | Embed     |
      |                          |                          |                  | Query     |
      |                          |                          |                  +-----+-----+
      |                          |                          |                        |
      |                          |                          |                  +-----v-----+
      |                          |                          |                  | STEP 2:   |
      |                          |                          |                  | Vector    |
      |                          |                          |                  | Search    |
      |                          |                          |                  | Pinecone  |
      |                          |                          |                  +-----+-----+
      |                          |                          |                        |
      |                          |                          |                  +-----v-----+
      |                          |                          |                  | STEP 3:   |
      |                          |                          |                  | Build     |
      |                          |                          |                  | Prompt    |
      |                          |                          |                  +-----+-----+
      |                          |                          |                        |
      |                          |                          |                  +-----v-----+
      |                          |                          |                  | STEP 4:   |
      |                          |                          |                  | LLM       |
      |                          |                          |                  | Inference |
      |                          |                          |                  +-----+-----+
      |                          |                          |                        |
      |                          |                          |   Response + Sources   |
      |                          |                          |<-----------------------|
      |                          |                          |                        |
      |                          |                    +-----v-----+                  |
      |                          |                    | Store in  |                  |
      |                          |                    | MongoDB   |                  |
      |                          |                    +-----+-----+                  |
      |                          |                          |                        |
      |                          |                    +-----v-----+                  |
      |                          |                    | Log Audit |                  |
      |                          |                    | Event     |                  |
      |                          |                    +-----+-----+                  |
      |                          |                          |                        |
      |                          |     JSON Response        |                        |
      |                          |<-------------------------|                        |
      |                          |                          |                        |
      |   Response with          |                          |                        |
      |   X-Request-ID header    |                          |                        |
      |<-------------------------|                          |                        |
      |                          |                          |                        |


+=======================================================================================+
|                          RAG PIPELINE - DETAILED FLOW                                  |
+=======================================================================================+

                                INDEXING PHASE (One-time Setup)
    +---------------------------------------------------------------------------+
    |                                                                            |
    |   +-------------+      +-------------+      +-------------+               |
    |   |   PDF       |      |   TEXT      |      |   CHUNK     |               |
    |   |   DOCUMENT  | ---> |   EXTRACT   | ---> |   SPLIT     |               |
    |   | (Medical    |      |   (PyPDF)   |      |   (500 char |               |
    |   |  Book)      |      |             |      |    overlap) |               |
    |   +-------------+      +-------------+      +------+------+               |
    |                                                    |                       |
    |                                                    v                       |
    |   +-------------+      +-------------+      +------+------+               |
    |   |  PINECONE   |      |  VECTOR     |      |  SENTENCE   |               |
    |   |  INDEX      | <--- |  EMBEDDINGS | <--- |  TRANSFORMER|               |
    |   |  "mchatbot" |      |  (384-dim)  |      |  (MiniLM)   |               |
    |   +-------------+      +-------------+      +-------------+               |
    |                                                                            |
    +---------------------------------------------------------------------------+


                                QUERY PHASE (Every Request)
    +---------------------------------------------------------------------------+
    |                                                                            |
    |   "What are the         +-------------+                                   |
    |    symptoms of    --->  |  EMBEDDING  |                                   |
    |    diabetes?"           |  (Same      |                                   |
    |                         |   Model)    |                                   |
    |                         +------+------+                                   |
    |                                |                                          |
    |                                v                                          |
    |                         +------+------+                                   |
    |                         |  SIMILARITY |                                   |
    |                         |  SEARCH     |                                   |
    |                         |  (Pinecone) |                                   |
    |                         |  Top k=2    |                                   |
    |                         +------+------+                                   |
    |                                |                                          |
    |         +----------------------+----------------------+                   |
    |         |                                             |                   |
    |         v                                             v                   |
    |   +-----+-----+                               +-------+-------+           |
    |   | DOC 1     |                               | DOC 2         |           |
    |   | Score:0.92|                               | Score: 0.87   |           |
    |   | "Diabetes |                               | "Common signs |           |
    |   |  symptoms |                               |  include..."  |           |
    |   |  include.."|                              |               |           |
    |   +-----------+                               +---------------+           |
    |         |                                             |                   |
    |         +----------------------+----------------------+                   |
    |                                |                                          |
    |                                v                                          |
    |                    +-----------+-----------+                              |
    |                    |    PROMPT TEMPLATE    |                              |
    |                    +-----------------------+                              |
    |                    | Context: {doc1 + doc2}|                              |
    |                    | Question: {user query}|                              |
    |                    | Instructions: Answer  |                              |
    |                    | only from context     |                              |
    |                    +-----------+-----------+                              |
    |                                |                                          |
    |                                v                                          |
    |                    +-----------+-----------+                              |
    |                    |      LLAMA 2 7B       |                              |
    |                    |    (4-bit quantized)  |                              |
    |                    |    CTransformers      |                              |
    |                    +-----------+-----------+                              |
    |                                |                                          |
    |                                v                                          |
    |                    +-----------+-----------+                              |
    |                    |    GENERATED ANSWER   |                              |
    |                    | "The main symptoms of |                              |
    |                    |  diabetes include..." |                              |
    |                    +-----------------------+                              |
    |                                                                            |
    +---------------------------------------------------------------------------+


+=======================================================================================+
|                          AUTHENTICATION FLOW                                           |
+=======================================================================================+

    REGISTRATION FLOW
    -----------------
    +--------+     +----------+     +-----------+     +----------+     +-----------+
    | Client | --> | Validate | --> | Check     | --> | Hash     | --> | Store in  |
    | POST   |     | Schema   |     | Username/ |     | Password |     | MongoDB   |
    | /auth/ |     | (Pydantic)|    | Email     |     | (bcrypt) |     |           |
    | register|    |          |     | Unique    |     | 12 rounds|     |           |
    +--------+     +----------+     +-----------+     +----------+     +-----+-----+
                                                                             |
                                                                             v
                                                                       +-----+-----+
                                                                       | Return    |
                                                                       | User Info |
                                                                       +-----------+


    LOGIN FLOW
    ----------
    +--------+     +----------+     +-----------+     +----------+     +-----------+
    | Client | --> | Find     | --> | Verify    | --> | Generate | --> | Return    |
    | POST   |     | User in  |     | Password  |     | JWT      |     | Tokens    |
    | /auth/ |     | MongoDB  |     | (bcrypt)  |     | Tokens   |     |           |
    | login  |     |          |     |           |     |          |     |           |
    +--------+     +----------+     +-----------+     +----------+     +-----------+
                                                            |
                                                            v
                                              +-------------+-------------+
                                              |                           |
                                              v                           v
                                       +------+------+            +-------+------+
                                       | Access Token|            | Refresh Token|
                                       | Exp: 30 min |            | Exp: 7 days  |
                                       +-------------+            +--------------+


    TOKEN REFRESH FLOW
    ------------------
    +--------+     +----------+     +-----------+     +----------+
    | Client | --> | Validate | --> | Check     | --> | Generate |
    | POST   |     | Refresh  |     | Token     |     | New      |
    | /auth/ |     | Token    |     | Type      |     | Token    |
    | refresh|     | (JWT)    |     | = refresh |     | Pair     |
    +--------+     +----------+     +-----------+     +----------+


+=======================================================================================+
|                        RATE LIMITING - TOKEN BUCKET ALGORITHM                          |
+=======================================================================================+

    How Token Bucket Works:
    ----------------------

    +------------------+
    |   TOKEN BUCKET   |
    |   Capacity: 20   |     <-- Maximum burst capacity
    |                  |
    |  +------------+  |
    |  | Tokens: 15 |  |     <-- Current available tokens
    |  +------------+  |
    |                  |
    |  Refill Rate:    |
    |  100 tokens/min  |     <-- Sustained rate
    |  (1.67/second)   |
    +------------------+

    Request Handling:
    ----------------

    REQUEST ARRIVES
          |
          v
    +-----+-----+
    | Tokens    |      YES     +-------------+
    | Available?|------------->| Consume 1   |
    | (>= 1)    |              | Token       |
    +-----+-----+              +------+------+
          |                           |
          | NO                        v
          v                    +------+------+
    +-----+-----+              | Process     |
    | Calculate |              | Request     |
    | Wait Time |              +-------------+
    +-----+-----+
          |
          v
    +-----+-----+
    | Return    |
    | 429 Error |
    | Retry-    |
    | After: Xs |
    +-----------+


    Timeline Example:
    ----------------

    Time:   0s      1s      2s      3s      4s      5s
            |       |       |       |       |       |
    Tokens: 20      18      16      17      15      16
            |       |       |       |       |       |
            +-2     +-2     +-0     +-2     +-0     (refill)
            req     req    (idle)   req    (idle)


+=======================================================================================+
|                        MONITORING DATA FLOW                                            |
+=======================================================================================+

    +---------------+     +---------------+     +---------------+     +---------------+
    |  APPLICATION  |     |  PROMETHEUS   |     |   GRAFANA     |     |    ALERTS     |
    +---------------+     +---------------+     +---------------+     +---------------+
           |                     |                     |                     |
           |   /metrics          |                     |                     |
           |   (every 15s)       |                     |                     |
           |<--------------------|                     |                     |
           |                     |                     |                     |
           | Metrics:            |                     |                     |
           | - request_count     |                     |                     |
           | - latency_histogram |                     |                     |
           | - error_rate        |                     |                     |
           | - active_sessions   |                     |                     |
           | - db_connections    |                     |                     |
           |-------------------->|                     |                     |
           |                     |                     |                     |
           |                     |   Query (PromQL)    |                     |
           |                     |<--------------------|                     |
           |                     |                     |                     |
           |                     |   Time Series Data  |                     |
           |                     |-------------------->|                     |
           |                     |                     |                     |
           |                     |                     |   Visualize         |
           |                     |                     |   Dashboards        |
           |                     |                     |                     |
           |                     |   Alert Rule Match  |                     |
           |                     |---------------------|-------------------->|
           |                     |                     |                     |
           |                     |                     |                     | Notify
           |                     |                     |                     | Team
           |                     |                     |                     |


    Metrics Collected:
    -----------------
    +---------------------+---------------------+---------------------+
    |   REQUEST METRICS   |     LLM METRICS     |   SYSTEM METRICS    |
    +---------------------+---------------------+---------------------+
    | requests_total      | llm_inference_time  | db_connections      |
    | request_latency_sec | llm_requests_total  | health_check_status |
    | active_requests     | llm_tokens_total    | rate_limit_hits     |
    | request_size_bytes  | llm_errors_total    | cache_hits          |
    | response_size_bytes | documents_retrieved | cache_misses        |
    +---------------------+---------------------+---------------------+


+=======================================================================================+
|                        CI/CD PIPELINE WORKFLOW                                         |
+=======================================================================================+

    +----------+     +----------+     +----------+     +----------+     +----------+
    |   CODE   |     |   LINT   |     |  TESTS   |     |  BUILD   |     |  DEPLOY  |
    |   PUSH   | --> |   CHECK  | --> |          | --> |  DOCKER  | --> |          |
    +----------+     +----------+     +----------+     +----------+     +----------+
         |               |                |                |                |
         |               |                |                |                |
         v               v                v                v                v
    +---------+     +---------+     +---------+     +---------+     +---------+
    | GitHub  |     | Black   |     | Pytest  |     | Build   |     | Push to |
    | Actions |     | isort   |     | 25+     |     | Multi-  |     | GHCR    |
    | Trigger |     | Flake8  |     | Tests   |     | stage   |     |         |
    |         |     | MyPy    |     | 80%+    |     | Image   |     | Deploy  |
    |         |     | Pylint  |     | Coverage|     |         |     | to K8s  |
    +---------+     +---------+     +---------+     +---------+     +---------+
                         |                |                |
                         v                v                v
                    +---------+     +---------+     +---------+
                    | Bandit  |     | Trivy   |     | Sign    |
                    | Security|     | Scan    |     | Image   |
                    | Check   |     | CVEs    |     |         |
                    +---------+     +---------+     +---------+


    Branch Strategy:
    ---------------
    +-------------+     +-------------+     +-------------+
    |   feature/  | --> |   develop   | --> |    main     |
    |   branches  |     |   (staging) |     | (production)|
    +-------------+     +-------------+     +-------------+
          |                   |                   |
          |    PR + Review    |    PR + Review    |
          +------------------>+------------------>|
                              |                   |
                         Auto Deploy         Auto Deploy
                         to Staging         to Production


+=======================================================================================+
|                        ERROR HANDLING FLOW                                             |
+=======================================================================================+

    +-------------+
    |   REQUEST   |
    +------+------+
           |
           v
    +------+------+
    |  Middleware |
    |  Exception  |
    |  Handler    |
    +------+------+
           |
           +------------------+------------------+------------------+
           |                  |                  |                  |
           v                  v                  v                  v
    +------+------+    +------+------+    +------+------+    +------+------+
    | Validation  |    | Auth        |    | Rate Limit  |    | Business    |
    | Error       |    | Error       |    | Error       |    | Logic Error |
    | (422)       |    | (401/403)   |    | (429)       |    | (500/503)   |
    +------+------+    +------+------+    +------+------+    +------+------+
           |                  |                  |                  |
           +------------------+------------------+------------------+
                              |
                              v
                    +---------+---------+
                    |  Structured JSON  |
                    |  Error Response   |
                    +-------------------+
                    | {                 |
                    |   "error": {      |
                    |     "code": "...",|
                    |     "message":"..",|
                    |     "details": {} |
                    |   },              |
                    |   "request_id":"."|
                    | }                 |
                    +-------------------+

```

## Summary

| Workflow | Components | Key Technologies |
|----------|------------|------------------|
| Chat Query | Validation -> RAG -> Response | FastAPI, LangChain, Llama 2 |
| RAG Pipeline | Embed -> Search -> Generate | Sentence Transformers, Pinecone |
| Authentication | Register -> Login -> Refresh | JWT, bcrypt, MongoDB |
| Rate Limiting | Token Bucket Algorithm | In-memory storage |
| Monitoring | Collect -> Store -> Visualize | Prometheus, Grafana |
| CI/CD | Lint -> Test -> Build -> Deploy | GitHub Actions, Docker, K8s |
