import functools
import inspect

from prefect import Flow, State, context, flow
from prefect.client.schemas import FlowRun
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select

from app.core.db import engine
from app.models import (
    Workflow,
    WorkflowType,
)


def _update_workflow_states_hook(_: Flow, run: FlowRun, state: State) -> None:
    statement = select(Workflow).where(Workflow.prefect_flow_run_id == run.id)
    with Session(engine) as session:
        try:
            workflow: Workflow = session.exec(statement).one()
            workflow.state = state.type
            session.add(workflow)
            session.commit()
        except NoResultFound:
            pass


def monitored_flow(description: str, related_object_arg_name: str):
    """
    A decorator to create a Prefect flow (equivalent of @flow) and monitor it
    by creating a corresponding Workflow object in the database and updating
    its state according to the flow's state.

    Args:
        description (str): A description of the flow.
        related_object_arg_name (str): The name of the argument that is the object
            related to the workflow (e.g. a Dataset).

    Any decorated function should be called with the following arguments:
    - an argument named after the value of `related_object_arg_name`
    - an argument named `current_user_id` which is the ID of the user who
      triggered the flow
    - an argument named `session` which is a SQLModel Session
    """

    def monitored_flow_inner(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            @flow(
                name=description,
                on_completion=[_update_workflow_states_hook],
                on_failure=[_update_workflow_states_hook],
                on_cancellation=[_update_workflow_states_hook],
                on_crashed=[_update_workflow_states_hook],
                on_running=[_update_workflow_states_hook],
            )
            def flow_func(*args, **kwargs):
                related_object = kwargs[related_object_arg_name]
                current_user_id = kwargs["current_user_id"]
                session = kwargs["session"]

                flow_run = context.get_run_context().flow_run
                assert isinstance(flow_run, FlowRun)

                build_dataset_workflow = Workflow(
                    type=WorkflowType.build_dataset,
                    description=description,
                    state=flow_run.state.type,
                    owner_id=current_user_id,
                    related_dataset_id=related_object.id,
                    prefect_flow_run_id=flow_run.id,
                    is_remote=False,
                )
                session.add(build_dataset_workflow)
                session.commit()
                expected_args = inspect.getfullargspec(func).args
                for arg_name in [related_object_arg_name, "current_user_id", "session"]:
                    if arg_name not in expected_args:
                        kwargs.pop(arg_name)
                return func(*args, **kwargs)

            return flow_func(*args, **kwargs)

        return wrapper

    return monitored_flow_inner
