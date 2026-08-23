import random

from fastapi import APIRouter

router = APIRouter(prefix="/api/topology", tags=["topology"])

@router.get("")
async def get_topology():
    """
    Returns mock topology data representing a hierarchical Kubernetes architecture
    (Service -> Deployment -> ReplicaSet -> Pod -> PVC) for the dashboard visualization.
    """
    nodes = [
        {"id": "svc/payment-service",     "label": "payment-service",     "kind": "Service",    "status": "running", "namespace": "payment"},
        {"id": "deploy/payment-service",  "label": "payment-service",     "kind": "Deployment", "status": "warning", "namespace": "payment", "info": "2/3 available"},
        {"id": "rs/payment-service-abc",  "label": "payment-service-abc", "kind": "ReplicaSet", "status": "warning", "namespace": "payment"},
        {"id": "pod/payment-svc-abc-1",   "label": "payment-svc-abc-1",   "kind": "Pod",        "status": "running", "namespace": "payment"},
        {"id": "pod/payment-svc-abc-2",   "label": "payment-svc-abc-2",   "kind": "Pod",        "status": "failed",  "namespace": "payment", "info": "CrashLoopBackOff"},
        {"id": "pod/payment-svc-abc-3",   "label": "payment-svc-abc-3",   "kind": "Pod",        "status": "warning", "namespace": "payment", "info": "Restarts: 5"},
        {"id": "pvc/payment-data",        "label": "payment-data",        "kind": "PersistentVolumeClaim", "status": "running", "namespace": "payment"},
        
        {"id": "svc/auth-service",        "label": "auth-service",        "kind": "Service",    "status": "running", "namespace": "auth"},
        {"id": "deploy/auth-service",     "label": "auth-service",        "kind": "Deployment", "status": "running", "namespace": "auth"},
        {"id": "rs/auth-service-xyz",     "label": "auth-service-xyz",    "kind": "ReplicaSet", "status": "running", "namespace": "auth"},
        {"id": "pod/auth-svc-xyz-1",      "label": "auth-svc-xyz-1",      "kind": "Pod",        "status": "running", "namespace": "auth"},
        {"id": "pod/auth-svc-xyz-2",      "label": "auth-svc-xyz-2",      "kind": "Pod",        "status": "running", "namespace": "auth"},
    ]

    links = [
        {"source": "svc/payment-service",    "target": "deploy/payment-service"},
        {"source": "deploy/payment-service", "target": "rs/payment-service-abc"},
        {"source": "rs/payment-service-abc", "target": "pod/payment-svc-abc-1"},
        {"source": "rs/payment-service-abc", "target": "pod/payment-svc-abc-2"},
        {"source": "rs/payment-service-abc", "target": "pod/payment-svc-abc-3"},
        {"source": "pod/payment-svc-abc-1",  "target": "pvc/payment-data"},
        {"source": "pod/payment-svc-abc-2",  "target": "pvc/payment-data"},
        {"source": "pod/payment-svc-abc-3",  "target": "pvc/payment-data"},
        
        {"source": "svc/auth-service",       "target": "deploy/auth-service"},
        {"source": "deploy/auth-service",    "target": "rs/auth-service-xyz"},
        {"source": "rs/auth-service-xyz",    "target": "pod/auth-svc-xyz-1"},
        {"source": "rs/auth-service-xyz",    "target": "pod/auth-svc-xyz-2"},
        
        # Inter-service dependency
        {"source": "deploy/payment-service", "target": "svc/auth-service"},
    ]

    return {
        "nodes": nodes,
        "links": links
    }
