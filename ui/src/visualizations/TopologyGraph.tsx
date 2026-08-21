import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { TopologyData, GraphNode, GraphLink } from './topology-data';

interface TopologyGraphProps {
  data: TopologyData;
}

function useForceGraph(data: TopologyData, width: number, height: number) {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [links, setLinks] = useState<GraphLink[]>([]);
  
  // Clone data to avoid mutating props, D3 modifies the objects directly
  const simulationData = useRef({
    nodes: data.nodes.map(d => ({ ...d })),
    links: data.links.map(d => ({ ...d }))
  });

  useEffect(() => {
    // Re-clone if data changes significantly (for simplicity, assuming data could update)
    simulationData.current = {
      nodes: data.nodes.map(d => ({ ...d })),
      links: data.links.map(d => ({ ...d }))
    };

    const sim = d3.forceSimulation(simulationData.current.nodes as d3.SimulationNodeDatum[])
      .force("link", d3.forceLink(simulationData.current.links).id((d: any) => d.id).distance(120))
      .force("charge", d3.forceManyBody().strength(-400))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(40))
      .on("tick", () => {
        // Trigger React re-render with new positions
        setNodes([...simulationData.current.nodes]);
        setLinks([...simulationData.current.links]);
      });

    return () => {
      sim.stop(); // Clean up on unmount
    };
  }, [data, width, height]);

  return { nodes, links };
}

export const TopologyGraph: React.FC<TopologyGraphProps> = ({ data }) => {
  const width = 800;
  const height = 600;
  const { nodes, links } = useForceGraph(data, width, height);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'failed': return 'var(--status-red)';
      case 'degraded': return 'var(--status-yellow)';
      case 'healthy': return 'var(--status-green)';
      default: return 'var(--text-muted)';
    }
  };

  return (
    <div style={{ width: "100%", height: "100%", position: 'relative' }}>
      <svg 
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid meet"
        style={{ width: "100%", height: "100%" }}
      >
        <defs>
          <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Links */}
        <g stroke="var(--border-subtle)" strokeOpacity={0.6}>
          {links.map((link, i) => {
            const source = link.source as GraphNode;
            const target = link.target as GraphNode;
            // D3 sets x/y on the nodes, but types require fallback
            const x1 = source.x ?? 0;
            const y1 = source.y ?? 0;
            const x2 = target.x ?? 0;
            const y2 = target.y ?? 0;

            return (
              <line
                key={`link-${i}`}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                strokeWidth={Math.sqrt(link.value)}
              />
            );
          })}
        </g>

        {/* Nodes */}
        <g stroke="#fff" strokeWidth={1.5}>
          {nodes.map(node => (
            <g key={node.id} transform={`translate(${node.x ?? 0},${node.y ?? 0})`}>
              <circle
                r={16}
                fill={getStatusColor(node.status)}
                stroke="var(--bg-primary)"
                strokeWidth={3}
                filter={node.status !== 'healthy' ? "url(#glow)" : ""}
              />
              <text
                dy={28}
                textAnchor="middle"
                fill="var(--text-primary)"
                stroke="none"
                fontSize="12px"
                fontWeight="500"
              >
                {node.id}
              </text>
              <text
                dy={42}
                textAnchor="middle"
                fill="var(--text-muted)"
                stroke="none"
                fontSize="10px"
              >
                {node.group}
              </text>
            </g>
          ))}
        </g>
      </svg>
    </div>
  );
};
