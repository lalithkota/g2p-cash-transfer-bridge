from datetime import datetime
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel

from .msg_header import MsgHeader, MsgResponseHeader, MsgStatusEnum


class SingleDisburseStatusEnum(Enum):
    rjct_reference_id_invalid = "rjct.reference_id.invalid"
    rjct_reference_id_duplicate = "rjct.reference_id.duplicate"
    rjct_timestamp_invalid = "rjct.timestamp.invalid"
    rjct_payer_fa_invalid = "rjct.payer_fa.invalid"
    rjct_payee_fa_invalid = "rjct.payee_fa.invalid"
    rjct_amount_invalid = "rjct.amount.invalid"
    rjct_schedule_ts_invalid = "rjct.schedule_ts.invalid"
    rjct_currency_code_invalid = "rjct.currency_code.invalid"


class SingleDisburseRequest(BaseModel):
    reference_id: str
    # TODO: Not compatible with G2P Connect
    # payer_fa: str
    payer_fa: Optional[str] = None
    payee_fa: str
    amount: str
    scheduled_timestamp: datetime
    payer_name: Optional[str] = None
    payee_name: Optional[str] = None
    note: Optional[str] = None
    purpose: str = None
    instruction: Optional[str] = None
    currency_code: Optional[str] = None
    locale: str = "eng"


class DisburseRequest(BaseModel):
    transaction_id: str
    disbursements: List[SingleDisburseRequest]


class DisburseHttpRequest(BaseModel):
    signature: Optional[str]
    header: MsgHeader
    message: DisburseRequest


class SingleDisburseResponse(BaseModel):
    reference_id: str
    timestamp: datetime = datetime.utcnow()
    status: MsgStatusEnum
    status_reason_code: Optional[SingleDisburseStatusEnum] = None
    status_reason_message: Optional[str] = ""
    instruction: Optional[str] = None
    amount: Optional[str] = None
    payer_fa: Optional[str] = None
    payer_name: Optional[str] = None
    payee_fa: Optional[str] = None
    payee_name: Optional[str] = None
    currency_code: Optional[str] = None
    locale: str = "eng"


class DisburseResponse(BaseModel):
    transaction_id: str
    disbursements_status: List[SingleDisburseResponse]


class DisburseHttpResponse(BaseModel):
    signature: Optional[str]
    header: MsgResponseHeader
    message: DisburseResponse


class TxnStatusTypeEnum(Enum):
    disburse = "disburse"
    # TODO: Not supported right now
    # search = "search"


class TxnStatusAttributeTypeEnum(Enum):
    reference_id_list = "reference_id_list"
    # TODO: Not supported right now
    # transaction_id = "transaction_id"
    # correlation_id = "correlation_id"


class SingleDisburseTxnStatusRequest(BaseModel):
    reference_id: str
    txn_type: TxnStatusTypeEnum
    attribute_type: TxnStatusAttributeTypeEnum
    attribute_value: Union[str, List[str]]
    locale: str = "eng"


class DisburseTxnStatusRequest(BaseModel):
    transaction_id: str
    txnstatus_request: SingleDisburseTxnStatusRequest


class DisburseTxnStatusHttpRequest(BaseModel):
    signature: Optional[str]
    header: MsgHeader
    message: DisburseTxnStatusRequest


class SingleDisburseTxnStatusResponse(BaseModel):
    txn_type: str
    # TODO: Remove none from following
    txn_status: Union[DisburseResponse, List[Union[SingleDisburseResponse, None]]]


class DisburseTxnStatusResponse(BaseModel):
    transaction_id: str
    correlation_id: str
    txnstatus_response: SingleDisburseTxnStatusResponse


class DisburseTxnStatusHttpResponse(BaseModel):
    signature: Optional[str]
    header: MsgResponseHeader
    message: DisburseTxnStatusResponse
