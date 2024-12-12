import { createFileRoute } from "@tanstack/react-router";
import { Suspense } from "react";
import { Container, Heading } from "@chakra-ui/react";
import { useSuspenseQuery } from "@tanstack/react-query";
import { WorkflowsService } from "../../../client";

export const Route = createFileRoute("/_layout/workflows/$id")({
  component: Workflow,
});


// Handles data fetching, controls and calls GraphDisplay component
function WorkflowContent() {
  const { id: workflow_id } = Route.useParams();
  const { data: workflowContent } = useSuspenseQuery({
    queryKey: ["workflow-content"],
    queryFn: () => WorkflowsService.readWorkflowContent({ id: parseInt(workflow_id) }),
  });

  return (
    <div>
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
      {workflowContent.metadata.type} - [{workflowContent.metadata.id}]{workflowContent.metadata.description} - {workflowContent.metadata.state} - {workflowContent.metadata.started_at} - {(workflowContent.metadata.ended_at && workflowContent.metadata.started_at)? Date.parse(workflowContent.metadata.ended_at) - Date.parse(workflowContent.metadata.started_at) : "-"}
      </Heading>
      <div>
        Logs:
        <ul>
          {workflowContent.logs.map((log) => (
            <li>{log.timestamp} - {log.message}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}


function Workflow() {
  return (
    <Container maxW="full">
      <Suspense fallback={<span>Loading workflow...</span>}>
        <WorkflowContent />
      </Suspense>
    </Container>
  );
}

export default Workflow;
