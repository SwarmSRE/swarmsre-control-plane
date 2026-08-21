export interface GraphNode {
  id: string;          // e.g., "deployment/payment-service"
  group: string;       // e.g., "kubernetes", "database", "external"
  status: string;      // e.g., "healthy", "degraded", "failed"
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

export interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  value: number;       // Represents traffic volume or dependency strength
}

export interface TopologyData {
  nodes: GraphNode[];
  links: GraphLink[];
}
