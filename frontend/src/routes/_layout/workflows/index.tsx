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
import { createFileRoute, Link } from "@tanstack/react-router"

import { Suspense } from "react"
import { ErrorBoundary } from "react-error-boundary"
import Navbar from "../../../components/Common/Navbar"
import { WorkflowsService } from "../../../client"

export const Route = createFileRoute("/_layout/workflows/")({
  component: Workflows,
})

function ItemsTableBody() {
  const { data: items } = useSuspenseQuery({
    queryKey: ["workflows"],
    queryFn: () => WorkflowsService.readWorkflows({}),
  })

  return (
    <Tbody>
      {items.data.map((workflow) => (
        <Tr key={workflow.id}>
          <Td><Link to={'/workflows/$id'} params={{ id: workflow.id.toString() }}>{workflow.id}</Link></Td>
          <Td>{workflow.type}</Td>
          <Td>{workflow.description}</Td>
          <Td>{workflow.related_dataset_id}</Td>
          <Td>{workflow.started_at}</Td>
          <Td>{(workflow.ended_at && workflow.started_at)? Date.parse(workflow.ended_at) - Date.parse(workflow.started_at) : "-"}</Td>
          <Td>{workflow.state}</Td>
        </Tr>
      ))}
    </Tbody>
  )
}
function WorkflowsTable() {
  return (
    <TableContainer>
      <Table size={{ base: "sm", md: "md" }}>
        <Thead>
          <Tr>
            <Th>ID</Th>
            <Th>Type</Th>
            <Th>Description</Th>
            <Th>Related dataset</Th>
            <Th>Start time</Th>
            <Th>Duration</Th>
            <Th>State</Th>
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

function Workflows() {
  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        Workflows
      </Heading>

      <Navbar type={"Processor"} />
      <WorkflowsTable />
    </Container>
  )
}
