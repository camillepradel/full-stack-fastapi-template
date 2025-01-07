import { createFileRoute } from "@tanstack/react-router";
import { Suspense, useState } from "react";
import {
  Button, Container, Heading, useDisclosure,
  Drawer,
  DrawerBody,
  DrawerFooter,
  DrawerHeader,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  Box,
} from "@chakra-ui/react";
import { useSuspenseQuery } from "@tanstack/react-query";
import { DatasetPublic, DatasetsData, DatasetsService, FilterSelect, GraphElementFilter, NodeType } from "../../../client";
import DatasetOverview from "../../../components/Datasets/DatasetOverview";
import DatasetFilters from "../../../components/Datasets/DatasetFilters";
import D3GraphDisplay, { GRAPH_HEIGHT } from "../../../components/Datasets/D3GraphDisplay";
import { GraphDisplayProps } from "../../../components/Datasets/GraphDisplayProps";

export const Route = createFileRoute("/_layout/datasets/$id")({
  component: GraphD3,
});

interface FiltersDrawerProps {
  dataset: DatasetPublic;
  nodeFilters: GraphElementFilter[];
  setNodeFilters: (nodeFilters: GraphElementFilter[]) => void;
  initNodeFilters: (node_types: NodeType[], initValue: FilterSelect) => GraphElementFilter[];
}

const FiltersDrawer = ({ dataset, nodeFilters, setNodeFilters, initNodeFilters }: FiltersDrawerProps) => {
  const [nodeFiltersLocal, setNodeFiltersLocal] = useState<GraphElementFilter[]>(nodeFilters);

  const filterUnchanged = JSON.stringify(nodeFilters) === JSON.stringify(nodeFiltersLocal)

  const { isOpen, onOpen, onClose } = useDisclosure()

  return (
    <>
      <Button colorScheme='teal' onClick={onOpen}>
        Filters
      </Button>
      <Drawer
        isOpen={isOpen}
        placement='right'
        onClose={onClose}
        size="md"
      >
        <DrawerOverlay />
        <DrawerContent>
          <DrawerCloseButton />
          <DrawerHeader>Filters</DrawerHeader>

          <DrawerBody>
            <DatasetFilters dataset={dataset} nodeFilters={nodeFiltersLocal} setNodeFilters={setNodeFiltersLocal} initNodeFilters={initNodeFilters} />
          </DrawerBody>

          <DrawerFooter>
            <Button variant='outline' mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button
              colorScheme='blue'
              isDisabled={filterUnchanged}
              // TODO: close drawer after applying filters (onClose() doesn't work for some reason)
              onClick={() => { setNodeFilters(nodeFiltersLocal); }}
            >
              Apply
            </Button>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>
    </>
  )
}

function initNodeFilters(node_types: NodeType[], initValue: FilterSelect = "everything"): GraphElementFilter[] {
  const nodeFilters: GraphElementFilter[] = node_types.map((node_type) => {
    return {
      element_type_name: node_type.name,
      select: initValue,
      filter_value: {
        combinator: 'and',
        rules: [],
      }
    }
  })
  return nodeFilters;
}

interface GraphDataProps {
  someNodeFrozen: boolean;
  setSomeNodeFrozen: (someNodeFrozen: boolean) => void;
  datasetContentQueryParams: DatasetsData['ReadDatasetContent'];
}

// Handles data fetching and calls GraphDisplay component
function GraphData({ someNodeFrozen, setSomeNodeFrozen, datasetContentQueryParams }: GraphDataProps) {
  const { data: dataset_content } = useSuspenseQuery({
    queryKey: ["dataset-content", datasetContentQueryParams],
    queryFn: () => DatasetsService.readDatasetContent(datasetContentQueryParams),
  });

  return (
    <D3GraphDisplay dataset_content={dataset_content} someNodeFrozen={someNodeFrozen} setSomeNodeFrozen={setSomeNodeFrozen} />
  );
}

// Handles metadata fetching, controls and calls GraphData component
function Graph() {
  const { id: dataset_id } = Route.useParams();
  const datasetQueryParams = { id: parseInt(dataset_id) }
  const { data: dataset } = useSuspenseQuery({
    queryKey: ["dataset", datasetQueryParams],
    queryFn: () => DatasetsService.readDataset(datasetQueryParams),
  });
  const [nodeFilters, setNodeFilters] = useState<GraphElementFilter[]>(
    initNodeFilters(dataset.dataset_schema?.node_types ?? [])
  );
  const datasetContentQueryParams = { id: parseInt(dataset_id), requestBody: { node_filters: nodeFilters } }

  const [someNodeFrozen, setSomeNodeFrozen] = useState(false);

  const unfreezeNodes = () => {
    setSomeNodeFrozen(false)
  }

  return (
    <div>
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        {dataset.name}
      </Heading>
      <Suspense fallback={<Box height={GRAPH_HEIGHT}>Loading graph data...</Box>}>
        <GraphData someNodeFrozen={someNodeFrozen} setSomeNodeFrozen={setSomeNodeFrozen} datasetContentQueryParams={datasetContentQueryParams} />
      </Suspense>
      <Button isDisabled={!someNodeFrozen} onClick={unfreezeNodes}>Unfreeze nodes</Button>
      <FiltersDrawer dataset={dataset} nodeFilters={nodeFilters} setNodeFilters={setNodeFilters} initNodeFilters={initNodeFilters} />
      <DatasetOverview dataset={dataset} />
    </div>
  );
}


function GraphD3() {
  return (
    <Container maxW="full">
      <Suspense fallback={<span>Loading graph...</span>}>
        <Graph />
      </Suspense>
    </Container>
  );
}

export default GraphD3;
