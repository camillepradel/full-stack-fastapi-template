import { createFileRoute } from "@tanstack/react-router";
import * as d3 from "d3";
import { Suspense, useEffect, useMemo, useRef } from "react";
import { Container, Heading } from "@chakra-ui/react";
import { useSuspenseQuery } from "@tanstack/react-query";
import { DatasetContentPublic, DatasetsService, NodePublic, RelationPublic } from "../../client";
import { D3DragEvent } from "d3";

export const Route = createFileRoute("/_layout/graph_d3")({
  component: GraphD3,
});

interface GraphDisplayProps {
  dataset_content: DatasetContentPublic;
}

type NodeDatum = NodePublic & d3.SimulationNodeDatum;

type LinkDatum = RelationPublic & d3.SimulationLinkDatum<NodeDatum>

function GraphDisplay({ dataset_content }: GraphDisplayProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  const { nodes, links, nodeTypes, relationTypes } = useMemo(() => {
    const nodeTypes = Array.from(new Set(dataset_content.nodes.map(n => n.type)));
    const relationTypes = Array.from(new Set(dataset_content.relations.map(d => d.type)));
    const nodes = Array.from(
      dataset_content.nodes,
      n => ({
        id: n.id,
        type: n.type,
        x: 0,
        y: 0
      } as NodeDatum)
    );
    const links = dataset_content.relations.map(d => ({ ...d } as LinkDatum));
    return { nodes, links, nodeTypes, relationTypes };
  }, [dataset_content]);

  useEffect(() => {
    if (!svgRef.current) return;

    const width = 928;
    const height = 600;
    const nodeColor = d3.scaleOrdinal(nodeTypes, d3.schemeCategory10);
    const relationColor = d3.scaleOrdinal(relationTypes, d3.schemePastel1);

    // Clear existing content
    d3.select(svgRef.current).selectAll("*").remove();


    function linkArc(d: LinkDatum) {
      const sourceNode = d.source as NodeDatum;
      const targetNode = d.target as NodeDatum;
      const r = Math.hypot((targetNode.x ?? 0) - (sourceNode.x ?? 0), (targetNode.y ?? 0) - (sourceNode.y ?? 0));
      return `
        M${sourceNode.x ?? 0},${sourceNode.y ?? 0}
        A${r},${r} 0 0,1 ${targetNode.x ?? 0},${targetNode.y ?? 0}
      `;
    }

    const drag = (simulation: d3.Simulation<NodeDatum, LinkDatum>) => {
      function dragstarted(event: D3DragEvent<SVGGElement, NodeDatum, NodeDatum>, d: NodeDatum) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      }

      function dragged(event: D3DragEvent<SVGGElement, NodeDatum, NodeDatum>, d: NodeDatum) {
        d.fx = event.x;
        d.fy = event.y;
      }

      function dragended(event: D3DragEvent<SVGGElement, NodeDatum, NodeDatum>, d: NodeDatum) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      }

      return d3.drag<SVGGElement, NodeDatum>()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);
    };

    const svg = d3.select(svgRef.current)
      .attr("viewBox", [-width / 2, -height / 2, width, height])
      .attr("width", width)
      .attr("height", height)
      .attr("class", "max-w-full h-auto font-sans text-xs");

    const simulation = d3.forceSimulation<NodeDatum>(nodes)
      .force("link", d3.forceLink<NodeDatum, LinkDatum>(links).id(d => d.id))
      .force("charge", d3.forceManyBody().strength(-4000))
      .force("x", d3.forceX())
      .force("y", d3.forceY());

    // Create arrow markers
    const defs = svg.append("defs");
    relationTypes.forEach(type => {
      defs.append("marker")
        .attr("id", `arrow-${type}`)
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 15)
        .attr("refY", -0.5)
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("orient", "auto")
        .append("path")
        .attr("fill", relationColor(type))
        .attr("d", "M0,-5L10,0L0,5");
    });

    // Create links
    const link = svg.append("g")
      .attr("class", "links")
      .attr("fill", "none")
      .attr("stroke-width", 1.5)
      .selectAll("path")
      .data(links)
      .join("path")
      .attr("stroke", d => relationColor(d.type))
      .attr("marker-end", d => `url(${new URL(`#arrow-${d.type}`, location.href)})`);

    // Create nodes
    const node = svg.append("g")
      .attr("class", "nodes")
      .attr("stroke-linecap", "round")
      .attr("stroke-linejoin", "round")
      .selectAll<SVGGElement, NodeDatum>("g")
      .data(nodes)
      .join("g")
      .attr("fill", d => nodeColor(d.type))
      .call(drag(simulation) as any); // Type assertion needed due to D3's typing limitations

    node.append("circle")
      .attr("stroke", "white")
      .attr("stroke-width", 1.5)
      .attr("r", 4);

    node.append("text")
      .attr("x", 8)
      .attr("y", "0.31em")
      .text(d => d.id)
      .clone(true)
      .lower()
      .attr("fill", "none")
      .attr("stroke", "white")
      .attr("stroke-width", 3);

    simulation.on("tick", () => {
      link.attr("d", linkArc);
      node.attr("transform", d => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [nodes, links, relationTypes]);

  return <svg ref={svgRef} />;
}

// Separate data fetching component
function GraphContent() {
  const { data: dataset_content } = useSuspenseQuery({
    queryKey: ["datasets"],
    queryFn: () => DatasetsService.readDataset({ id: 3 }),
  });

  return <GraphDisplay dataset_content={dataset_content} />;
}


function GraphD3() {
  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        D3 graph
      </Heading>
      <Suspense fallback={<span>Loading graph...</span>}>
        <GraphContent />
      </Suspense>
    </Container>
  );
}

export default GraphD3;
