#!/bin/bash
set -e

echo "🚀 Deploying Payment Service Dummy App..."

cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
  namespace: demo
  labels:
    app: payment-service
spec:
  replicas: 1
  selector:
    matchLabels:
      app: payment-service
  template:
    metadata:
      labels:
        app: payment-service
    spec:
      containers:
      - name: payment-service
        image: nginx:alpine
        ports:
        - containerPort: 80
        resources:
          limits:
            memory: "128Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: payment-service
  namespace: demo
spec:
  selector:
    app: payment-service
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
EOF

echo "⏳ Waiting for Payment Service to be ready..."
kubectl wait --for=condition=Available=True deployment/payment-service -n demo --timeout=60s

echo "✅ Payment Service deployed successfully!"
