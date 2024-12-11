import * as d3 from "d3";
import { useEffect, useRef } from "react";
import { NumericPropertyStatistics } from "../../client";


interface NumericPropertyDistributionProps {
  nps: NumericPropertyStatistics;
}

function NumericPropertyDistribution({ nps }: NumericPropertyDistributionProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  const width = 260;
  const height = 100;
  const marginTop = 20;
  const marginRight = 10;
  const marginBottom = 30;
  const marginLeft = 40;

  useEffect(() => {
    // Clear existing content
    d3.select(svgRef.current).selectAll("*").remove();

    // Create the SVG container.
    const svg = d3.select(svgRef.current)

    if (nps.bins && nps.bins.length > 0 && nps.bins[0].min_max_counts && nps.bins[0].min_max_counts.length > 0) {
      let bins = nps.bins[0].min_max_counts as Array<[number, number, number]>;

      // Declare the x (horizontal position) scale.
      const x = d3.scaleLinear()
        .domain([bins[0][0], bins[bins.length - 1][1]])
        .range([marginLeft, width - marginRight]);

      // Declare the y (vertical position) scale.
      const y = d3.scaleLinear()
        .domain([0, d3.max(bins, (bin) => bin[2]) ?? 0])
        .range([height - marginBottom, marginTop]);

      svg.attr("width", width)
        .attr("height", height)
        .attr("viewBox", [0, 0, width, height])
        .attr("style", "max-width: 100%; height: auto;");

      // Add a rect for each bin.
      svg.append("g")
        .attr("fill", "steelblue")
        .selectAll()
        .data(bins)
        .join("rect")
        .attr("x", (d) => x(d[0]) + 1)
        .attr("width", (d) => x(d[1]) - x(d[0]) - 1)
        .attr("y", (d) => y(d[2]))
        .attr("height", (d) => y(0) - y(d[2]));

      // Add the x-axis and label.
      svg.append("g")
        .attr("transform", `translate(0,${height - marginBottom})`)
        .call(d3.axisBottom(x).ticks(width / 80).tickSizeOuter(0))
        .call((g) => g.append("text")
          .attr("x", width)
          .attr("y", marginBottom - 4)
          .attr("fill", "currentColor")
          .attr("text-anchor", "end"));

      // Add the y-axis and label, and remove the domain line.
      svg.append("g")
        .attr("transform", `translate(${marginLeft},0)`)
        .call(d3.axisLeft(y).ticks(height / 40))
        .call((g) => g.select(".domain").remove())
        .call((g) => g.append("text")
          .attr("x", -marginLeft)
          .attr("y", 10)
          .attr("fill", "currentColor")
          .attr("text-anchor", "start"));
    } else {
      svg.append("g")
        .append("text")
        .attr("x", width / 2)
        .attr("y", height / 2)
        .attr("text-anchor", "middle")
        .text("No data available");
    }

  }, [nps])

  // Return the SVG element.
  return <svg ref={svgRef} />;
}

export default NumericPropertyDistribution;
