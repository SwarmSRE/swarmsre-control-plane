import random

from fastapi import APIRouter

router = APIRouter(prefix="/api/topology", tags=["topology"])

@router.get("")
async def get_topology():
    """
    Returns the current cluster topology (nodes and links) for the D3.js visualization.
    For MVP, this returns a static/mock representation of a typical microservices architecture.
    """
    # Mock microservices topology
    nodes = [
        {"id": "ingress-gateway", "group": "gateway", "status": "healthy"},
        {"id": "frontend-app", "group": "frontend", "status": "healthy"},
        {"id": "auth-service", "group": "backend", "status": "healthy"},
        {"id": "payment-service", "group": "backend", "status": "degraded"},
        {"id": "inventory-service", "group": "backend", "status": "healthy"},
        {"id": "shipping-service", "group": "backend", "status": "healthy"},
        {"id": "user-db", "group": "database", "status": "healthy"},
        {"id": "payment-db", "group": "database", "status": "failed"},
        {"id": "inventory-db", "group": "database", "status": "healthy"},
        {"id": "redis-cache", "group": "cache", "status": "healthy"},
        {"id": "stripe-api", "group": "external", "status": "healthy"},
    ]

    links = [
        {"source": "ingress-gateway", "target": "frontend-app", "value": 10},
        {"source": "frontend-app", "target": "auth-service", "value": 5},
        {"source": "frontend-app", "target": "payment-service", "value": 8},
        {"source": "frontend-app", "target": "inventory-service", "value": 6},
        {"source": "frontend-app", "target": "shipping-service", "value": 3},
        
        {"source": "auth-service", "target": "user-db", "value": 5},
        {"source": "auth-service", "target": "redis-cache", "value": 8},
        
        {"source": "payment-service", "target": "payment-db", "value": 8},
        {"source": "payment-service", "target": "stripe-api", "value": 2},
        {"source": "payment-service", "target": "auth-service", "value": 4},
        
        {"source": "inventory-service", "target": "inventory-db", "value": 6},
        {"source": "inventory-service", "target": "redis-cache", "value": 4},
        
        {"source": "shipping-service", "target": "inventory-service", "value": 2},
    ]

    # In a real system, the status would be dynamically computed based on active incidents
    # For now, we inject some random jitter to simulate live traffic
    for link in links:
        link["value"] = max(1, link["value"] + random.randint(-1, 2))

    return {
        "nodes": nodes,
        "links": links
    }
