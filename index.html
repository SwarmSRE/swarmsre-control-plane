#!/bin/sh
set -e

# SwarmSRE Installation Script
# https://github.com/SwarmSRE/swarmsre-control-plane

GITHUB_REPO="SwarmSRE/swarmsre-control-plane"
MANIFEST_URL="https://get.swarmsre.app/install.yaml"

echo "=========================================================="
echo "🐝 Welcome to SwarmSRE - The AI Control Plane for Kubernetes"
echo "=========================================================="

if ! command -v kubectl >/dev/null 2>&1; then
    echo "Error: kubectl is required but not installed."
    exit 1
fi

NAMESPACE="swarmsre-system"

echo "1️⃣ Creating namespace '$NAMESPACE'..."
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

echo "2️⃣ Applying SwarmSRE manifests..."
kubectl apply -n "$NAMESPACE" -f "$MANIFEST_URL"

echo "3️⃣ Waiting for deployment to be ready..."
kubectl rollout status deployment/swarmsre-server -n "$NAMESPACE" --timeout=120s

echo ""
echo "✅ SwarmSRE successfully installed!"
echo ""
echo "To access the dashboard, run:"
echo "  kubectl port-forward svc/swarmsre-server -n $NAMESPACE 8000:8000"
echo "Then visit: http://localhost:8000"
echo "=========================================================="
