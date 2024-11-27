
// import useCustomToast from "../../hooks/useCustomToast"


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

import CreateDataset from "./CreateDataset"

interface AddDatasetProps {
  isOpen: boolean
  onClose: () => void
}


const AddDataset = ({ isOpen, onClose }: AddDatasetProps) => {

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
          <ModalHeader>Add Dataset</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>

            <CreateDataset></CreateDataset>

          </ModalBody>

          <ModalFooter gap={3}>
            <Button onClick={onClose}>Cancel</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  )
}

export default AddDataset
