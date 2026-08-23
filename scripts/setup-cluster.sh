#!/bin/bash
set -e

CLUSTER_NAME="swarmsre-cluster"

if kind get clusters | grep -q "^${CLUSTER_NAME}\$"; then
    echo "Cluster ${CLUSTER_NAME} already exists. Skipping creation."
else
    echo "Creating KinD cluster..."
    kind create cluster --name ${CLUSTER_NAME} --config scripts/kind-config.yaml
fi

echo "Installing NGINX Ingress..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

echo "Waiting for Ingress to be ready (this may take a minute)..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s

echo "Creating swarmsre-system namespace..."
kubectl create namespace swarmsre-system --dry-run=client -o yaml | kubectl apply -f -

echo "Cluster setup complete! 🎉"
