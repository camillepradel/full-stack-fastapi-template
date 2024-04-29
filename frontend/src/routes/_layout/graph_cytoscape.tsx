import { createFileRoute } from "@tanstack/react-router"

import cytoscape from 'cytoscape';
import { useEffect, useRef } from "react";
import { Box, Container, Heading } from "@chakra-ui/react";

export const Route = createFileRoute("/_layout/graph_cytoscape")({
  component: GraphCytoscape,
})


function GraphDisplay() {
  const ref = useRef()
  useEffect(() => {
    cytoscape({
      container: ref.current,

      elements: {
        nodes: [
          {
            data: { id: 'a' }
          },

          {
            data: { id: 'b' }
          }
        ],
        edges: [
          {
            data: { id: 'ab', source: 'a', target: 'b' }
          }
        ]
      },

      layout: {
        name: 'grid',
        rows: 1
      },

      // so we can see the ids
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(id)'
          }
        }
      ]
    });
  }, [])
  return (
    <Box height={300} ref={ref} />
  )
}


function GraphCytoscape() {
  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        Cytoscape.js graph
      </Heading>
      <GraphDisplay />
    </Container>
  )
}
