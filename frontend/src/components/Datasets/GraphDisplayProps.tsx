import { DatasetContent } from "../../client";

export interface GraphDisplayProps {
    dataset_content: DatasetContent;
    someNodeFrozen: boolean;
    setSomeNodeFrozen: (someNodeFrozen: boolean) => void;
}
