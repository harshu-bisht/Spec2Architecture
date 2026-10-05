import os
import chromadb
from chromadb.utils import embedding_functions

# Curated Enterprise System Design Knowledge Base
SYSTEM_DESIGN_PATTERNS = [
    {
        "id": "pattern_cqrs_event_sourcing",
        "title": "CQRS (Command Query Responsibility Segregation) & Event Sourcing",
        "category": "Architecture",
        "content": (
            "Pattern: CQRS & Event Sourcing. Use when write and read workloads have drastically different scaling needs. "
            "Commands mutate state via an immutable Append-Only Event Store (Kafka/PostgreSQL events). "
            "Queries read from denormalized Read Models optimized with Elasticsearch or Redis. "
            "Trade-offs: Provides extreme auditability and horizontal read scaling, but introduces eventual consistency and event schema migration complexity."
        )
    },
    {
        "id": "pattern_saga_distributed_tx",
        "title": "Saga Pattern for Distributed Microservice Transactions",
        "category": "Data Consistency",
        "content": (
            "Pattern: Saga Pattern. Replaces 2-Phase Commit (2PC) in distributed microservices. "
            "Coordinates multi-service transactions using either Choreography (event-driven via message broker) "
            "or Orchestration (central stateful orchestrator). Each step must implement a Compensating Transaction "
            "to roll back changes if downstream services fail. Crucial for Payment, Order, and Inventory workflows."
        )
    },
    {
        "id": "pattern_cache_aside_redis",
        "title": "Cache-Aside & Multi-Level Caching with Redis",
        "category": "Performance",
        "content": (
            "Pattern: Cache-Aside (Lazy Loading). The application queries cache (Redis/Memcached) first; "
            "on cache miss, queries primary DB and populates cache with a defined TTL. "
            "To prevent Cache Stampede (Thundering Herd), use Mutex Locking or probabilistic early expiration. "
            "For write operations, use Cache Invalidation rather than direct cache updates to prevent stale reads."
        )
    },
    {
        "id": "pattern_database_partitioning",
        "title": "Database Sharding, Partitioning & Read Replicas",
        "category": "Storage",
        "content": (
            "Pattern: Sharding & Read Replicas. Use Master-Replica architecture for read-heavy OLTP databases. "
            "Direct writes to Primary, route reads to Read Replicas with replica-lag awareness. "
            "When primary DB exceeds 2TB or IOPS limits, apply Horizontal Sharding using a consistent hash key "
            "(e.g., tenant_id or user_uuid). Avoid cross-shard joins by colocating related entities."
        )
    },
    {
        "id": "pattern_idempotency_api",
        "title": "Idempotent API Design & Rate Limiting",
        "category": "API Design",
        "content": (
            "Pattern: Idempotency Keys & Token Bucket Rate Limiting. For payment, dispatch, and order creation endpoints, "
            "require client-supplied 'Idempotency-Key' in HTTP headers. Store key in Redis with TTL. "
            "If duplicate key arrives, return original response without re-executing logic. "
            "Protect APIs with distributed Token Bucket rate limiter at API Gateway (e.g. Kong, Envoy, Traefik)."
        )
    },
    {
        "id": "pattern_event_driven_kafka",
        "title": "Event-Driven Microservices with Apache Kafka & RabbitMQ",
        "category": "Integration",
        "content": (
            "Pattern: Event-Driven Asynchronous Decoupling. Decouple synchronous HTTP calls by publishing events "
            "to distributed log (Kafka) or AMQP queue (RabbitMQ). Use Kafka for high-throughput, ordered stream processing "
            "(telemetry, audit logs, order streams). Use RabbitMQ for complex message routing and task queues. "
            "Implement Dead Letter Queues (DLQ) for failed message retry handling."
        )
    },
    {
        "id": "pattern_api_gateway_bff",
        "title": "API Gateway & Backend-For-Frontend (BFF) Pattern",
        "category": "Networking",
        "content": (
            "Pattern: API Gateway & BFF. Single entry point for external mobile and web clients. "
            "Handles SSL termination, JWT authentication, rate limiting, request validation, and service aggregation. "
            "BFF tailoring prevents mobile clients from making dozens of chatty microservice calls over cellular networks."
        )
    },
    {
        "id": "pattern_zero_trust_security",
        "title": "Zero-Trust Microservice Security & mTLS",
        "category": "Security",
        "content": (
            "Pattern: Zero-Trust & Mutual TLS (mTLS). Encrypt inter-service communication with mTLS certificates "
            "managed by Service Mesh (Istio / Linkerd). Use short-lived OAuth2/JWT tokens with granular role-based scopes (RBAC). "
            "Store secrets in HashiCorp Vault or AWS Secrets Manager, never in environment variables or code."
        )
    }
]

class SystemDesignRAGEngine:
    """
    RAG Engine that indexes and retrieves architectural patterns to ground
    the LangGraph state machine.
    """

    def __init__(self, persist_dir="./chroma_db"):
        self.persist_dir = persist_dir
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(name="system_design_patterns")
        self._initialize_knowledge_base()

    def _initialize_knowledge_base(self):
        """Seed the vector collection if empty."""
        if self.collection.count() == 0:
            docs = [p["content"] for p in SYSTEM_DESIGN_PATTERNS]
            metadatas = [{"title": p["title"], "category": p["category"]} for p in SYSTEM_DESIGN_PATTERNS]
            ids = [p["id"] for p in SYSTEM_DESIGN_PATTERNS]
            self.collection.add(
                documents=docs,
                metadatas=metadatas,
                ids=ids
            )

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        """Retrieve most relevant system design architectural patterns."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            retrieved = []
            if results and results.get("documents"):
                for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                    retrieved.append({
                        "title": meta.get("title", ""),
                        "category": meta.get("category", ""),
                        "content": doc
                    })
            return retrieved
        except Exception:
            # Fallback to keyword matching if embedding query encounters issues
            keywords = query.lower().split()
            matched = []
            for p in SYSTEM_DESIGN_PATTERNS:
                score = sum(1 for kw in keywords if kw in p["content"].lower())
                if score > 0:
                    matched.append((score, p))
            matched.sort(key=lambda x: x[0], reverse=True)
            return [m[1] for m in matched[:top_k]]
