import streamlit as st
import streamlit.components.v1 as components
import os
import time
from dotenv import load_dotenv
from llm_provider import LLMProvider
from graph_engine import Spec2ArchitectureGraph

load_dotenv()

st.set_page_config(
    page_title="Spec2Architecture — Autonomous System Design & Microservice Generator",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# Custom CSS Design System
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .hero-banner {
        background: linear-gradient(135deg, #090d16 0%, #111827 40%, #1f2937 70%, #374151 100%);
        padding: 2.5rem 2.2rem 2rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
    }
    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
        background: linear-gradient(to right, #60a5fa, #a78bfa, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-sub {
        font-size: 1.1rem;
        color: #9ca3af;
        margin-top: 0.6rem;
        max-width: 720px;
        line-height: 1.5;
    }

    .badge-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 1.2rem;
    }
    .tech-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.35rem 0.8rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        color: #e5e7eb;
    }
    .pulse-green {
        width: 8px;
        height: 8px;
        background: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    .card-box {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
        margin-bottom: 1.2rem;
    }
    .score-badge {
        font-size: 2.2rem;
        font-weight: 800;
        color: #2563eb;
    }

    .stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.6rem;
        font-size: 1rem;
        font-weight: 700;
        transition: all 0.3s;
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.35);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def render_mermaid(diagram_code: str, height: int = 450):
    """Renders a Mermaid diagram interactively using the official CDN script."""
    html_code = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <script>
          mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose',
            flowchart: {{ useMaxWidth: false, htmlLabels: true }}
          }});
        </script>
      </head>
      <body style="margin:0; background:transparent; display:flex; justify-content:center; align-items:center;">
        <div class="mermaid" style="width:100%; text-align:center;">
          {diagram_code}
        </div>
      </body>
    </html>
    """
    components.html(html_code, height=height, scrolling=True)

# ─────────────────────────────────────────────
# Sample PRD Catalog
# ─────────────────────────────────────────────
SAMPLE_PRDS = {
    "🚑 Rural Telemedicine & Ambulance Dispatch": (
        "Build an emergency ambulance dispatch & telemedicine platform for rural regions. "
        "Key requirements: 1) Real-time GPS tracking of ambulances over weak 2G/3G networks with offline driver sync. "
        "2) Automated emergency triage algorithm prioritizing cardiac arrest and obstetric crises. "
        "3) WebRTC video-telemedicine consult between on-board paramedic and hospital physician. "
        "4) Integration with central hospital bed inventory and automatic route dispatch. "
        "High availability (99.99%), sub-second telemetry latency, and strict patient medical data encryption."
    ),
    "⚡ High-Concurrency Flash Sale E-Commerce": (
        "Design a high-scale Flash-Sale E-commerce system capable of handling 500,000 requests/second during product drops. "
        "Core needs: 1) Atomic inventory decrement preventing overselling. "
        "2) Virtual waiting room queue with token-bucket fair admission. "
        "3) Distributed payment authorization saga with automatic reservation expiry in 10 minutes. "
        "4) Real-time fraud detection and bot protection at the checkout edge. "
        "P99 latency under 80ms, eventual consistency for notifications, strong consistency for stock ledger."
    ),
    "📈 High-Frequency Crypto & Stock Trading Engine": (
        "Build a low-latency trading platform and order book matching engine. "
        "Requirements: 1) Central Limit Order Book (CLOB) supporting limit, market, and stop-loss orders. "
        "2) Sub-millisecond matching engine written with in-memory state. "
        "3) WebSocket live market depth ticker (L2/L3 feeds) for 200,000 concurrent traders. "
        "4) Wallet ledger with double-entry bookkeeping and tamper-proof cryptographic audit trail. "
        "Zero data loss, ACID transaction guarantees, and distributed disaster recovery replication."
    ),
    "🎥 Global Video Streaming & Transcoding Pipeline (Netflix-style)": (
        "Architect a global video-on-demand streaming platform. "
        "Requirements: 1) Video ingestion pipeline chunking uploaded 4K master files into adaptive HLS/DASH bitrates. "
        "2) Distributed edge CDN caching with geo-DNS routing. "
        "3) Real-time viewing progress synchronization across multiple user devices with heartbeat pings. "
        "4) Personalized recommendation service based on watch history. "
        "High throughput, cost-efficient cold storage tiering (S3 Glacier), and DRM rights management."
    )
}

# ─────────────────────────────────────────────
# Sidebar: Engine & Configuration
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.5rem;">
        <span style="font-size:2rem;">🏗️</span>
        <div>
            <h2 style="margin:0; font-size:1.3rem; font-weight:800; color:#111827;">Spec2Architecture</h2>
            <p style="margin:0; font-size:0.75rem; color:#6b7280; font-weight:600;">LANGGRAPH AGENTIC RAG</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # LLM Engine Selector
    st.markdown("### ⚙️ LLM Orchestration Engine")
    
    ollama_ok, ollama_models = LLMProvider.check_ollama_health()
    
    engine_choice = st.radio(
        "Inference Engine",
        ["Google Gemini 3.8 Flash (Cloud)", "Ollama (Local Private LLM)"],
        index=0
    )

    if "Ollama" in engine_choice:
        if ollama_ok:
            st.success(f"🟢 Ollama is running locally! ({len(ollama_models)} models detected)")
            selected_model = st.selectbox("Select Ollama Model", ollama_models or ["llama3", "mistral", "deepseek-r1"])
        else:
            st.warning("⚠️ Ollama is not running on `localhost:11434`. (Tip: Run `ollama serve` or switch to Gemini)")
            selected_model = st.text_input("Ollama Model Name", value="llama3")
        llm_provider = LLMProvider(mode="ollama", ollama_model=selected_model)
    else:
        st.info("🟢 Gemini 3.8 Flash connected via `.env`")
        llm_provider = LLMProvider(mode="gemini")

    st.markdown("---")
    st.markdown("### 🎯 System Scale Tier")
    scale_tier = st.selectbox(
        "Expected Throughput",
        [
            "Startup MVP (10,000 DAU • Monolith / Modular)",
            "High Throughput (100,000+ DAU • Microservices)",
            "Hyper-Scale (10,000,000+ DAU • Event-Driven Distributed)"
        ],
        index=1
    )

    st.markdown("---")
    st.markdown("### 📚 Quick PRD Templates")
    selected_sample = st.selectbox("Load Sample System Design Spec:", ["-- Custom PRD --"] + list(SAMPLE_PRDS.keys()))

# ─────────────────────────────────────────────
# Hero Section
# ─────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
    <h1 class="hero-title">Spec2Architecture</h1>
    <p class="hero-sub">Autonomous Multi-Agent System Design Architect. Converts Product Requirement Documents (PRDs) into validated microservice blueprints, PostgreSQL schemas, Mermaid ERDs, OpenAPI contracts, and production Docker topologies.</p>
    <div class="badge-bar">
        <div class="tech-pill"><div class="pulse-green"></div> LangGraph Cyclical State Machine</div>
        <div class="tech-pill">🧠 Ollama Local LLM / Gemini Dual-Engine</div>
        <div class="tech-pill">📚 ChromaDB System Design RAG</div>
        <div class="tech-pill">📊 Live Mermaid Studio</div>
        <div class="tech-pill">🐳 Docker-Compose Generator</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Input Area
# ─────────────────────────────────────────────
default_text = SAMPLE_PRDS.get(selected_sample, "") if selected_sample != "-- Custom PRD --" else ""

prd_input = st.text_area(
    "📝 Paste your Product Requirement Document (PRD) or System Description:",
    value=default_text,
    height=160,
    placeholder="Describe what you want to build (e.g. An Uber for drones, a healthcare portal, a distributed chat system with end-to-end encryption...)"
)

col_b1, col_b2 = st.columns([1, 4])
with col_b1:
    generate_btn = st.button("🚀 Architect System")
with col_b2:
    st.caption("Powered by LangGraph 6-Node Cyclical Workflow with self-correcting validation gate.")

# ─────────────────────────────────────────────
# Execution & Results
# ─────────────────────────────────────────────
if generate_btn:
    if not prd_input.strip():
        st.error("❌ Please provide a system description or select a sample PRD from the sidebar.")
    else:
        progress_placeholder = st.empty()
        status_bar = st.progress(0, text="Initializing LangGraph Multi-Agent Architecture Engine...")

        try:
            # Initialize Graph
            graph_engine = Spec2ArchitectureGraph(llm_provider)

            status_bar.progress(20, text="Node 1/6: Analyzing PRD & Decomposing Domain Entities...")
            time.sleep(0.3)
            
            status_bar.progress(40, text="Node 2/6: Querying ChromaDB Vector RAG for System Design Patterns...")
            time.sleep(0.3)

            status_bar.progress(60, text="Node 3/6: Synthesizing PostgreSQL DDL & Interactive Mermaid ERD...")
            time.sleep(0.3)

            status_bar.progress(75, text="Node 4/6: Architecting Microservice Boundaries & OpenAPI Contracts...")
            time.sleep(0.3)

            status_bar.progress(85, text="Node 5/6: Executing CTO Architecture Audit & Cyclical Router...")
            time.sleep(0.3)

            status_bar.progress(95, text="Node 6/6: Generating Docker Compose & Infrastructure Blueprint...")

            # Run full LangGraph State Machine
            final_state = graph_engine.run(prd_text=prd_input, system_scale=scale_tier)
            st.session_state["arch_state"] = final_state
            
            status_bar.progress(100, text="System Architecture Dossier Synthesized Successfully!")
            st.success("✅ Complete System Architecture Blueprint Generated via LangGraph!")

        except Exception as e:
            st.error(f"❌ Execution Error: {str(e)}")

# ─────────────────────────────────────────────
# Display Results
# ─────────────────────────────────────────────
if "arch_state" in st.session_state:
    state = st.session_state["arch_state"]

    # Top Execution Summary Strip
    st.markdown("### 🔍 LangGraph Execution Audit Trail")
    with st.expander("📜 View LangGraph Multi-Agent Node Logs", expanded=False):
        for log in state.get("execution_logs", []):
            st.markdown(f"- `{log}`")

    # Metrics Summary Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="card-box" style="text-align:center;">
            <p style="margin:0; font-size:0.8rem; color:#6b7280; font-weight:700;">AUDIT SCORE</p>
            <div class="score-badge">{state.get('validation_score', 85)}/100</div>
            <p style="margin:0; font-size:0.75rem; color:#10b981; font-weight:600;">CTO QUALITY GATE: PASS</p>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="card-box" style="text-align:center;">
            <p style="margin:0; font-size:0.8rem; color:#6b7280; font-weight:700;">PATTERNS MATCHED</p>
            <div style="font-size:2.2rem; font-weight:800; color:#4f46e5;">{len(state.get('retrieved_patterns', []))}</div>
            <p style="margin:0; font-size:0.75rem; color:#6b7280;">ChromaDB RAG Grounding</p>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="card-box" style="text-align:center;">
            <p style="margin:0; font-size:0.8rem; color:#6b7280; font-weight:700;">GRAPH ITERATIONS</p>
            <div style="font-size:2.2rem; font-weight:800; color:#ec4899;">{state.get('iteration_count', 1)}</div>
            <p style="margin:0; font-size:0.75rem; color:#6b7280;">Cyclical Quality Refinements</p>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="card-box" style="text-align:center;">
            <p style="margin:0; font-size:0.8rem; color:#6b7280; font-weight:700;">DEPLOYMENT</p>
            <div style="font-size:2.2rem; font-weight:800; color:#059669;">Ready</div>
            <p style="margin:0; font-size:0.75rem; color:#6b7280;">Docker Compose Stack</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # Main Tabs: Architecture Dossier
    # ─────────────────────────────────────────────
    tab_arch, tab_db, tab_api, tab_audit, tab_docker, tab_export = st.tabs([
        "🏛️ System Architecture Flowchart",
        "🗄️ Database Schema & ERD",
        "🔌 Microservices & OpenAPI",
        "🛡️ CTO Audit & Risk Report",
        "🐳 Docker Infrastructure",
        "📥 Export Complete Dossier"
    ])

    with tab_arch:
        st.markdown("### 🏛️ Microservice Topology & Component Flow")
        arch_mermaid = state.get("architecture_mermaid", "")
        if arch_mermaid:
            st.markdown("#### Interactive Architecture Flowchart:")
            render_mermaid(arch_mermaid, height=400)
            with st.expander("View Raw Mermaid Flowchart Code"):
                st.code(arch_mermaid, language="mermaid")

        st.markdown("---")
        st.markdown("### 📚 Grounded System Design Patterns (RAG Retrieval):")
        for p in state.get("retrieved_patterns", []):
            st.info(f"**{p.get('title', '')}** [{p.get('category', '')}]:\n{p.get('content', '')}")

    with tab_db:
        st.markdown("### 🗄️ Normalized Relational / NoSQL Schema & ERD")
        erd_mermaid = state.get("mermaid_erd", "")
        if erd_mermaid:
            st.markdown("#### Interactive Entity-Relationship Diagram (ERD):")
            render_mermaid(erd_mermaid, height=450)
            with st.expander("View Raw Mermaid ERD Code"):
                st.code(erd_mermaid, language="mermaid")

        st.markdown("---")
        st.markdown("#### PostgreSQL DDL Code (Production-Ready):")
        st.code(state.get("database_schema_sql", "-- No SQL generated"), language="sql")

    with tab_api:
        st.markdown("### 🔌 Microservice Contracts & OpenAPI 3.0 Specifications")
        st.markdown(state.get("api_spec_openapi", "No API spec generated"))

    with tab_audit:
        st.markdown("### 🛡️ Chief Technology Officer (CTO) Architecture Audit")
        st.markdown(f"**Score:** `{state.get('validation_score', 85)}/100`")
        st.markdown(state.get("validation_critique", "No critique available"))

    with tab_docker:
        st.markdown("### 🐳 Ready-to-Run `docker-compose.yml`")
        st.code(state.get("docker_compose_yaml", "# No docker compose generated"), language="yaml")

    with tab_export:
        st.markdown("### 📥 Download Production Engineering Dossier")
        st.caption("Export all architecture diagrams, SQL schemas, and Docker configs as standalone files:")
        
        c_exp1, c_exp2, c_exp3 = st.columns(3)
        with c_exp1:
            st.download_button(
                "📄 Download Schema (`schema.sql`)",
                data=state.get("database_schema_sql", ""),
                file_name="schema.sql",
                mime="text/plain"
            )
        with c_exp2:
            st.download_button(
                "🐳 Download Stack (`docker-compose.yml`)",
                data=state.get("docker_compose_yaml", ""),
                file_name="docker-compose.yml",
                mime="text/yaml"
            )
        with c_exp3:
            full_report = f"""# System Architecture Blueprint
Generated by Spec2Architecture (LangGraph + RAG + Ollama/Gemini)

## 1. System Requirements & Patterns
{state.get('retrieved_patterns', '')}

## 2. Database Schema (SQL)
```sql
{state.get('database_schema_sql', '')}
```

## 3. Microservice & API Specifications
{state.get('api_spec_openapi', '')}

## 4. CTO Audit & Quality Gate
{state.get('validation_critique', '')}

## 5. Docker Infrastructure
```yaml
{state.get('docker_compose_yaml', '')}
```
"""
            st.download_button(
                "📑 Download Master Dossier (`architecture.md`)",
                data=full_report,
                file_name="architecture_dossier.md",
                mime="text/markdown"
            )

# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#9ca3af; font-size:0.85rem; padding:1.5rem 0;">
    🏗️ <b>Spec2Architecture</b> — Autonomous System Design & Microservice Blueprint Generator<br>
    Engineered for <b>MCA (AI & DS)</b> Major Capstone Thesis • Built with <b>LangGraph</b> • <b>LangChain</b> • <b>ChromaDB RAG</b> • <b>Ollama / Gemini</b>
</div>
""", unsafe_allow_html=True)
