# SwarmSRE Control Plane 🐝

**The brain of the operation for predicting, detecting, and fixing Kubernetes incidents using AI.**

SwarmSRE is an autonomous SRE platform built on **LangGraph**. It continuously monitors your Kubernetes clusters, ingests telemetry and logs, synthesizes Root Cause Analyses (RCAs), and proposes actionable Kubernetes manifests to remediate incidents automatically—all while enforcing a strict Human-in-the-Loop (HITL) pause gate for safety.

## 🏗️ Architecture

SwarmSRE follows a **unified ArgoCD-style architecture**:

- **FastAPI Control Plane**: The Python backend that powers the LangGraph state machine, connects to AI models (Gemini/Llama), and manages WebSocket broadcasts.
- **React Dashboard**: The frontend UI built with Vite, React, and D3.js. It is compiled statically and served directly by the FastAPI app in production.
- **MCP Server (Agent)**: An optional Model Context Protocol server deployed in target clusters to execute actions.
- **PostgreSQL**: Stores the immutable audit trail for all AI actions.

## 🚀 Quick Install (Kubernetes)

SwarmSRE is designed to be installed on any Kubernetes cluster in seconds.

### Option 1: Static Manifest (Easiest)
```bash
kubectl create namespace swarmsre-system
kubectl apply -n swarmsre-system -f https://get.swarmsre.app/install.yaml
```

### Option 2: The Installer Script
```bash
curl -sfL https://get.swarmsre.app | sh -
```

### Option 3: Helm OCI (Recommended for Production)
```bash
helm install swarmsre oci://ghcr.io/swarmsre/charts/swarmsre-server \
  --version 0.1.0 \
  --namespace swarmsre-system --create-namespace \
  --set config.databaseUrl="postgresql://user:pass@host:5432/db" \
  --set config.openaiApiKey="sk-..."
```

*(Note: The default `install.yaml` and script will provision a bundled PostgreSQL StatefulSet. For production, disable it and pass a `databaseUrl` via Helm).*

## 🛠️ Local Development

### 1. Prerequisites
- `uv` for Python package management
- Node.js 20+ for UI development

### 2. Build & Run
```bash
# 1. Build the React UI
cd ui && npm install && npm run build && cd ..

# 2. Run the FastAPI backend
cp .env.example .env
uv run uvicorn main:app --reload
```
Navigate to `http://localhost:8000` to view the SwarmSRE dashboard!

## 🧪 Testing

The platform includes a robust Pytest suite with end-to-end (E2E) flows and WebSocket integration tests.
```bash
PYTHONPATH=. uv run pytest tests/
```