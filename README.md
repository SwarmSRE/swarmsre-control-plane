# SwarmSRE Control Plane 🐝

**The brain of the operation for predicting, detecting, and fixing Kubernetes incidents using AI.**

SwarmSRE is an autonomous SRE platform built on **LangGraph**. It continuously monitors your Kubernetes clusters, ingests telemetry and logs, synthesizes Root Cause Analyses (RCAs), and proposes actionable Kubernetes manifests to remediate incidents automatically—all while enforcing a strict Human-in-the-Loop (HITL) pause gate for safety.

## 🏗️ Architecture

SwarmSRE follows a **unified ArgoCD-style architecture**:

- **FastAPI Control Plane**: The Python backend that powers the LangGraph state machine, connects to AI models (Gemini/Llama), and manages WebSocket broadcasts.
- **React Dashboard**: The frontend UI built with Vite, React, and D3.js. It is compiled statically and served directly by the FastAPI app in production.
- **MCP Server (Agent)**: An optional Model Context Protocol server deployed in target clusters to execute actions.
- **PostgreSQL**: Stores the immutable audit trail for all AI actions.

## 🚀 Quickstart

### 1. Prerequisites
- `uv` for Python package management
- Node.js 20+ for UI development
- PostgreSQL (or rely on SQLite fallback... *wait, SQLite was removed! You must use Postgres*)

### 2. Environment Setup
```bash
cp .env.example .env
# Edit .env and configure your LLM API keys and DATABASE_URL
```

### 3. Build & Run Locally
```bash
# 1. Build the React UI
cd ui
npm install
npm run build
cd ..

# 2. Run the FastAPI backend
uv run uvicorn main:app --reload
```
Navigate to `http://localhost:8000` to view the SwarmSRE dashboard!

## 🧪 Testing

The platform includes a robust Pytest suite with end-to-end (E2E) flows and WebSocket integration tests.
```bash
PYTHONPATH=. uv run pytest tests/
```

## 🚢 Deployment (Helm)

We provide Helm charts for Kubernetes deployments:
```bash
# Install the SwarmSRE Control Plane
helm install swarmsre charts/swarmsre-server/
```