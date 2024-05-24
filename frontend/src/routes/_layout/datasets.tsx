import { createFileRoute } from "@tanstack/react-router"

import { Container, Heading, Tab, TabList, TabPanel, TabPanels, Tabs } from "@chakra-ui/react";
import CreateDataset from "../../components/Datasets/CreateDataset";

const tabsConfig = [
  { title: "Create new dataset", component: CreateDataset },
]

export const Route = createFileRoute("/_layout/datasets")({
  component: Datasets,
})

function Datasets() {
  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
        Datasets
      </Heading>
      <Tabs variant="enclosed">
        <TabList>
          {tabsConfig.map((tab, index) => (
            <Tab key={index}>{tab.title}</Tab>
          ))}
        </TabList>
        <TabPanels>
          {tabsConfig.map((tab, index) => (
            <TabPanel key={index}>
              <tab.component />
            </TabPanel>
          ))}
        </TabPanels>
      </Tabs>
    </Container>
  )
}
