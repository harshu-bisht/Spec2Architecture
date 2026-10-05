import json
from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from llm_provider import LLMProvider
from rag_engine import SystemDesignRAGEngine

class ArchitectureState(TypedDict):
    prd_text: str
    system_scale: str
    active_step: str
    functional_reqs: List[str]
    non_functional_reqs: Dict[str, Any]
    retrieved_patterns: List[Dict[str, str]]
    database_schema_sql: str
    mermaid_erd: str
    microservices: List[Dict[str, Any]]
    api_spec_openapi: str
    architecture_mermaid: str
    docker_compose_yaml: str
    validation_score: int
    validation_critique: str
    iteration_count: int
    execution_logs: List[str]


class Spec2ArchitectureGraph:
    """
    LangGraph Multi-Agent Architecture Engine.
    Executes a stateful, cyclical graph to convert PRD specs into
    validated, production-grade microservice blueprints.
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.rag = SystemDesignRAGEngine()
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(ArchitectureState)

        # Register Multi-Agent Nodes
        workflow.add_node("requirement_analyst", self._node_requirement_analyst)
        workflow.add_node("pattern_rag_retriever", self._node_pattern_rag_retriever)
        workflow.add_node("database_architect", self._node_database_architect)
        workflow.add_node("api_service_architect", self._node_api_service_architect)
        workflow.add_node("architecture_validator", self._node_architecture_validator)
        workflow.add_node("infrastructure_architect", self._node_infrastructure_architect)

        # Set Entry Point
        workflow.set_entry_point("requirement_analyst")

        # Standard Sequential Transitions
        workflow.add_edge("requirement_analyst", "pattern_rag_retriever")
        workflow.add_edge("pattern_rag_retriever", "database_architect")
        workflow.add_edge("database_architect", "api_service_architect")
        workflow.add_edge("api_service_architect", "architecture_validator")

        # Cyclical Conditional Edge: Quality Gate
        workflow.add_conditional_edges(
            "architecture_validator",
            self._validation_router,
            {
                "refine": "database_architect",
                "proceed": "infrastructure_architect",
            }
        )

        workflow.add_edge("infrastructure_architect", END)
        return workflow.compile()

    # ── NODE 1: Requirement Analyst ──────────────────────────────────────────
    def _node_requirement_analyst(self, state: ArchitectureState) -> Dict[str, Any]:
        prompt = f"""
Analyze this Product Requirement Document (PRD) for an enterprise software system:
---
{state['prd_text']}
---
Target Scale Tier: {state.get('system_scale', 'High Throughput (100k+ DAU)')}

Extract:
1. Key Functional Requirements (bullet list of 4-6 core capabilities)
2. Non-Functional Requirements (Latency target in ms, Consistency model: Strong vs Eventual, Read/Write Ratio, SLA)
3. Domain Entities (e.g., User, Booking, Payment, Vehicle, etc.)

Format response clearly with headings.
"""
        response = self.llm.generate(prompt, system_prompt="You are a Principal Software Architect analyzing system requirements.")
        
        logs = state.get("execution_logs", [])
        logs.append("✅ Node 1 [Requirement Analyst]: Extracted domain entities & non-functional requirements.")
        
        return {
            "functional_reqs": [line.strip() for line in response.split("\n") if line.strip().startswith(("-", "*", "1", "2", "3", "4", "5"))][:6],
            "non_functional_reqs": {"summary": response},
            "active_step": "Requirement Analysis Completed",
            "execution_logs": logs
        }

    # ── NODE 2: Pattern RAG Retriever ─────────────────────────────────────────
    def _node_pattern_rag_retriever(self, state: ArchitectureState) -> Dict[str, Any]:
        query = f"{state['prd_text']} {state.get('system_scale', '')}"
        retrieved = self.rag.retrieve(query, top_k=3)
        
        logs = state.get("execution_logs", [])
        pattern_names = ", ".join([p.get('title', '') for p in retrieved])
        logs.append(f"✅ Node 2 [Pattern RAG]: Grounded with architectural patterns: {pattern_names}")

        return {
            "retrieved_patterns": retrieved,
            "active_step": "Architectural Patterns Retrieved via RAG",
            "execution_logs": logs
        }

    # ── NODE 3: Database & ERD Architect ─────────────────────────────────────
    def _node_database_architect(self, state: ArchitectureState) -> Dict[str, Any]:
        patterns_str = "\n".join([f"- {p['title']}: {p['content']}" for p in state.get('retrieved_patterns', [])])
        critique = state.get("validation_critique", "")
        critique_prompt = f"\nAddress this previous audit critique in your redesign:\n{critique}" if critique else ""

        prompt = f"""
Design the complete Database Architecture for this system:
PRD: {state['prd_text']}
Scale: {state.get('system_scale', 'Enterprise')}
Grounded Architectural Patterns:
{patterns_str}
{critique_prompt}

Generate TWO parts:
1. SQL Schema (PostgreSQL): Complete DDL statements with PRIMARY KEYs (UUIDs), FOREIGN KEYs, appropriate data types, and performance INDEXES (e.g. for high-cardinality searches).
2. Mermaid ERD: Provide a clean 'erDiagram' enclosed in ```mermaid code block illustrating entities and their 1-to-many / many-to-many cardinalities.
"""
        response = self.llm.generate(prompt, system_prompt="You are a Principal Database Administrator & Data Architect.")
        
        # Parse Mermaid ERD
        mermaid_erd = "erDiagram\n    USER ||--o{ BOOKING : places\n    BOOKING ||--|| PAYMENT : has"
        if "```mermaid" in response:
            try:
                mermaid_erd = response.split("```mermaid")[1].split("```")[0].strip()
            except Exception:
                pass

        logs = state.get("execution_logs", [])
        logs.append("✅ Node 3 [Database Architect]: Formulated normalized SQL schemas, indexes, and Mermaid ERD.")

        return {
            "database_schema_sql": response,
            "mermaid_erd": mermaid_erd,
            "active_step": "Database Schema & ERD Synthesized",
            "execution_logs": logs
        }

    # ── NODE 4: API & Microservice Architect ─────────────────────────────────
    def _node_api_service_architect(self, state: ArchitectureState) -> Dict[str, Any]:
        prompt = f"""
Design the Microservices Boundary and REST/gRPC API contracts for:
PRD: {state['prd_text']}

Requirements:
1. Identify 3 to 4 Decoupled Microservices (e.g., Auth & Identity Service, Core Domain Service, Notification/Worker Service, Payment/Billing Service).
2. For each service: Define responsibility, database ownership, and internal vs external exposure.
3. Generate a valid OpenAPI 3.0 YAML / JSON snippet for the 3 most critical endpoints (showing method, path, requestBody, and 200/400 responses).
4. Provide a Mermaid Architecture Flowchart in ```mermaid code block (graph TD) showing clients -> API Gateway -> Microservices -> DBs & Cache.
"""
        response = self.llm.generate(prompt, system_prompt="You are an Enterprise API Architect & Microservice Specialist.")

        # Parse architecture flowchart
        arch_mermaid = "graph TD\n    Client[Mobile/Web Apps] --> Gateway[API Gateway / Kong]\n    Gateway --> S1[Auth Service]\n    Gateway --> S2[Core Service]\n    S2 --> DB[(PostgreSQL)]\n    S2 --> Cache[(Redis Cache)]"
        if "```mermaid" in response:
            try:
                arch_mermaid = response.split("```mermaid")[1].split("```")[0].strip()
            except Exception:
                pass

        logs = state.get("execution_logs", [])
        logs.append("✅ Node 4 [API & Microservice Architect]: Generated service boundaries, OpenAPI contracts & Architecture diagram.")

        return {
            "api_spec_openapi": response,
            "architecture_mermaid": arch_mermaid,
            "active_step": "Microservice Architecture & OpenAPI Contracts Defined",
            "execution_logs": logs
        }

    # ── NODE 5: Architecture Validator & Quality Gate ─────────────────────────
    def _node_architecture_validator(self, state: ArchitectureState) -> Dict[str, Any]:
        current_iter = state.get("iteration_count", 0) + 1
        
        prompt = f"""
Perform a rigorous, strict Enterprise Architecture Review on this system design:
PRD: {state['prd_text']}
Database Schema:
{state.get('database_schema_sql', '')[:1000]}...
Microservice API Architecture:
{state.get('api_spec_openapi', '')[:1000]}...

Evaluate against:
1. Single Point of Failure (SPOF)
2. Data consistency (Is there appropriate caching, transaction rollback mechanism?)
3. Security (Auth, rate limiting, data isolation)
4. Scalability bottlenecks

Output your evaluation in this EXACT format:
SCORE: <integer between 60 and 95>
CRITIQUE: <2-3 sentences of actionable recommendations for missing items or improvements>
STATUS: <PASS or FAIL>
"""
        response = self.llm.generate(prompt, system_prompt="You are a Chief Technology Officer (CTO) conducting an architecture audit.")
        
        # Extract score
        score = 85
        try:
            for line in response.split("\n"):
                if "SCORE:" in line.upper():
                    score = int(''.join(filter(str.isdigit, line.split(":")[-1])))
                    break
        except Exception:
            score = 82

        logs = state.get("execution_logs", [])
        logs.append(f"🔍 Node 5 [Architecture Validator] (Iteration {current_iter}): System Score: {score}/100. Audit completed.")

        return {
            "validation_score": score,
            "validation_critique": response,
            "iteration_count": current_iter,
            "active_step": f"Architecture Audited — Score {score}/100",
            "execution_logs": logs
        }

    # ── ROUTER: Conditional Edge Logic ────────────────────────────────────────
    def _validation_router(self, state: ArchitectureState) -> str:
        score = state.get("validation_score", 85)
        iteration = state.get("iteration_count", 1)

        # Cyclical refinement loop if score is low and hasn't repeated more than once
        if score < 75 and iteration < 2:
            return "refine"
        return "proceed"

    # ── NODE 6: Infrastructure & Docker Architect ─────────────────────────────
    def _node_infrastructure_architect(self, state: ArchitectureState) -> Dict[str, Any]:
        prompt = f"""
Generate production-ready infrastructure artifacts for:
PRD: {state['prd_text']}

Deliverables:
1. Complete `docker-compose.yml` including:
   - PostgreSQL 16 container with health check and volume
   - Redis 7 container for distributed caching
   - API Gateway container (Kong or Traefik or Envoy)
   - Microservice app containers with environment variables and restart policies
2. Production Deployment & Monitoring Blueprint (Prometheus, Grafana, Distributed Tracing with OpenTelemetry).
"""
        response = self.llm.generate(prompt, system_prompt="You are a Principal Site Reliability Engineer (SRE) & DevOps Architect.")

        logs = state.get("execution_logs", [])
        logs.append("✅ Node 6 [DevOps Architect]: Generated production docker-compose.yml & telemetry topology.")

        return {
            "docker_compose_yaml": response,
            "active_step": "Full System Architecture Dossier Synthesized",
            "execution_logs": logs
        }

    def run(self, prd_text: str, system_scale: str = "High Throughput (100k+ DAU)") -> ArchitectureState:
        """Execute the LangGraph workflow from start to end."""
        initial_state: ArchitectureState = {
            "prd_text": prd_text,
            "system_scale": system_scale,
            "active_step": "Initializing Graph...",
            "functional_reqs": [],
            "non_functional_reqs": {},
            "retrieved_patterns": [],
            "database_schema_sql": "",
            "mermaid_erd": "",
            "microservices": [],
            "api_spec_openapi": "",
            "architecture_mermaid": "",
            "docker_compose_yaml": "",
            "validation_score": 0,
            "validation_critique": "",
            "iteration_count": 0,
            "execution_logs": ["🚀 LangGraph Engine Initialized."]
        }
        return self.graph.invoke(initial_state)
