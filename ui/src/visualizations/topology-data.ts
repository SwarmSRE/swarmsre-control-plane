export interface GraphNode {
  id: string;
  label: string;
  kind: 'Namespace' | 'Deployment' | 'ReplicaSet' | 'Pod' | 'Service' | 
        'Ingress' | 'PersistentVolumeClaim' | 'ConfigMap' | 'Secret';
  status: 'running' | 'failed' | 'warning' | 'pending' | 'unknown';
  namespace?: string;
  info?: string;
  // d3 DAG properties
  x?: number;
  y?: number;
  // Legacy d3 force properties (might still be used internally by some d3 logic depending on implementation)
  fx?: number | null;
  fy?: number | null;
}

export interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  value?: number;
}

export interface TopologyData {
  nodes: GraphNode[];
  links: GraphLink[];
}
