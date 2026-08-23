import * as d3 from 'd3';

const svg = d3.select(document.createElement('svg'));

const zoom = d3.zoom()
  .on("zoom", (event) => {
    g.attr("transform", event.transform);
  });

svg.call(zoom);
svg.call(zoom.transform, d3.zoomIdentity.translate(50, 50).scale(0.8));

const g = svg.append("g");
