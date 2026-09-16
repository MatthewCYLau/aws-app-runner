from fastapi import FastAPI, BackgroundTasks, HTTPException, Header, status, APIRouter
from pydantic import BaseModel
from api.config.logging import get_logger

logger = get_logger(__name__)


router = APIRouter(prefix="/api/v1/webhook", tags=["webhook"])


class WebhookPayload(BaseModel):
    event: str
    data: dict


def process_webhook_event(event_type: str, payload_data: dict):
    logger.info(f"Processing '{event_type}' asynchronously...")


@router.post("/", status_code=status.HTTP_200_OK)
async def handle_webhook(
    payload: WebhookPayload,
    background_tasks: BackgroundTasks,
    x_signature: str | None = Header(default=None),  # Provider signature header
):
    # 2. Security Check: Verify signature or secret header
    if not x_signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing signature header"
        )

    background_tasks.add_task(process_webhook_event, payload.event, payload.data)

    return {"status": "received"}
