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


class SimpleMpesaPaymentBackendService(BasePaymentBackendService):
    def __init__(self, name="", **kwargs):
        super().__init__(name if name else _config.payment_backend_name, **kwargs)
        self.reference_ids_list: Dict[str, ReferenceIdStatus] = {}

    async def disburse(self, disbursement_request: DisburseRequest):
        try:
            data = {"email": _config.agent_email, "password": _config.agent_password}

            response = httpx.post(
                _config.auth_url,
                data=data,
                timeout=_config.api_timeout,
            )
            response.raise_for_status()
            response_data = response.json()
            auth_token = response_data.get("token")

            for disbursement in disbursement_request.disbursements:
                self.reference_ids_list[disbursement.reference_id] = ReferenceIdStatus(
                    txn_id=disbursement_request.transaction_id,
                    ref_id=disbursement.reference_id,
                    status=MsgStatusEnum.pdng,
                )
                headers = {
                    "Authorization": f"Bearer {auth_token}",
                }
                data = {
                    "amount": int(float(disbursement.amount)),
                    "accountNo": await self.get_account_no_from_payee_fa(
                        disbursement.payee_fa
                    ),
                    "customerType": _config.customer_type,
                }
                try:
                    response = httpx.post(
                        _config.payment_url,
                        headers=headers,
                        data=data,
                        timeout=_config.api_timeout,
                    )
                    _logger.info(
                        "MPesa Payment Transfer response: %s", response.content
                    )
                    response.raise_for_status()

                    # TODO: Do Status check rather than hardcoding
                    self.reference_ids_list[
                        disbursement.reference_id
                    ].status = MsgStatusEnum.succ
                except Exception:
                    _logger.exception("Mpesa Payment Failed with unknown reason")
                    self.reference_ids_list[
                        disbursement.reference_id
                    ].status = MsgStatusEnum.rjct

        except Exception:
            _logger.exception("Mpesa Payment Failed during authentication")

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

    async def get_account_no_from_payee_fa(self, fa: str) -> str:
        return fa[fa.find(":") + 1 : fa.rfind(".")]
