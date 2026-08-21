#!/bin/bash
# reset-demo.sh - Restores the Payment Service

set -e

echo "🧹 Cleaning up chaos..."
# Restore the working image
kubectl patch deployment payment-service -n demo --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/image", "value":"nginx:alpine"}]'

# Delete any chaos mesh objects if they exist
kubectl delete networkchaos --all -n demo 2>/dev/null || true
kubectl delete podchaos --all -n demo 2>/dev/null || true

echo "⏳ Waiting for Payment Service to recover..."
kubectl wait --for=condition=Available=True deployment/payment-service -n demo --timeout=60s
echo "✅ Environment reset successfully!"
