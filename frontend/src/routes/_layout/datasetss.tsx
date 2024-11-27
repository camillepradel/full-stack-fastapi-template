import {
  Container,
  Flex,
  Heading,
  Skeleton,
  Table,
  TableContainer,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
} from "@chakra-ui/react"
import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"

import { Suspense } from "react"
import { ErrorBoundary } from "react-error-boundary"
import { DatasetsService } from "../../client"
import ActionsMenu from "../../components/Common/ActionsMenu"
import Navbar from "../../components/Common/Navbar"

export const Route = createFileRoute("/_layout/datasetss")({
  component: Datasetss,
})

function ItemsTableBody() {
  const { data: items } = useSuspenseQuery({
    queryKey: ["datasets"],
    queryFn: () => DatasetsService.readDatasets({}),
  })

  return (
    <Tbody>
      {items.data.map((dataset) => (
        <Tr key={dataset.id}>
          <Td>{dataset.id}</Td>
          <Td>{dataset.name}</Td>
          <Td>
            <ActionsMenu type={"Dataset"} value={dataset} /> NOT WORKING
          </Td>
        </Tr>
      ))}
    </Tbody>
  )
}
function DatasetsTable() {
  return (
    <TableContainer>
      <Table size={{ base: "sm", md: "md" }}>
        <Thead>
          <Tr>
            <Th>ID</Th>
            <Th>Name</Th>
          </Tr>
        </Thead>
        <ErrorBoundary
          fallbackRender={({ error }) => (
            <Tbody>
              <Tr>
                <Td colSpan={4}>Something went wrong: {error.message}</Td>
              </Tr>
            </Tbody>
          )}
        >
          <Suspense
            fallback={
              <Tbody>
                {new Array(5).fill(null).map((_, index) => (
                  <Tr key={index}>
                    {new Array(4).fill(null).map((_, index) => (
                      <Td key={index}>
                        <Flex>
                          <Skeleton height="20px" width="20px" />
                        </Flex>
                      </Td>
                    ))}
                  </Tr>
                ))}
              </Tbody>
            }
          >
            <ItemsTableBody />
          </Suspense>
        </ErrorBoundary>
      </Table>
    </TableContainer>
  )
}

function Datasetss() {
  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        Datasets Management
      </Heading>

      <Navbar type={"Dataset"} />
      <DatasetsTable />
    </Container>
  )
}
