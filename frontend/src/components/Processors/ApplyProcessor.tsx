import {
  Button,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
} from "@chakra-ui/react"

import { Form } from '@rjsf/chakra-ui';
import validator from '@rjsf/validator-ajv8';
import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { Suspense } from "react";
import { ApiError, ApplyProcessor, DatasetsService, WorkflowsService } from "../../client";
import useCustomToast from "../../hooks/useCustomToast";
import { IChangeEvent } from "@rjsf/core";
import { RJSFSchema } from "@rjsf/utils";
import React from "react";


const ApplyProcessorForm = () => {
  const { data: jsonSchema } = useSuspenseQuery({
    queryKey: ["apply-processor-options"],
    queryFn: () => WorkflowsService.getApplyProcessorOptions(),
  })

  const log = (type: string) => console.log.bind(console, type);

  const formRef = React.useRef(null);
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const mutation = useMutation({
    mutationFn: (data: ApplyProcessor) =>
      DatasetsService.applyProcessor({ requestBody: data }),
    onSuccess: () => {
      showToast("Success!", "Workflow created successfully.", "success");
      console.log(formRef);
    },
    onError: (err: ApiError) => {
      const errDetail = (err.body as any)?.detail;
      showToast("Something went wrong.", `${errDetail}`, "error");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["workflows"] })
    },
  })

  const onSubmit = (data: IChangeEvent<any, RJSFSchema, any>, _e: any) => mutation.mutate(data.formData);

  return (
    <Form
      schema={jsonSchema}
      validator={validator}
      onChange={log('changed')}
      onSubmit={onSubmit}
      onError={log('errors')}
      ref={formRef}
    />
  )
}

interface ApplyProcessorModalProps {
  isOpen: boolean
  onClose: () => void
}


const ApplyProcessorModal = ({ isOpen, onClose }: ApplyProcessorModalProps) => {

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        size={{ base: "sm", md: "md" }}
        isCentered
      >
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Apply Processor</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>

            <Suspense fallback={<span>Loading form</span>}>
              <ApplyProcessorForm />
            </Suspense>

          </ModalBody>

          <ModalFooter gap={3}>
            <Button onClick={onClose}>Cancel</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  )
}

export default ApplyProcessorModal
