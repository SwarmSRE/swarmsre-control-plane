#!/bin/bash
# inject-faults.sh - Triggers a CrashLoopBackOff

set -e

echo "🚀 Injecting Chaos: Breaking the Payment Service..."
# Apply a broken configuration (bad image tag) to cause ImagePullBackOff / CrashLoopBackOff
kubectl patch deployment payment-service -n demo --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/image", "value":"nginx:broken-tag"}]'

echo "⏳ Waiting for deployment failure..."
kubectl wait --for=condition=Available=False deployment/payment-service -n demo --timeout=30s || true

echo "💥 Chaos injected successfully! The SwarmSRE agent should detect this shortly."
