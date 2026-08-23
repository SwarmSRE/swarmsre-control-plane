import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { TopologyData } from './topology-data';

interface TopologyGraphProps {
  data: TopologyData;
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'running': return '#10B981';
    case 'failed': return '#EF4444';
    case 'warning': return '#F59E0B';
    case 'pending': return '#3B82F6';
    default: return '#64748B';
  }
};

const getKindIconUrl = (kind: string) => {
  switch (kind) {
    case 'Pod': return '/icons/icon-pod.svg';
    case 'Deployment': return '/icons/icon-deployment.svg';
    case 'ReplicaSet': return '/icons/icon-replicaset.svg';
    case 'Service': return '/icons/icon-service.svg';
    case 'PersistentVolumeClaim': return '/icons/icon-pvc.svg';
    default: return '/icons/icon-default.svg';
  }
};

const layerMap: Record<string, number> = {
  'Service': 0,
  'Ingress': 0,
  'Deployment': 1,
  'ReplicaSet': 2,
  'Pod': 3,
  'PersistentVolumeClaim': 4,
  'ConfigMap': 4,
  'Secret': 4
};

export const TopologyGraph: React.FC<TopologyGraphProps> = ({ data }) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || !data || !Array.isArray(data.nodes) || data.nodes.length === 0) return;

    const height = 600;

    // Deep clone data
    const nodes = data.nodes.map(d => {
      const n = { ...d };
      // Fix X position based on hierarchy layer
      const layer = layerMap[n.kind || 'Pod'] ?? 3;
      n.x = 100 + layer * 200; 
      n.fx = n.x; // Lock X coordinate
      return n;
    });
    
    // We need to map string IDs to object references for d3 links
    const nodeById = new Map(nodes.map(n => [n.id, n]));
    const links = data.links.map(d => ({
      source: typeof d.source === 'string' ? nodeById.get(d.source) : d.source,
      target: typeof d.target === 'string' ? nodeById.get(d.target) : d.target,
    })).filter(l => l.source && l.target);

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // Zoom container
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 3])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });

    svg.call(zoom);
    
    // Create the 'g' element BEFORE applying the initial zoom, 
    // because zoom.transform triggers the zoom event synchronously!
    const g = svg.append("g");

    // Set initial zoom to fit
    svg.call(zoom.transform, d3.zoomIdentity.translate(50, 50).scale(0.8));

    // Defs for arrows & filters
    const defs = svg.append("defs");
    
    defs.append("marker")
      .attr("id", "arrow")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 25) // Offset to not overlap node
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("fill", "#475569")
      .attr("d", "M0,-5L10,0L0,5");

    const filter = defs.append("filter")
      .attr("id", "glow-red")
      .attr("x", "-50%").attr("y", "-50%").attr("width", "200%").attr("height", "200%");
    filter.append("feGaussianBlur").attr("stdDeviation", "8").attr("result", "blur");
    filter.append("feComposite").attr("in", "SourceGraphic").attr("in2", "blur").attr("operator", "over");

    // Simulation (only for Y coordinate spacing)
    const simulation = d3.forceSimulation(nodes as any)
      .force("y", d3.forceY(height / 2).strength(0.05))
      .force("collide", d3.forceCollide().radius(40)) // Prevent Y overlap
      .stop(); // run synchronously

    // Run simulation purely to calculate Y coordinates statically
    for (let i = 0; i < 150; i++) simulation.tick();

    // Links (Bezier curves for hierarchical look)
    const link = g.append("g")
      .attr("fill", "none")
      .attr("stroke", "#334155")
      .attr("stroke-width", 2)
      .selectAll("path")
      .data(links)
      .join("path")
      .attr("marker-end", "url(#arrow)")
      .attr("d", (d: any) => {
        const dx = d.target.x - d.source.x,
              dy = d.target.y - d.source.y,
              dr = Math.sqrt(dx * dx + dy * dy) * 1.5;
        return `M${d.source.x},${d.source.y}A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`;
      })
      .attr("class", "transition-all duration-300 ease-in-out");

    // Nodes
    const node = g.append("g")
      .selectAll("g")
      .data(nodes)
      .join("g")
      .attr("transform", (d: any) => `translate(${d.x},${d.y})`)
      .attr("cursor", "pointer")
      // Hover effects
      .on("mouseenter", function(event: any, d: any) {
        // Elevate node with glow
        d3.select(event.currentTarget).select("rect")
          .transition().duration(200)
          .attr("stroke", "#00F0FF")
          .attr("stroke-width", 3)
          .attr("filter", "url(#glow-red)"); // Reuse glow filter for highlight
          
        d3.select(event.currentTarget)
          .transition().duration(200)
          .attr("transform", `translate(${d.x},${d.y - 4})`); // Lift up slightly

        // Highlight connected links
        link.attr("stroke", (l: any) => 
          l.source.id === d.id || l.target.id === d.id ? "#00F0FF" : "#1E293B"
        ).attr("stroke-width", (l: any) => 
          l.source.id === d.id || l.target.id === d.id ? 3 : 1
        ).style("opacity", (l: any) => 
          l.source.id === d.id || l.target.id === d.id ? 1 : 0.3
        );
      })
      .on("mouseleave", function(event: any, d: any) {
        d3.select(event.currentTarget).select("rect")
          .transition().duration(200)
          .attr("stroke", (n: any) => getStatusColor(n.status))
          .attr("stroke-width", 2.5)
          .attr("filter", (n: any) => n.status === 'failed' ? "url(#glow-red)" : null);
          
        d3.select(event.currentTarget)
          .transition().duration(200)
          .attr("transform", `translate(${d.x},${d.y})`);

        // Reset links
        link.attr("stroke", "#334155")
            .attr("stroke-width", 2)
            .style("opacity", 1);
      });

    // Node Box
    node.append("rect")
      .attr("x", -20)
      .attr("y", -20)
      .attr("width", 40)
      .attr("height", 40)
      .attr("rx", 10) // More rounded corners
      .attr("fill", "#0B1120")
      .attr("stroke", (d: any) => getStatusColor(d.status))
      .attr("stroke-width", 2.5)
      .attr("filter", (d: any) => d.status === 'failed' ? "url(#glow-red)" : null)
      .attr("class", "transition-all duration-300");

    // Node Icon
    node.append("image")
      .attr("href", (d: any) => getKindIconUrl(d.kind))
      .attr("x", -12)
      .attr("y", -12)
      .attr("width", 24)
      .attr("height", 24);

    // Label Text
    node.append("text")
      .attr("dy", 35)
      .attr("text-anchor", "middle")
      .attr("fill", "#F8FAFC")
      .attr("font-size", "12px")
      .attr("font-weight", "600")
      .attr("font-family", "var(--font-sans)")
      .attr("class", "pointer-events-none")
      .text((d: any) => d.label);

    // Sub-info (e.g. "3/3 Ready")
    node.append("text")
      .attr("dy", 50)
      .attr("text-anchor", "middle")
      .attr("fill", (d: any) => getStatusColor(d.status))
      .attr("font-size", "10px")
      .attr("font-family", "var(--font-sans)")
      .attr("class", "pointer-events-none")
      .text((d: any) => d.info || d.kind);

  }, [data]);

  return (
    <div className="w-full h-full relative border border-[#1E293B]/50 rounded-xl overflow-hidden shadow-[0_0_40px_rgba(0,0,0,0.5)]">
      <div className="absolute top-4 left-4 z-10 flex gap-2">
        <div className="glass-panel rounded-lg px-3 py-1.5 text-xs text-[#E2E8F0] font-medium flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#10B981] shadow-[0_0_8px_#10B981]"></span> Running
        </div>
        <div className="glass-panel rounded-lg px-3 py-1.5 text-xs text-[#E2E8F0] font-medium flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#F59E0B] shadow-[0_0_8px_#F59E0B]"></span> Warning
        </div>
        <div className="glass-panel rounded-lg px-3 py-1.5 text-xs text-[#E2E8F0] font-medium flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#EF4444] shadow-[0_0_8px_#EF4444] animate-pulse"></span> Failed
        </div>
      </div>
      <svg
        ref={svgRef}
        className="w-full h-full bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-[#1E293B]/20 via-[#0B1120] to-[#0B1120]"
        style={{ cursor: 'grab' }}
      />
    </div>
  );
};
