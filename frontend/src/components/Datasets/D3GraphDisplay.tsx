import * as d3 from "d3";
import { useEffect, useMemo, useRef, useState } from "react";
import { Node, OpenAPI, Relation } from "../../client";
import { D3DragEvent } from "d3";
import { getProperty } from "dot-prop";
import { GraphDisplayProps } from "./GraphDisplayProps";
import { Box, Flex, Text, IconButton, VStack, Heading } from "@chakra-ui/react";
import { CloseIcon } from "@chakra-ui/icons";

type NodeDatum = Node & d3.SimulationNodeDatum;

type LinkDatum = Relation & d3.SimulationLinkDatum<NodeDatum>

const GRAPH_HEIGHT = 600;
const GRAPH_DEFAULT_WIDTH = 928;
const LINK_INIT_STROKE_WIDTH = 1.5;

type SelectedItem = {
  type: 'node' | 'link';
  data: NodeDatum | LinkDatum;
} | null;

const PropertiesPane = ({ item, onClose }: { item: SelectedItem; onClose: () => void }) => {
  if (!item) return null;

  const data = item.data.data || {};

  return (
    <Box
      position="absolute"
      bottom="4"
      right="4"
      bg="white"
      p="4"
      borderRadius="lg"
      boxShadow="lg"
      borderWidth="1px"
      maxW="md"
    >
      <Flex justify="space-between" align="center" mb="2">
        <Heading size="sm">{item.type === 'node' ? 'Node' : 'Link'} Properties</Heading>
        <IconButton
          icon={<CloseIcon />}
          onClick={onClose}
          aria-label="Close"
          size="sm"
          variant="ghost"
        />
      </Flex>
      <VStack spacing="0.5" align="stretch">
        {Object.entries(data).map(([key, value]) => (
          <Flex key={key}>
            <Text fontWeight="medium" mr="2">{key}:</Text>
            <Text>{String(value)}</Text>
          </Flex>
        ))}
      </VStack>
    </Box>
  );
};

function D3GraphDisplay({ dataset_content, someNodeFrozen, setSomeNodeFrozen }: GraphDisplayProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedItem, setSelectedItem] = useState<SelectedItem>(null);

  const { nodes, links, nodeTypes, relationTypes } = useMemo(() => {
    const nodeTypes = Array.from(new Set(dataset_content.nodes.map(n => n.type)));
    const relationTypes = Array.from(new Set(dataset_content.relations.map(d => d.type)));
    const nodes = dataset_content.nodes.map(d => ({ ...d, x: 0, y: 0 } as NodeDatum));
    const links = dataset_content.relations.map(d => ({ ...d } as LinkDatum));
    return { nodes, links, nodeTypes, relationTypes };
  }, [dataset_content]);

  useEffect(() => {
    if (!svgRef.current) return;

    const width = svgRef.current?.parentElement?.clientWidth || GRAPH_DEFAULT_WIDTH;
    const height = svgRef.current?.parentElement?.clientHeight || GRAPH_HEIGHT;
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
      let icon = (node_icons ? (node_icons[d.type] || node_icons["*"]) : null) || "Icon-round-Question_mark.svg.png";
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
      .attr("width", "100%")
      .attr("height", "100%")
      .style("font-family", "inherit")
      .style("font-size", "0.75rem")
      .on("click", (event) => {
        // Close properties pane when clicking on empty space
        if (event.target === svgRef.current) {
          setSelectedItem(null);
        }
      });

    // Create a container group for zooming
    const container = svg.append("g");

    const simulation = d3.forceSimulation<NodeDatum>(nodes)
      .force("link", d3.forceLink<NodeDatum, LinkDatum>(links).id(d => d.id))
      .force("charge", d3.forceManyBody().strength(-1000))
      .force("x", d3.forceX())
      .force("y", d3.forceY());

    // Create arrow markers
    const defs = container.append("defs");
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
    const link = container.append("g")
      .attr("class", "links")
      .attr("fill", "none")
      .selectAll("path")
      .data(links)
      .join("path")
      .attr("stroke", d => relationColor(d.type))
      .attr("stroke-width", LINK_INIT_STROKE_WIDTH)
      .attr("marker-end", d => `url(${new URL(`#arrow-${d.type}`, location.href)})`)
      .on("click", (event, d) => {
        event.stopPropagation();
        setSelectedItem({ type: 'link', data: d });
      });

    // Create nodes
    const node = container.append("g")
      .attr("class", "nodes")
      .attr("stroke-linecap", "round")
      .attr("stroke-linejoin", "round")
      .selectAll<SVGGElement, NodeDatum>("g")
      .data(nodes)
      .join("g")
      .call(drag(simulation) as any)
      .call(displayNode)
      .on("click", (event, d) => {
        event.stopPropagation();
        setSelectedItem({ type: 'node', data: d });
      });

    simulation.on("tick", () => {
      link.attr("d", linkArc);
      node.attr("transform", d => `translate(${d.x},${d.y})`);
    });

    // Add zoom and pan behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 10])
      .on("zoom", (event) => {
        container.attr("transform", event.transform);
        // Make nodes, labels and edges scale as well, but not as much as the graph
        const graphElementsScale = 1 / (1 + (event.transform.k-1) / 2 || 1);
        node.selectAll("text").attr("transform", `scale(${graphElementsScale})`);
        node.selectAll("image").attr("transform", `scale(${graphElementsScale})`);
        node.selectAll("circle").attr("transform", `scale(${graphElementsScale})`);
        link.classed("plop", true);
        link.attr("stroke-width", LINK_INIT_STROKE_WIDTH*graphElementsScale);
      });

    svg.call(zoom);

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

  return (
    <Box position="relative" width="100%" height={GRAPH_HEIGHT}>
      <svg ref={svgRef}></svg>
      <PropertiesPane item={selectedItem} onClose={() => setSelectedItem(null)} />
    </Box>
  );
}

export default D3GraphDisplay;
export { GRAPH_HEIGHT };
