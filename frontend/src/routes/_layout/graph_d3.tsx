import { createFileRoute } from "@tanstack/react-router"

import * as d3 from "d3";
import { useEffect, useRef } from "react";
import { Container, Heading } from "@chakra-ui/react";

export const Route = createFileRoute("/_layout/graph_d3")({
  component: GraphD3,
})


function GraphDisplay() {
  const ref = useRef<SVGSVGElement>(null)
  useEffect(() => {
    const svgElement = d3.select(ref.current)
    svgElement.append("circle")
      .attr("cx", 150)
      .attr("cy", 70)
      .attr("r", 50)
  }, [])
  return (
    <svg ref={ref} />
  )
}


function GraphD3() {
  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        D3 graph
      </Heading>
      <GraphDisplay />
    </Container>
  )
}
