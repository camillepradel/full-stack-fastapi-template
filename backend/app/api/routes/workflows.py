import asyncio
from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    ApplyProcessor,
    Workflow,
    WorkflowContent,
    WorkflowPublic,
    WorkflowsPublic,
)
from app.utils_prefect import get_flow_run_logs

router = APIRouter()


@router.get("/", response_model=WorkflowsPublic)
def read_workflows(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> WorkflowsPublic:
    """
    Retrieve workflows of current user.
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Workflow)
        count = session.exec(count_statement).one()
        statement = select(Workflow).offset(skip).limit(limit)
        workflows: Sequence[Workflow] = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Workflow)
            .where(Workflow.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Workflow)
            .where(Workflow.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        workflows: Sequence[Workflow] = session.exec(statement).all()

    return WorkflowsPublic(data=workflows, count=count)


@router.get("/{id}")
def read_workflow_content(
    session: SessionDep, current_user: CurrentUser, id: int
) -> WorkflowContent:
    """
    Get information on a workflow.
    """
    workflow: Workflow | None = session.get(Workflow, id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if not current_user.is_superuser and (workflow.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # TODO?: define our own Log class with less information
    logs = asyncio.run(get_flow_run_logs(workflow.prefect_flow_run_id))
    workflow_content: WorkflowContent = WorkflowContent(
        metadata=WorkflowPublic.model_validate(workflow), logs=logs
    )

    return workflow_content


@router.get("/apply-processor-options/", response_model=dict[str, Any])
def get_apply_processor_options() -> dict[str, Any]:
    """
    Get all options to define processor's parameters.

    Returns:
        dict[str, Any]: The JSON schema for all options to define processor's parameters.
    """
    json_schema: dict[str, Any] = ApplyProcessor.model_json_schema()
    return json_schema
