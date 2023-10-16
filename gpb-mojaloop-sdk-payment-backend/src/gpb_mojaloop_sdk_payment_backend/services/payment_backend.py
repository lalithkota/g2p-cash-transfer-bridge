import logging
from typing import Dict, List

import httpx
from g2p_payments_bridge_core.models.disburse import (
    DisburseRequest,
    SingleDisburseResponse,
)
from g2p_payments_bridge_core.models.msg_header import MsgStatusEnum
from g2p_payments_bridge_core.services.payment_backend import BasePaymentBackendService
from pydantic import BaseModel

from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(__name__)


class ReferenceIdStatus(BaseModel):
    txn_id: str
    ref_id: str
    status: MsgStatusEnum


class MojaloopSdkPaymentBackendService(BasePaymentBackendService):
    def __init__(self, name="", **kwargs):
        super().__init__(name if name else _config.payment_backend_name, **kwargs)
        self.reference_ids_list: Dict[str, ReferenceIdStatus] = {}

    async def disburse(self, disbursement_request: DisburseRequest):
        for disbursement in disbursement_request.disbursements:
            self.reference_ids_list[disbursement.reference_id] = ReferenceIdStatus(
                txn_id=disbursement_request.transaction_id,
                ref_id=disbursement.reference_id,
                status=MsgStatusEnum.pdng,
            )
            data = {
                "homeTransactionId": disbursement.reference_id,
                "from": {
                    "idType": _config.payer_id_type,
                    "idValue": _config.payer_id_value,
                },
                "to": {
                    "idType": _config.payee_id_type,
                    "idValue": await self.get_payee_id_value_from_payee_fa(
                        disbursement.payee_fa
                    ),
                },
                "currency": disbursement.currency_code,
                "amount": float(disbursement.amount),
                "note": disbursement.note,
                "transactionType": "TRANSFER",
                "amountType": "SEND",
            }
            try:
                response = httpx.post(
                    _config.transfers_url,
                    json=data,
                    timeout=_config.api_timeout,
                )
                _logger.info(
                    "Mojaloop SDK Payment Transfer response: %s", response.content
                )
                response.raise_for_status()

                # TODO: Do Status check rather than hardcoding
                self.reference_ids_list[
                    disbursement.reference_id
                ].status = MsgStatusEnum.succ
            except Exception:
                _logger.exception("Mojaloop SDK Payment Failed with unknown reason")
                self.reference_ids_list[
                    disbursement.reference_id
                ].status = MsgStatusEnum.rjct

    async def disburse_status_by_ref_ids(
        self, ref_ids: List[str]
    ) -> List[SingleDisburseResponse]:
        return [
            SingleDisburseResponse(
                reference_id=ref,
                status=self.reference_ids_list[ref].status,
            )
            for ref in ref_ids
        ]

    async def get_payee_id_value_from_payee_fa(self, fa: str) -> str:
        return fa[fa.find(":") + 1 : fa.rfind("@")]
