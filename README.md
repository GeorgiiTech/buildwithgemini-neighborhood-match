# 🏡 Neighborhood Match

> A conversational agent that helps movers and families find the ideal neighborhood and home based on safety, school quality, and lifestyle needs with a catalog of neighborhoods and housing listings.

[![Build with Gemini](https://img.shields.io/badge/Build%20with%20Gemini-World%20Tour-4285F4?logo=google&logoColor=white)](https://github.com/cszhu/build-with-gemini)
[![Track 3](https://img.shields.io/badge/Track%203-Agent--First%20Apps-EA4335)](https://github.com/cszhu/build-with-gemini)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-Agent%20Platform-4285F4?logo=googlecloud&logoColor=white)](https://cloud.google.com/products/agent-platform)
[![Built with ADK](https://img.shields.io/badge/Built%20with-ADK%20%2B%20agents--cli-34A853)](https://google.github.io/agents-cli/)
[![A2UI Enabled](https://img.shields.io/badge/UI-A2UI%20v0.8-blueviolet)](https://adk.dev/integrations/a2ui/)

---

## 🎬 Demo

[![Neighborhood Match Demo](assets/demo.gif)](assets/demo.mp4)

*Live walkthrough showing customer intake interview, preference analysis, and native A2UI recommendation cards with safety scores, school ratings, and budget breakdown.*

> 🎥 **Video:** Watch or download the recording: [`assets/demo.mp4`](assets/demo.mp4)

---

## 🌟 Overview

Relocating to a new city or neighborhood is one of the most stressful life decisions. Information is notoriously fragmented across listing portals, school ranking websites, crime heatmaps, transit boards, and local forums.

**Neighborhood Match** is an intelligent relocation concierge that unifies this workflow into a guided conversation. It understands what matters most to you—whether that is top-tier public schools for your kids, low crime rates, high-speed fiber internet for remote work, or dedicated parking for your vehicles. The agent ranks neighborhoods using a weighted multi-factor scoring model, retrieves real housing listings, calculates monthly living budgets, and presents findings using rich visual cards powered by **Agent-to-User Interface (A2UI)**.

---

## ✨ Key Features

- **📋 Intelligent Intake & Profiling**: Automatically detects whether a user is visiting for the first time or returning. Gathers key parameters: origin, destination, rent vs. buy, budget ceiling, kids/schools, pets, vehicles/parking, remote work needs, and safety vs. walkability priorities.
- **🧠 Cross-Session Long-Term Memory**: Automatically recalls personal facts across visits (e.g., family size, marital status, budget, vehicle count) via Vertex AI Memory Bank, eliminating redundant questions in follow-up sessions.
- **🎯 Weighted Multi-Factor Scoring**: Evaluates neighborhoods using a multi-criteria model that scores safety/crime rate, school district quality, budget affordability, transit/walk scores, fiber internet readiness, and dedicated parking.
- **🏠 Housing Catalog & Inventory Search**: Searches curated real estate listings filtered by bedroom count, target budget, and neighborhood match scores.
- **💰 Affordability Breakdown**: Calculates complete monthly living costs, including rent/mortgage payments, HOA fees, property taxes, estimated utilities, and renter's/homeowner's insurance.
- **📊 Relocation Market Trends & Analytics**: Stores mover origins, target destinations, and reasons for leaving in Firestore, generating aggregate relocation intelligence for future movers.
- **🪟 Native Agent-First UI (A2UI) + Markdown**: Dual-mode rendering delivering conversational prose, pros/cons, and next steps in markdown alongside responsive interactive A2UI cards.
- **🎨 Neighborhood Vibe Concepts**: Generates concept imagery for streetscapes and neighborhood atmosphere using Google Cloud media generation.

---

## ☁️ Google Cloud Architecture & Tools

Neighborhood Match is built on Google Cloud's Agent Platform using the Agent Development Kit (ADK) and integrates the full suite of cloud-native AI services:

| Component | Google Cloud Service | Purpose & Implementation |
|---|---|---|
| **Memory** | **Vertex AI Memory Bank** | Cross-session long-term memory powered by `PreloadMemoryTool` and `generate_memories_callback`. Preserves mover profile facts across conversation turns. |
| **Database** | **Cloud Firestore** | NoSQL document storage storing structured customer intake profiles, indexed neighborhood statistics (crime metrics, school ratings, walkability), and relocation analytics. |
| **Object Storage** | **Cloud Storage (GCS)** | Scalable asset storage for neighborhood streetscape imagery, listing photos, and uploaded documents. |
| **Retrieval** | **Vertex AI RAG Engine** | Grounded document retrieval over municipal neighborhood guides, crime reports, and school district performance data. |
| **Media Generation** | **Imagen / Nano Banana 2** | Dynamic visual concept generation (`gemini-3.1-flash-lite-image`) visualizing neighborhood vibe, architecture, and streetscape aesthetics. |
| **Agent-First UI** | **A2UI (v0.8)** | Declarative component framework (`A2uiSchemaManager`, `BasicCatalog`, `after_model_callback`) rendering responsive cards, metrics, and tables in the chat UI. |
| **Agent Runtime** | **Agent Platform Reasoning Engine** | Serverless agent hosting with native A2A protocol support for scalable, low-latency reasoning and tool orchestration. |
| **Web Frontend** | **Cloud Run** | Containerized FastAPI proxy serving the web chat interface and routing bidirectional A2A protocol communication to the agent backend. |

---

## 📁 Project Structure

```text
build-with-gemini/
├── assets/
│   ├── demo.gif                   # Optimized, looping demo recording
│   └── build-with-gemini-banner.png
├── project_brief.md               # Original project brief and tool coverage spec
├── neighborhood-match/
│   ├── app/
│   │   ├── agent.py               # Core ADK agent, tools, callbacks, and A2UI schema
│   │   ├── firestore_db.py        # Cloud Firestore client, schema seeding, and queries
│   │   └── a2ui_utils.py          # A2UI response formatting callback & prose extraction
│   ├── frontend/
│   │   ├── main.py                # FastAPI A2A client proxy
│   │   ├── static/
│   │   │   └── index.html         # Modern web chat UI with native A2UI renderer
│   │   ├── requirements.txt       # Frontend dependencies
│   │   └── Dockerfile             # Cloud Run container definition
│   ├── agents-cli-manifest.yaml   # Agent Platform deployment manifest
│   ├── deployment_metadata.json   # Deployed Reasoning Engine resource metadata
│   ├── pyproject.toml             # Python dependencies (managed via uv)
│   └── tests/                     # Unit and integration test suite (11 passing tests)
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **uv**: Fast Python package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Google Cloud SDK**: (`gcloud auth login` and `gcloud auth application-default login`)
- **agents-cli**: (`uv tool install google-agents-cli`)

### 1. Install Dependencies

```bash
cd neighborhood-match
uv sync
```

### 2. Test Locally with Agent Playground

Launch the local interactive ADK Playground to test tools, memory callbacks, and reasoning loops:

```bash
agents-cli playground
```

### 3. Run the Web Frontend Locally

Start the FastAPI proxy and chat interface locally:

```bash
cd frontend
uv run python main.py
```

Open `http://localhost:8080` in your browser to interact with the agent.

---

## 🧪 Testing & Evaluation

Run the unit and integration tests:

```bash
uv run pytest tests/unit tests/integration
```

Run agent evaluation against predefined relocation scenarios:

```bash
agents-cli eval
```

### Sample Test Questions

- *"I'm moving with my family (one boy who needs good schools), have a remote job, and want a very safe neighborhood with low crime. Where should we look to rent an apartment under $3,000/month?"*
- *"Show me 2-bedroom listings in Round Rock and calculate the estimated monthly budget including utilities and parking."*
- *"What are the safety and transit scores for Mueller vs. Avery Ranch?"*

---

## 🚢 Deployment

The agent and web frontend are deployed to Google Cloud serverless infrastructure:

```bash
# Deploy the reasoning engine to Agent Platform
agents-cli deploy

# Deploy the frontend proxy to Cloud Run
gcloud run deploy neighborhood-match-frontend \
  --source frontend/ \
  --region us-central1 \
  --allow-unauthenticated
```

---

## 📄 License

This project was developed as part of the **Build with Gemini World Tour** (Track 3: Agent-First Applications). Provided for demonstration purposes.
