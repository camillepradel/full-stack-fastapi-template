import { createFileRoute } from "@tanstack/react-router";
import * as d3 from "d3";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Button, Container, Heading } from "@chakra-ui/react";
import { useSuspenseQuery } from "@tanstack/react-query";
import { DatasetContent, DatasetsService, Node, OpenAPI, Relation } from "../../client";
import { D3DragEvent } from "d3";
import { getProperty } from "dot-prop";

export const Route = createFileRoute("/_layout/graph_d3")({
  component: GraphD3,
});

interface GraphDisplayProps {
  dataset_content: DatasetContent;
  someNodeFrozen: boolean;
  setSomeNodeFrozen: (someNodeFrozen: boolean) => void;
}

type NodeDatum = Node & d3.SimulationNodeDatum;

type LinkDatum = Relation & d3.SimulationLinkDatum<NodeDatum>

function GraphDisplay({ dataset_content, someNodeFrozen, setSomeNodeFrozen }: GraphDisplayProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  const { nodes, links, nodeTypes, relationTypes } = useMemo(() => {
    const nodeTypes = Array.from(new Set(dataset_content.nodes.map(n => n.type)));
    const relationTypes = Array.from(new Set(dataset_content.relations.map(d => d.type)));
    const nodes = dataset_content.nodes.map(d => ({ ...d, x: 0, y: 0 } as NodeDatum));
    const links = dataset_content.relations.map(d => ({ ...d } as LinkDatum));
    return { nodes, links, nodeTypes, relationTypes };
  }, [dataset_content]);

  useEffect(() => {
    if (!svgRef.current) return;

    const width = 928;
    const height = 600;
    const nodeColor = d3.scaleOrdinal(nodeTypes, d3.schemeCategory10);
    const relationColor = d3.scaleOrdinal(relationTypes, d3.schemePastel1);
    const metadata = dataset_content.metadata

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

    const getNodeIcon = (d: NodeDatum) => {
      const node_icons = metadata?.graph_display_specifications?.node_icons
      let icon = (node_icons? (node_icons[d.type] || node_icons["*"]) : null) || "Icon-round-Question_mark.svg.png";
      return OpenAPI.BASE + "/static/" + icon
    }


    const getDisplayLabel = (d: NodeDatum) => {
      let candidate_fields = ["data.name", "data.label", "data.id", "id"]
      if (metadata?.graph_display_specifications?.node_label_field_name) {
        candidate_fields.unshift(metadata.graph_display_specifications.node_label_field_name)
      }
      for (const candidate_field of candidate_fields) {
        const label = getProperty(d, candidate_field)
        if (label) {
          return label
        }
      }
      return d.id
    }

    const displayNode = (node: d3.Selection<SVGGElement, NodeDatum, SVGGElement, unknown>) => {
      if (metadata?.graph_display_specifications?.node_icons)
        node.append("image")
          .attr("xlink:href", getNodeIcon)
          .attr("width", 40)
          .attr("height", 40)
          .attr("x", -20)
          .attr("y", -20);
      else
        node.append("circle")
          .attr("fill", d => nodeColor(d.type))
          .attr("stroke", "white")
          .attr("stroke-width", 1.5)
          .attr("r", 4);

      node.append("text")
        .attr("x", 8)
        .attr("y", "0.31em")
        .text(getDisplayLabel)
        .attr("stroke", "white")
        .attr("stroke-width", 3)
        .clone(true)
        .attr("fill", "black")
        .attr("stroke", "none")
        .attr("stroke-width", 1);

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

      function dragended(event: D3DragEvent<SVGGElement, NodeDatum, NodeDatum>, _d: NodeDatum) {
        if (!event.active) simulation.alphaTarget(0);
        setSomeNodeFrozen(true);
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
      .force("charge", d3.forceManyBody().strength(-1000))
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
      .call(drag(simulation) as any) // Type assertion needed due to D3's typing limitations
      .call(displayNode);

    simulation.on("tick", () => {
      link.attr("d", linkArc);
      node.attr("transform", d => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [nodes, links, relationTypes]);

  function unfreezeNodes() {
    for (const node of nodes) {
      node.fx = null;
      node.fy = null;
    }
  }

  useEffect(() => {
    if (!someNodeFrozen) {
      unfreezeNodes();
    }
  }, [someNodeFrozen])

  return <svg ref={svgRef} />;
}

// Handles data fetching, controls and calls GraphDisplay component
function Graph() {
  const { data: dataset_content } = useSuspenseQuery({
    queryKey: ["dataset-content"],
    queryFn: () => DatasetsService.readDatasetContent({ id: 1 }),
  });

  const [someNodeFrozen, setSomeNodeFrozen] = useState(false);

  const unfreezeNodes = () => {
    setSomeNodeFrozen(false)
  }

  return (
    <div>
      <GraphDisplay dataset_content={dataset_content} someNodeFrozen={someNodeFrozen} setSomeNodeFrozen={setSomeNodeFrozen} />
      <Button isDisabled={!someNodeFrozen} onClick={unfreezeNodes}>Unfreeze nodes</Button>
    </div>
  );
}


function GraphD3() {
  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        D3 graph
      </Heading>
      <Suspense fallback={<span>Loading graph...</span>}>
        <Graph />
      </Suspense>
    </Container>
  );
}

export default GraphD3;
