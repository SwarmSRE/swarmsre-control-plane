import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { TopologyData, GraphNode } from './topology-data';

interface TopologyGraphProps {
  data: TopologyData;
}

// Function to generate a hexagon path
const getHexagonPath = (radius: number) => {
  const points = [];
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 180) * (60 * i - 30); // Pointy top hexagon
    const x = radius * Math.cos(angle);
    const y = radius * Math.sin(angle);
    points.push(`${x},${y}`);
  }
  return `M${points.join('L')}Z`;
};

export const TopologyGraph: React.FC<TopologyGraphProps> = ({ data }) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || !data) return;

    const width = 800;
    const height = 600;

    // Deep clone data because d3 mutates it
    const nodes: d3.SimulationNodeDatum[] & GraphNode[] = data.nodes.map(d => ({ ...d }));
    const links: d3.SimulationLinkDatum<d3.SimulationNodeDatum & GraphNode>[] = data.links.map(d => ({ ...d }));

    const svg = d3.select(svgRef.current)
      .attr("viewBox", `0 0 ${width} ${height}`)
      .attr("preserveAspectRatio", "xMidYMid meet");

    svg.selectAll("*").remove(); // Clear previous renders

    // Define defs and filters
    const defs = svg.append("defs");

    // Glow filter for critical nodes
    const filter = defs.append("filter")
      .attr("id", "glow")
      .attr("x", "-50%")
      .attr("y", "-50%")
      .attr("width", "200%")
      .attr("height", "200%");

    filter.append("feGaussianBlur")
      .attr("stdDeviation", "4")
      .attr("result", "blur");
    
    filter.append("feComposite")
      .attr("in", "SourceGraphic")
      .attr("in2", "blur")
      .attr("operator", "over");

    // Simulation
    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d: any) => d.id).distance(120))
      .force("charge", d3.forceManyBody().strength(-400))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(50));

    // Links container
    const link = svg.append("g")
      .attr("stroke", "#1E293B")
      .attr("stroke-opacity", 0.8)
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke-width", (d: any) => Math.sqrt(d.value as number));

    // Nodes container
    const node = (svg.append("g")
      .selectAll("g")
      .data(nodes)
      .join("g") as any)
      .call(d3.drag<SVGGElement, any>()
        .on("start", (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on("drag", (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on("end", (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
      );

    const getStatusColor = (status: string) => {
      switch (status) {
        case 'failed': return '#EF4444'; // critical-red
        case 'degraded': return '#F59E0B'; // warning-yellow
        case 'healthy': return '#10B981'; // healthy-green
        default: return '#94A3B8';
      }
    };

    // Draw hexagons
    node.append("path")
      .attr("d", getHexagonPath(22))
      .attr("fill", (d: any) => `${getStatusColor(d.status)}33`) // 20% opacity background
      .attr("stroke", (d: any) => getStatusColor(d.status))
      .attr("stroke-width", 2)
      .attr("filter", (d: any) => d.status === 'failed' ? "url(#glow)" : null)
      .classed("pulse-failed", (d: any) => d.status === 'failed'); // We'll add this class in global CSS or handle it in inline style if possible. Wait, tailwind animate-pulse might not work perfectly on SVG paths without setting it in class. We'll add a class.
      
    // Applying Tailwind's animate-pulse to failed nodes
    node.selectAll("path.pulse-failed")
      .attr("class", "animate-pulse");

    // Labels
    node.append("text")
      .attr("dy", 38)
      .attr("text-anchor", "middle")
      .attr("fill", "#F8FAFC")
      .attr("font-size", "12px")
      .attr("font-weight", "600")
      .text((d: any) => d.id);

    node.append("text")
      .attr("dy", 52)
      .attr("text-anchor", "middle")
      .attr("fill", "#94A3B8")
      .attr("font-size", "10px")
      .text((d: any) => d.group);

    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [data]);

  return (
    <div className="w-full h-full relative">
      <svg
        ref={svgRef}
        className="w-full h-full bg-[#0B1120] rounded-lg"
      />
    </div>
  );
};
