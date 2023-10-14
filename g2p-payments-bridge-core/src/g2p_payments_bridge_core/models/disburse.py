from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from . import MsgHeader, MsgResponseHeader


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


class DisbursementTransactionRequest(BaseModel):
    transaction_id: str
    disbursements: List[DisbursementRequest]


class DisburseHttpRequest(BaseModel):
    signature: Optional[str]
    header: MsgHeader
    message: DisbursementTransactionRequest


class DisbursementStatus(BaseModel):
    reference_id: str
    timestamp: datetime
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


class DisbursementTransactionResponse(BaseModel):
    transaction_id: str
    disbursements_status: List[DisbursementStatus]


class DisburseHttpResponse(BaseModel):
    signature: Optional[str]
    header: MsgResponseHeader
    message: DisbursementTransactionResponse
