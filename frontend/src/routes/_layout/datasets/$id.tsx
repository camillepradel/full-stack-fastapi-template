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
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  HStack,
  SliderMark,
} from "@chakra-ui/react";
import { useSuspenseQuery } from "@tanstack/react-query";
import { DatasetPublic, DatasetsData, DatasetsService, FilterSelect, GraphElementFilter, NodeType } from "../../../client";
import DatasetOverview from "../../../components/Datasets/DatasetOverview";
import DatasetFilters from "../../../components/Datasets/DatasetFilters";
import D3GraphDisplay, { GRAPH_HEIGHT } from "../../../components/Datasets/D3GraphDisplay";

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

interface LimitSliderProps {
  maxLimit: number | null;
  limit: number;
  setLimit: (limit: number) => void;
}

const LimitSlider = ({ maxLimit, limit, setLimit }: LimitSliderProps) => {
  const [limitLocal, setLimitLocal] = useState(limit);
  if (maxLimit !== null && limitLocal > maxLimit) setLimitLocal(maxLimit);

  return (
    <>
      {maxLimit && <Box w="300px">
        <Slider
          aria-label="results-limit-slider"
          min={0}
          max={maxLimit}
          value={limitLocal}
          onChange={(v) => setLimitLocal(v)}
          onChangeEnd={(v) => setLimit(v)}
        >
          <SliderMark value={0} mt="1" ml="-2.5">
            0
          </SliderMark>
          <SliderMark value={maxLimit} mt="1" ml="-2.5">
            {maxLimit}
          </SliderMark>
          <SliderMark
            value={limitLocal}
            textAlign='center'
            bg='blue.500'
            color='white'
            mt='-10'
            ml='-5'
            w='12'
          >
            {limitLocal}
          </SliderMark>
          <SliderTrack>
            <SliderFilledTrack />
          </SliderTrack>
          <SliderThumb bg="blue.500" />
        </Slider>
      </Box>}
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
  setResultItemsTotal: (resultItemsTotal: number) => void;
}

// Handles data fetching and calls GraphDisplay component
function GraphData({ someNodeFrozen, setSomeNodeFrozen, datasetContentQueryParams, setResultItemsTotal }: GraphDataProps) {
  // TODO: below service is called twice with same results when limit is changed from initial value 1000 to something lower
  //       this should be addressed
  const { data: dataset_content } = useSuspenseQuery({
    queryKey: ["dataset-content", datasetContentQueryParams],
    queryFn: () => DatasetsService.readDatasetContent(datasetContentQueryParams),
  });

  // FIXME: below call generates a warning about updating a component while rendering a different component
  setResultItemsTotal(dataset_content.result_items_total);

  return (
    <D3GraphDisplay dataset_content={dataset_content} someNodeFrozen={someNodeFrozen} setSomeNodeFrozen={setSomeNodeFrozen} />
  );
}

// Handles metadata fetching, controls and calls GraphData component
function Graph() {
  // TODO: this component and its children seem to be rendered more than necessary because of the shared state variables
  //       this should be addressed
  const { id: dataset_id } = Route.useParams();
  const datasetQueryParams = { id: parseInt(dataset_id) }
  const { data: dataset } = useSuspenseQuery({
    queryKey: ["dataset", datasetQueryParams],
    queryFn: () => DatasetsService.readDataset(datasetQueryParams),
  });
  const [nodeFilters, setNodeFilters] = useState<GraphElementFilter[]>(
    initNodeFilters(dataset.dataset_schema?.node_types ?? [])
  );

  const [maxLimit, setMaxLimit] = useState<number | null>(null);

  const [limit, setLimit] = useState<number>(1000);

  const datasetContentQueryParams = {
    id: parseInt(dataset_id),
    requestBody: { node_filters: nodeFilters },
    limit: limit
  };

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
        <GraphData someNodeFrozen={someNodeFrozen} setSomeNodeFrozen={setSomeNodeFrozen} datasetContentQueryParams={datasetContentQueryParams} setResultItemsTotal={setMaxLimit} />
      </Suspense>
      <HStack spacing={4} mt={4}>
        <Button isDisabled={!someNodeFrozen} onClick={unfreezeNodes}>Unfreeze nodes</Button>
        <FiltersDrawer dataset={dataset} nodeFilters={nodeFilters} setNodeFilters={setNodeFilters} initNodeFilters={initNodeFilters} />
        <LimitSlider maxLimit={maxLimit} limit={limit} setLimit={setLimit} />
      </HStack>
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
