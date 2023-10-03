import datetime
from typing import List, Optional

from fastapi import FastAPI
from pydantic import AnyHttpUrl, BaseModel

app = FastAPI()

# Define Pydantic models for request and response schemas


class Error(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    errors: List[Error]


class MsgHeader(BaseModel):
    version: str = "1.0.0"
    message_id: str
    message_ts: datetime.datetime
    action: str
    sender_id: str
    sender_uri: Optional[AnyHttpUrl]
    receiver_id: Optional[str]
    total_count: int
    is_msg_encrypted: bool = False
    meta: dict = {}


class DisbursementRequest(BaseModel):
    reference_id: str
    payer_fa: str
    payee_fa: str
    amount: str
    scheduled_timestamp: str
    payer_name: Optional[str]
    payee_name: Optional[str]
    note: Optional[str]
    purpose: str
    instruction: Optional[str]
    currency_code: str
    locale: str


class DisburseRequestMessage(BaseModel):
    transaction_id: str
    disbursements: List[DisbursementRequest]


class DisburseHttpRequest(BaseModel):
    signature: Optional[str]
    header: MsgHeader
    message: DisburseRequestMessage


class MsgResponseHeader(BaseModel):
    version: str = "1.0.0"
    message_id: str
    message_ts: datetime.datetime
    action: str
    status: str
    status_reason_code: Optional[str]
    status_reason_message: Optional[str]
    total_count: Optional[int]
    completed_count: Optional[str]
    sender_id: Optional[str]
    receiver_id: Optional[str]
    total_count: Optional[str]
    is_msg_encrypted: bool = False
    meta: dict = {}


class DisbursementStatus(BaseModel):
    reference_id: str
    timestamp: str
    status: str
    status_reason_code: Optional[str]
    status_reason_message: Optional[str]
    instruction: Optional[str]
    amount: Optional[str]
    payer_fa: Optional[str]
    payer_name: Optional[str]
    payee_fa: Optional[str]
    payee_name: Optional[str]
    currency_code: Optional[str]
    locale: Optional[str]


class DisburseStatusMessage(BaseModel):
    transaction_id: str
    disbursements_status: List[DisbursementStatus]


class DisburseHttpResponse(BaseModel):
    signature: Optional[str]
    header: MsgResponseHeader
    message: DisburseStatusMessage


# Define route for /disburse/sync/disburse endpoint
@app.post(
    "/disburse/sync/disburse",
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def post_dsbt_sync_disburse(request: DisburseHttpRequest) -> DisburseHttpResponse:
    try:

        # Validate the message signature here

        # Process the disbursement request here

        # Return a successful response
        response = {"message": {"ack_status": "ACK"}}
        return response
    except Exception as e:
        # Handle errors and return an error response
        error = Error(code="ERR", message=str(e))
        response = {"message": {"ack_status": "ERR", "error": error}}
        return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
