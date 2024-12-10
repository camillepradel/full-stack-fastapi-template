import { DatasetPublic } from "../../client";
import { SymbolicPropertyStatistics, NumericPropertyStatistics } from "../../client";
import { Box, Button, Center, Tab, TabList, TabPanel, TabPanels, Tabs } from '@chakra-ui/react';
import {
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
} from '@chakra-ui/react'
import { SimpleGrid } from '@chakra-ui/react'
import {
  Table,
  Thead,
  Tbody,
  Tfoot,
  Tr,
  Th,
  Td,
  TableContainer,
} from '@chakra-ui/react'
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverHeader,
  PopoverBody,
  PopoverArrow,
  PopoverCloseButton,
} from '@chakra-ui/react'
import NumericPropertyDistribution from "./NumericPropertyDistribution";




interface PropertyStatisticsProps {
  propertyStatistics: SymbolicPropertyStatistics | NumericPropertyStatistics | null;
}

const PropertyStatistics = ({ propertyStatistics }: PropertyStatisticsProps) => {
  if (!propertyStatistics) return null;
  if ("value_counts" in propertyStatistics) {
    // SymbolicPropertyStatistics
    let sps = propertyStatistics as SymbolicPropertyStatistics;
    return (
      <div>
        <TableContainer>
          <Table size='sm'>
            <Thead>
              <Tr>
                <Th>Value</Th>
                <Th isNumeric>Count</Th>
              </Tr>
            </Thead>
            <Tbody>
              {sps.value_counts.map((value_count) => (
                <Tr key={value_count[0] as string}>
                  <Td>{value_count[0] ? (value_count[0] as string) : "null"}</Td>
                  <Td isNumeric>{value_count[1] as number}</Td>
                </Tr>
              ))}
            </Tbody>
            {sps.value_counts_max &&
              <Tfoot>
                <Tr>
                  <Th>...</Th>
                  <Th></Th>
                </Tr>
              </Tfoot>
            }
          </Table>
        </TableContainer>
      </div>
    )
  } else {
    // NumericPropertyStatistics
    let nps = propertyStatistics as NumericPropertyStatistics;
    return (
      <div>
        <NumericPropertyDistribution nps={nps} />
      </div>
    )
  }
}

interface DatasetOverviewProps {
  dataset: DatasetPublic;
}

const DatasetOverview = ({ dataset }: DatasetOverviewProps) => {
  return (
    <Tabs>
      <TabList>
        <Tab>Nodes</Tab>
        <Tab>Relations</Tab>
      </TabList>

      <TabPanels>
        <TabPanel>
          <Accordion>
            {dataset.dataset_schema?.node_types.map((node_type) => (
              <AccordionItem key={node_type.name}>
                <h2>
                  <AccordionButton>
                    <Box as='span' flex='1' textAlign='left'>
                      {node_type.name}
                    </Box>
                    <AccordionIcon />
                  </AccordionButton>
                </h2>
                <AccordionPanel pb={4}>
                  <SimpleGrid columns={[2, null, 3]} spacing='10px'>
                    {node_type.properties.map((property) => (
                      <Box key={property.name}>
                        <Center h='60px'>
                          {property.is_primary_key ? '🔑 ' : ''}{property.name}: {property.type}
                          <Popover>
                            <PopoverTrigger>
                              <Button>details</Button>
                            </PopoverTrigger>
                            <PopoverContent>
                              <PopoverArrow />
                              <PopoverCloseButton />
                              <PopoverHeader>Overview of values</PopoverHeader>
                              <PopoverBody>
                                {dataset.statistics?.node_type_to_property_to_statistics && node_type.name in dataset.statistics?.node_type_to_property_to_statistics &&
                                  property.name in dataset.statistics?.node_type_to_property_to_statistics[node_type.name] &&
                                  <PropertyStatistics propertyStatistics={dataset.statistics?.node_type_to_property_to_statistics[node_type.name][property.name]} />
                                }
                              </PopoverBody>
                            </PopoverContent>
                          </Popover>

                        </Center>
                      </Box>
                    ))}
                  </SimpleGrid>
                </AccordionPanel>
              </AccordionItem>
            ))}
          </Accordion>
        </TabPanel>
        <TabPanel>
          <p>two!</p>
        </TabPanel>
      </TabPanels>
    </Tabs>
  )
}

export default DatasetOverview
