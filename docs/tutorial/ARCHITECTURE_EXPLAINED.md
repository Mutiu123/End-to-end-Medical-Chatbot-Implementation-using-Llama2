# Architecture and Workflow - Explained

This document provides a detailed explanation of the architectural decisions, tool choices, and methodologies I used when designing the Medical Chatbot API. I will walk you through each component, explaining why I chose specific approaches and how they work together to create a production-ready system.

## Table of Contents

1. [Why I Chose This Architecture](#why-i-chose-this-architecture)
2. [The RAG Pattern Explained](#the-rag-pattern-explained)
3. [Framework and Technology Choices](#framework-and-technology-choices)
4. [Security Architecture Decisions](#security-architecture-decisions)
5. [Database Design Rationale](#database-design-rationale)
6. [Monitoring Strategy](#monitoring-strategy)
7. [Deployment Architecture](#deployment-architecture)
8. [Trade-offs and Considerations](#trade-offs-and-considerations)

---

## Why I Chose This Architecture

### The Problem I Was Solving

When I started this project, I had a simple Flask-based chatbot that worked for demos but was not ready for production. The original application had several limitations:

- No authentication or authorization
- No rate limiting (anyone could flood the API)
- No structured logging or monitoring
- Direct database calls without connection pooling
- No input validation beyond basic checks
- Single-file architecture that was hard to maintain

I needed to transform this into an enterprise-grade application that could:

1. Handle multiple users securely
2. Scale horizontally under load
3. Be monitored and debugged in production
4. Resist common security attacks
5. Be deployed consistently across environments

### The Layered Architecture Approach

I chose a layered architecture because it provides clear separation of concerns. Looking at the PROJECT_ARCHITECTURE.md diagram, you can see I organized the application into distinct layers:

```
Clients -> API Gateway -> Application Layer -> Service Layer -> Data Layer
```

**Why this matters:** Each layer has a single responsibility. The API layer handles HTTP concerns (validation, serialization). The service layer contains business logic. The data layer manages persistence. This means I can change one layer without affecting others.

For example, if I later decide to switch from MongoDB to PostgreSQL, I only need to modify the data layer. The service layer does not care where data comes from - it just calls the repository methods.

---

## The RAG Pattern Explained

### Why RAG Instead of Fine-tuning?

I chose Retrieval-Augmented Generation (RAG) over fine-tuning the LLM for several important reasons:

**1. Accuracy for Medical Information**

Medical information must be accurate. If I fine-tuned Llama 2 on medical texts, the model would "memorize" information in its weights. But LLMs can hallucinate - they might generate plausible-sounding but incorrect medical advice.

With RAG, every answer is grounded in actual documents. The model can only respond based on the context I provide. If the answer is not in the retrieved documents, the model is instructed to say "I don't know" rather than make something up.

**2. Updatable Knowledge Base**

Medical knowledge evolves. New treatments emerge, guidelines change. With fine-tuning, I would need to retrain the entire model to incorporate new information - an expensive and time-consuming process.

With RAG, I simply add new documents to Pinecone. The next query will automatically consider the new information. No model retraining required.

**3. Traceability**

When a doctor or patient asks "where did this information come from?", I can show the exact source documents. This is critical for medical applications where trust and verification matter.

### How the RAG Pipeline Works

Looking at WORKFLOW_DIAGRAMS.md, I show the RAG pipeline in two phases:

**Indexing Phase (One-time)**

```
PDF Document -> Text Extraction -> Chunking -> Embedding -> Vector Store
```

I chose 500-character chunks with 20-character overlap. Why these numbers?

- **500 characters**: Large enough to contain meaningful information, small enough to be specific. If chunks are too large, the retrieved context might contain irrelevant information. If too small, context is lost.

- **20-character overlap**: Ensures that sentences spanning chunk boundaries are not broken. This preserves semantic coherence.

I use Sentence Transformers (all-MiniLM-L6-v2) for embeddings. This model produces 384-dimensional vectors that capture semantic meaning. It is small (80MB) and fast, which matters for production deployment.

**Query Phase (Every Request)**

```
User Query -> Embed -> Vector Search (k=2) -> Build Prompt -> LLM Inference -> Response
```

I retrieve only k=2 documents. Why so few?

- **Context window limits**: Llama 2 has a context limit. More documents mean less room for the response.
- **Relevance**: The top 2 documents are usually the most relevant. Adding more often adds noise.
- **Latency**: Fewer documents mean faster processing.

---

## Framework and Technology Choices

### FastAPI Over Flask

I migrated from Flask to FastAPI for several reasons:

**1. Async Support**

FastAPI is built on ASGI (Starlette), providing native async/await support. My application makes multiple I/O operations:
- Database queries
- Vector store searches
- LLM inference (which can take seconds)

With Flask, each request blocks a worker while waiting for I/O. With FastAPI, the worker can handle other requests during I/O waits. This dramatically improves throughput under load.

**2. Automatic Validation**

FastAPI integrates with Pydantic. I define schemas once, and FastAPI:
- Validates incoming requests
- Serializes responses
- Generates OpenAPI documentation

In Flask, I would need to write validation code manually for every endpoint.

**3. Modern Python Features**

FastAPI leverages Python type hints. This makes the code self-documenting and enables IDE autocompletion. It also catches errors at development time rather than runtime.

### Pydantic v2 for Validation

I specifically chose Pydantic v2 (not v1) because:

- **Performance**: Pydantic v2 is 5-50x faster than v1. For high-throughput APIs, this matters.
- **Improved validation**: Better error messages, more validation options.
- **Field validators**: I use custom validators for email format, password strength, query sanitization.

Example from my ChatRequest schema:

```python
@field_validator("query")
@classmethod
def sanitize_query(cls, v: str) -> str:
    return v.strip()
```

This automatically strips whitespace from every query before processing.

### Llama 2 with CTransformers

I chose the 7B parameter model with 4-bit quantization because:

**1. Size Constraints**

The full Llama 2 7B model is about 14GB. The 4-bit quantized version is about 3.5GB. This fits in memory on modest hardware without requiring expensive GPUs.

**2. Speed**

CTransformers provides CPU inference in C/C++, which is faster than pure Python implementations. For a production API where response time matters, this is crucial.

**3. Quality Retention**

4-bit quantization reduces precision but retains most of the model's capability. For my use case (answering questions based on provided context), the quality loss is acceptable.

---

## Security Architecture Decisions

### JWT Authentication

I implemented JWT (JSON Web Tokens) with separate access and refresh tokens:

**Access Token (30 minutes)**
- Short-lived to limit exposure if stolen
- Stateless - no database lookup required to validate
- Contains user ID and roles for authorization

**Refresh Token (7 days)**
- Longer-lived for user convenience
- Used only to get new access tokens
- If compromised, can be revoked by changing user's password

**Why not sessions?**

Session-based authentication requires server-side storage. This creates problems for horizontal scaling - if a user's session is on Server A, but their next request goes to Server B, authentication fails.

JWTs are self-contained. Any server can validate them without shared storage.

### Token Bucket Rate Limiting

I implemented the token bucket algorithm rather than simpler alternatives (like fixed window) because:

**The Problem with Fixed Window**

A fixed window of "100 requests per minute" has a flaw: A user could send 100 requests at 0:59, then 100 more at 1:01. That is 200 requests in 2 seconds - essentially bypassing the limit.

**How Token Bucket Works**

The bucket has a capacity (20 tokens) and a refill rate (100/minute = 1.67/second).

- Each request consumes 1 token
- Tokens refill continuously
- If bucket is empty, request is rejected
- Burst capacity (20) allows temporary spikes

This smooths out request rates while allowing legitimate burst traffic.

### Input Sanitization

I implemented multi-layer input sanitization:

**1. Pydantic Validation**
- Length limits (max 2000 characters for queries)
- Type checking
- Required field validation

**2. Custom Sanitization**
- HTML entity encoding (prevents XSS)
- SQL keyword detection (prevents injection)
- Command character stripping (prevents command injection)

**Why multiple layers?**

Defense in depth. If one layer fails, others catch the attack. For a medical application, security is not optional.

---

## Database Design Rationale

### MongoDB Over SQL

I chose MongoDB for this project because:

**1. Document Model Fits the Data**

Conversations are naturally document-like:
```json
{
  "session_id": "abc123",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

This maps directly to MongoDB documents. With SQL, I would need separate tables and JOINs.

**2. Schema Flexibility**

As I iterate on the product, the data model might change. MongoDB handles schema evolution gracefully - I can add fields without migrations.

**3. Horizontal Scaling**

MongoDB shards data across servers. For a chat application that might have millions of conversations, this matters.

### Connection Pooling

I configured a connection pool with min=10, max=50 connections. Why?

**Minimum (10)**

Cold start is slow. If I create connections on-demand, the first requests after deployment wait for connection establishment. Pre-creating 10 connections means immediate availability.

**Maximum (50)**

This limits resource usage. If I allowed unlimited connections, a traffic spike could exhaust database server resources and crash everything.

**Singleton Pattern**

I use a singleton for the database manager:

```python
class DatabaseManager:
    _instance: Optional["DatabaseManager"] = None

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

This ensures all parts of the application share the same connection pool. Creating multiple pools would waste connections.

---

## Monitoring Strategy

### Why Prometheus + Grafana?

I chose this stack because:

**1. Pull-Based Model**

Prometheus scrapes metrics from my application. This is more reliable than push-based systems - if the monitoring system is down, I do not lose application stability.

**2. Kubernetes Integration**

Prometheus service discovery automatically finds pods. I do not need to manually configure endpoints.

**3. PromQL**

The query language is powerful. I can write complex queries like "95th percentile latency over the last hour, broken down by endpoint."

### The 15 Metrics I Collect

I did not add metrics randomly. Each serves a purpose:

**Request Metrics** (5)
- `requests_total`: Know traffic volume
- `request_latency`: Know performance
- `active_requests`: Know concurrency
- `request_size`: Know payload patterns
- `response_size`: Know response patterns

**LLM Metrics** (4)
- `llm_inference_latency`: The biggest latency contributor
- `llm_requests_total`: Track LLM usage
- `llm_tokens_total`: Track cost (LLM tokens are not free)
- `llm_errors_total`: Know when LLM fails

**System Metrics** (6)
- `db_connections`: Know pool utilization
- `rate_limit_hits`: Know if limits are too aggressive
- `health_check_status`: Know component health
- `auth_attempts`: Detect brute force attacks
- `active_sessions`: Know concurrent users
- `cache_hits/misses`: Know cache effectiveness

### Structured Logging

I format logs as JSON, not plain text. Why?

**Machine Parseable**

Log aggregators (ELK, Splunk) can parse JSON automatically. I can search "find all logs where status_code=500 and latency > 1000ms."

**Request ID Tracking**

Every log includes the request ID:

```json
{
  "request_id": "abc123",
  "message": "Query processed",
  "latency_ms": 450
}
```

When debugging, I can trace a single request across all components.

---

## Deployment Architecture

### Multi-Stage Docker Build

Looking at my Dockerfile, I use multi-stage builds:

```dockerfile
FROM python:3.11-slim as builder
# Install dependencies, create wheels

FROM python:3.11-slim as production
# Copy only what's needed
```

**Why?**

The builder stage contains compilers, headers, and build tools (hundreds of MB). The production image does not need these. Multi-stage builds keep the final image small (reduced attack surface, faster pulls).

### Non-Root Container Execution

```dockerfile
RUN useradd --uid 1000 appuser
USER appuser
```

If someone exploits my application, they gain container access as `appuser`, not `root`. This limits damage potential.

### Kubernetes Architecture

I deploy with 3 replicas minimum because:

**1. High Availability**

If one pod crashes, two others handle traffic. Zero downtime.

**2. Rolling Updates**

Kubernetes updates pods one at a time. With 3 replicas, 2 always serve traffic during deployment.

**3. Pod Anti-Affinity**

I configure pods to spread across nodes:

```yaml
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
```

If a node fails, not all pods go down together.

### Horizontal Pod Autoscaler

```yaml
minReplicas: 3
maxReplicas: 10
metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        averageUtilization: 70
```

When CPU crosses 70%, Kubernetes adds pods. When it drops, pods are removed. This handles traffic spikes automatically without manual intervention.

---

## Trade-offs and Considerations

### What I Sacrificed for Simplicity

**1. No Redis**

A production system might use Redis for:
- Rate limiting (distributed)
- Session storage
- Response caching

I used in-memory storage instead. This is simpler but does not work for horizontal scaling. Each pod has its own rate limit bucket.

**Future improvement:** Add Redis for distributed rate limiting.

**2. No Message Queue**

For very long LLM inferences, I might want to queue requests and process asynchronously. I chose synchronous processing for simplicity.

**Future improvement:** Add RabbitMQ/Redis queues for async processing.

**3. Model Stored Locally**

The LLM model file (3.5GB) must be present in each container. This makes images large and deployments slow.

**Future improvement:** Use a model serving system (TensorRT, Triton) with shared model storage.

### What I Would Do Differently for 10x Scale

If this system needed to handle 10x more traffic:

1. **Add caching layer**: Cache frequent query responses in Redis
2. **Separate LLM service**: Run LLM inference on dedicated GPU instances
3. **Read replicas**: Add MongoDB read replicas for query distribution
4. **CDN for static assets**: Offload static file serving
5. **Regional deployment**: Deploy to multiple regions for lower latency

---

## Conclusion

The architecture I designed balances several competing concerns:

- **Security vs. Usability**: JWT with refresh tokens provides security without constant re-login
- **Performance vs. Accuracy**: RAG with k=2 retrieval balances speed and relevance
- **Complexity vs. Maintainability**: Layered architecture adds structure without over-engineering
- **Cost vs. Capability**: 4-bit quantization runs on CPU while maintaining quality

Every decision has trade-offs. I chose options that provide the best balance for a production medical chatbot while leaving room for future scaling.

The diagrams in PROJECT_ARCHITECTURE.md and WORKFLOW_DIAGRAMS.md visualize these concepts. Use them as a reference when you need to understand how components interact or when explaining the system to others.
