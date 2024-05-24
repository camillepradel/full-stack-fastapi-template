import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query"
import { Suspense } from "react"
import { ApiError, DatasetCreate, DatasetsService } from "../../client"
import Form from '@rjsf/chakra-ui';
import validator from '@rjsf/validator-ajv8';
import useCustomToast from "../../hooks/useCustomToast";
import React from "react";


const CreateDatasetForm = () => {
  const { data: jsonSchema } = useSuspenseQuery({
    queryKey: ["datasets"],
    queryFn: () => DatasetsService.getCreateOptions(),
  })

  const log = (type) => console.log.bind(console, type);

  const formRef = React.createRef();
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const mutation = useMutation({
    mutationFn: (data: DatasetCreate) =>
      DatasetsService.createDataset({ requestBody: data }),
    onSuccess: () => {
      showToast("Success!", "Item created successfully.", "success");
      console.log(formRef);
    },
    onError: (err: ApiError) => {
      const errDetail = (err.body as any)?.detail;
      showToast("Something went wrong.", `${errDetail}`, "error");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["items"] })
    },
  })

  const onSubmit = ({ formData }) => mutation.mutate(formData);

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

const CreateDataset = () => {
  return (
    <Suspense fallback={<span>Loading form</span>}>
      <CreateDatasetForm />
    </Suspense>
  )
}

export default CreateDataset
