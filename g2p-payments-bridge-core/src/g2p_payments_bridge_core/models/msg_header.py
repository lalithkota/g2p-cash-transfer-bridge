from datetime import datetime
from typing import Optional

from pydantic import AnyUrl, BaseModel


class MsgHeader(BaseModel):
    version: str = "1.0.0"
    message_id: str
    message_ts: datetime
    action: str
    sender_id: str
    sender_uri: Optional[AnyUrl]
    receiver_id: Optional[str]
    total_count: int
    is_msg_encrypted: bool = False
    meta: dict = {}


class MsgResponseHeader(BaseModel):
    version: str = "1.0.0"
    message_id: str
    message_ts: datetime
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
