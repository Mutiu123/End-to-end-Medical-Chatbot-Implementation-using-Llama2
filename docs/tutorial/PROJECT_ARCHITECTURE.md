# Medical Chatbot - Project Architecture

```
+=======================================================================================+
|                     MEDICAL CHATBOT API - SYSTEM ARCHITECTURE                         |
|                              Production-Ready Design                                   |
+=======================================================================================+

                                    +-----------------+
                                    |    CLIENTS      |
                                    +-----------------+
                                    | * Web Browser   |
                                    | * Mobile App    |
                                    | * API Consumers |
                                    | * CLI Tools     |
                                    +--------+--------+
                                             |
                                             | HTTPS/TLS
                                             v
+-------------------------------------------------------------------------------------------+
|                               INGRESS / LOAD BALANCER                                     |
|  +---------------------------------------------------------------------------------+      |
|  |  * SSL Termination    * Rate Limiting (nginx)    * Request Routing              |      |
|  |  * DDoS Protection    * Health Checks            * Load Distribution            |      |
|  +---------------------------------------------------------------------------------+      |
+-------------------------------------------------------------------------------------------+
                                             |
                                             v
+-------------------------------------------------------------------------------------------+
|                                  API GATEWAY LAYER                                        |
|  +----------------------------------+  +------------------------------------------+       |
|  |     SECURITY MIDDLEWARE          |  |        REQUEST PROCESSING                |       |
|  |  +----------------------------+  |  |  +------------------------------------+  |       |
|  |  | * JWT Authentication       |  |  |  | * Request ID Generation            |  |       |
|  |  | * Token Bucket Rate Limit  |  |  |  | * Request/Response Logging         |  |       |
|  |  | * CORS Validation          |  |  |  | * Performance Timing               |  |       |
|  |  | * Input Sanitization       |  |  |  | * Error Handling                   |  |       |
|  |  | * Security Headers         |  |  |  | * Content-Type Validation          |  |       |
|  |  +----------------------------+  |  |  +------------------------------------+  |       |
|  +----------------------------------+  +------------------------------------------+       |
+-------------------------------------------------------------------------------------------+
                                             |
                                             v
+-------------------------------------------------------------------------------------------+
|                               FASTAPI APPLICATION LAYER                                   |
|                                                                                           |
|  +------------------+  +------------------+  +------------------+  +------------------+   |
|  |   AUTH ROUTES    |  |   CHAT ROUTES    |  |  HEALTH ROUTES   |  | METRICS ROUTES   |   |
|  +------------------+  +------------------+  +------------------+  +------------------+   |
|  | POST /register   |  | POST /query      |  | GET /live        |  | GET /metrics     |   |
|  | POST /login      |  | GET /history     |  | GET /ready       |  | (Prometheus)     |   |
|  | POST /refresh    |  | DELETE /history  |  | GET /health      |  |                  |   |
|  | GET /me          |  |                  |  |                  |  |                  |   |
|  | POST /logout     |  |                  |  |                  |  |                  |   |
|  +------------------+  +------------------+  +------------------+  +------------------+   |
|                                             |                                             |
|  +---------------------------------------------------------------------------------+      |
|  |                         PYDANTIC V2 VALIDATION LAYER                            |      |
|  |  * Request Schema Validation     * Response Serialization                       |      |
|  |  * Type Coercion                 * Custom Validators                            |      |
|  +---------------------------------------------------------------------------------+      |
+-------------------------------------------------------------------------------------------+
                                             |
                        +--------------------+--------------------+
                        |                    |                    |
                        v                    v                    v
+-------------------------------------------------------------------------------------------+
|                                  SERVICE LAYER                                            |
|                                                                                           |
|  +------------------------+  +------------------------+  +------------------------+      |
|  |    CHATBOT SERVICE     |  |     AUTH SERVICE       |  |    AUDIT SERVICE       |      |
|  +------------------------+  +------------------------+  +------------------------+      |
|  | * Query Processing     |  | * User Registration    |  | * Event Logging        |      |
|  | * RAG Pipeline         |  | * Password Hashing     |  | * Access Tracking      |      |
|  | * Context Retrieval    |  | * Token Generation     |  | * Prediction Logging   |      |
|  | * Response Generation  |  | * Token Validation     |  | * Security Events      |      |
|  | * Source Attribution   |  | * Session Management   |  |                        |      |
|  +------------------------+  +------------------------+  +------------------------+      |
+-------------------------------------------------------------------------------------------+
                                             |
                        +--------------------+--------------------+
                        |                                         |
                        v                                         v
+---------------------------------------+  +--------------------------------------------+
|          LLM / AI LAYER               |  |           DATA PERSISTENCE LAYER           |
|                                       |  |                                            |
|  +--------------------------------+   |  |  +----------------+  +------------------+  |
|  |     LANGCHAIN ORCHESTRATION    |   |  |  |   MONGODB      |  |    PINECONE      |  |
|  +--------------------------------+   |  |  +----------------+  +------------------+  |
|  |                                |   |  |  | * Users        |  | * Vector Index   |  |
|  |  +----------+  +------------+  |   |  |  | * Sessions     |  | * Embeddings     |  |
|  |  | RETRIEVER|  | QA CHAIN   |  |   |  |  | * Audit Logs   |  | * Similarity     |  |
|  |  | (k=2)    |  | (stuff)    |  |   |  |  | * Chats        |  |   Search         |  |
|  |  +----------+  +------------+  |   |  |  +----------------+  +------------------+  |
|  |       |              |         |   |  |        |                     |            |
|  |       v              v         |   |  |        |    Connection       |            |
|  |  +----------+  +------------+  |   |  |        |    Pooling          |            |
|  |  | PINECONE |  | LLAMA 2    |  |   |  |        |    (10-50)          |            |
|  |  | VECTOR   |  | 7B-CHAT    |  |   |  |        v                     |            |
|  |  | STORE    |  | (4-bit)    |  |   |  |  +----------------+          |            |
|  |  +----------+  +------------+  |   |  |  | Motor Async    |          |            |
|  |       ^              ^         |   |  |  | Driver         |          |            |
|  |       |              |         |   |  |  +----------------+          |            |
|  |  +----------+  +------------+  |   |  |                              |            |
|  |  | SENTENCE |  | PROMPT     |  |   |  +------------------------------+            |
|  |  | TRANS-   |  | TEMPLATE   |  |   |                                              |
|  |  | FORMERS  |  |            |  |   +----------------------------------------------+
|  |  | (MiniLM) |  |            |  |
|  |  +----------+  +------------+  |
|  +--------------------------------+
+---------------------------------------+


+=======================================================================================+
|                           MONITORING & OBSERVABILITY STACK                            |
+=======================================================================================+

+-------------------------------------------------------------------------------------------+
|                                                                                           |
|  +------------------------+  +------------------------+  +------------------------+      |
|  |      PROMETHEUS        |  |        GRAFANA         |  |     STRUCTURED LOGS    |      |
|  +------------------------+  +------------------------+  +------------------------+      |
|  | METRICS COLLECTED:     |  | DASHBOARDS:            |  | LOG TYPES:             |      |
|  | * requests_total       |  | * API Performance      |  | * JSON Formatted       |      |
|  | * request_latency      |  | * LLM Inference        |  | * Request ID Tracking  |      |
|  | * llm_inference_time   |  | * Database Health      |  | * Audit Events         |      |
|  | * db_connections       |  | * Error Rates          |  | * Error Traces         |      |
|  | * rate_limit_hits      |  | * Business Metrics     |  | * Performance Data     |      |
|  | * chat_queries_total   |  |                        |  |                        |      |
|  | * auth_attempts        |  | ALERTS:                |  | DESTINATIONS:          |      |
|  | * active_sessions      |  | * High Error Rate      |  | * stdout (container)   |      |
|  | * health_check_status  |  | * High Latency         |  | * File (optional)      |      |
|  | * cache_hits/misses    |  | * Service Down         |  | * Log Aggregator       |      |
|  +------------------------+  +------------------------+  +------------------------+      |
|                                                                                           |
+-------------------------------------------------------------------------------------------+


+=======================================================================================+
|                              DEPLOYMENT ARCHITECTURE                                   |
+=======================================================================================+

+-------------------------------------------------------------------------------------------+
|                              KUBERNETES CLUSTER (EKS/GKE/AKS)                            |
|                                                                                           |
|  +-----------------------------------------------------------------------------------+   |
|  |                            NAMESPACE: medical-chatbot                              |   |
|  |                                                                                    |   |
|  |  +------------------+  +------------------+  +------------------+                  |   |
|  |  |   POD 1 (API)    |  |   POD 2 (API)    |  |   POD 3 (API)    |   <-- HPA       |   |
|  |  |  +-----------+   |  |  +-----------+   |  |  +-----------+   |   (3-10 pods)   |   |
|  |  |  | Container |   |  |  | Container |   |  |  | Container |   |                  |   |
|  |  |  | non-root  |   |  |  | non-root  |   |  |  | non-root  |   |                  |   |
|  |  |  | readonly  |   |  |  | readonly  |   |  |  | readonly  |   |                  |   |
|  |  |  +-----------+   |  |  +-----------+   |  |  +-----------+   |                  |   |
|  |  +------------------+  +------------------+  +------------------+                  |   |
|  |           |                    |                    |                              |   |
|  |           +--------------------+--------------------+                              |   |
|  |                                |                                                   |   |
|  |                    +-----------v-----------+                                       |   |
|  |                    |    SERVICE (ClusterIP) |                                       |   |
|  |                    |    Port: 80 -> 8080    |                                       |   |
|  |                    +-----------+------------+                                       |   |
|  |                                |                                                   |   |
|  |  +-----------------------------+-----------------------------+                     |   |
|  |  |                             |                             |                     |   |
|  |  v                             v                             v                     |   |
|  |  +-------------+    +------------------+    +------------------+                   |   |
|  |  | ConfigMap   |    |     Secrets      |    | Network Policy   |                   |   |
|  |  | (non-secret |    | (sensitive data) |    | (ingress/egress  |                   |   |
|  |  |  config)    |    |                  |    |  rules)          |                   |   |
|  |  +-------------+    +------------------+    +------------------+                   |   |
|  |                                                                                    |   |
|  +-----------------------------------------------------------------------------------+   |
|                                                                                           |
+-------------------------------------------------------------------------------------------+


+=======================================================================================+
|                                 SECURITY ARCHITECTURE                                  |
+=======================================================================================+

                           +---------------------------+
                           |    INCOMING REQUEST       |
                           +-------------+-------------+
                                         |
                                         v
                           +---------------------------+
                           |   TLS/SSL TERMINATION     |
                           |   (nginx-ingress)         |
                           +-------------+-------------+
                                         |
                                         v
                           +---------------------------+
                           |   RATE LIMITING           |
                           |   Token Bucket Algorithm  |
                           |   100 req/min, burst: 20  |
                           +-------------+-------------+
                                         |
                                         v
                           +---------------------------+
                           |   CORS VALIDATION         |
                           |   Restrictive Origins     |
                           +-------------+-------------+
                                         |
                                         v
                           +---------------------------+
                           |   INPUT SANITIZATION      |
                           |   * XSS Prevention        |
                           |   * SQL Injection Block   |
                           |   * Command Injection     |
                           +-------------+-------------+
                                         |
                                         v
                           +---------------------------+
                           |   JWT AUTHENTICATION      |
                           |   * HS256 Algorithm       |
                           |   * 30 min expiration     |
                           |   * Refresh tokens: 7d    |
                           +-------------+-------------+
                                         |
                                         v
                           +---------------------------+
                           |   AUTHORIZATION (RBAC)    |
                           |   Role-based Access       |
                           +-------------+-------------+
                                         |
                                         v
                           +---------------------------+
                           |   PYDANTIC VALIDATION     |
                           |   Schema Enforcement      |
                           +-------------+-------------+
                                         |
                                         v
                           +---------------------------+
                           |   APPLICATION LOGIC       |
                           +---------------------------+


+=======================================================================================+
|                                  TECHNOLOGY STACK                                      |
+=======================================================================================+

+-------------------+-------------------+-------------------+-------------------+
|     BACKEND       |      AI/ML        |     DATABASE      |    DEPLOYMENT     |
+-------------------+-------------------+-------------------+-------------------+
| * Python 3.11     | * LangChain       | * MongoDB 7.0     | * Docker          |
| * FastAPI         | * Llama 2 (7B)    | * Motor (async)   | * Kubernetes      |
| * Pydantic v2     | * CTransformers   | * Pinecone        | * GitHub Actions  |
| * Uvicorn         | * Sentence-Trans. | * (Vector DB)     | * Prometheus      |
| * python-jose     | * HuggingFace     |                   | * Grafana         |
| * bcrypt          |                   |                   |                   |
+-------------------+-------------------+-------------------+-------------------+

                              +---------------------------+
                              |     DESIGN PRINCIPLES     |
                              +---------------------------+
                              | * Clean Architecture      |
                              | * Dependency Injection    |
                              | * Single Responsibility   |
                              | * Async/Await Patterns    |
                              | * 12-Factor App           |
                              | * Security by Default     |
                              +---------------------------+

```

## Quick Reference

| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Framework | FastAPI | Async API with OpenAPI docs |
| LLM | Llama 2 7B (4-bit) | Medical question answering |
| Vector Store | Pinecone | Semantic document retrieval |
| Database | MongoDB | User data, conversations |
| Caching | In-memory | Rate limiting buckets |
| Monitoring | Prometheus + Grafana | Metrics and dashboards |
| Container | Docker | Consistent deployment |
| Orchestration | Kubernetes | Scalability and resilience |
