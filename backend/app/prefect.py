from prefect import get_client
from prefect.client.schemas.objects import Log
from prefect.server.schemas.filters import LogFilter


async def get_flow_run_logs(flow_run_id) -> list[Log]:
    async with get_client() as client:
        logs = await client.read_logs(LogFilter(flow_run_id={"any_": [flow_run_id]}))

    return logs
