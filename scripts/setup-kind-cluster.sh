#!/bin/bash
set -e

CLUSTER_NAME="swarmsre-demo"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if kind get clusters | grep -q "^${CLUSTER_NAME}\$"; then
    echo "✅ Cluster ${CLUSTER_NAME} already exists. Skipping creation."
else
    echo "🚀 Creating KinD cluster: ${CLUSTER_NAME}..."
    kind create cluster --name ${CLUSTER_NAME} --config "${DIR}/kind-config.yaml"
fi

echo "📦 Installing NGINX Ingress Controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

echo "⏳ Waiting for NGINX Ingress to be ready..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s

echo "📁 Creating swarmsre-system namespace..."
kubectl create namespace swarmsre-system --dry-run=client -o yaml | kubectl apply -f -

echo "📁 Creating demo namespace..."
kubectl create namespace demo --dry-run=client -o yaml | kubectl apply -f -

echo "🎉 Cluster setup complete!"
