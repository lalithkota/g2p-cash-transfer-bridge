import logging

import httpx
from g2p_payments_bridge_core.models.disburse import DisburseRequest
from g2p_payments_bridge_core.services.payment_backend import BasePaymentBackendService

from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(__name__)


class SimpleMpesaPaymentBackendService(BasePaymentBackendService):
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
                headers = {
                    "Authorization": f"Bearer {auth_token}",
                }
                data = {
                    "amount": int(disbursement.amount),
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

                except Exception:
                    _logger.exception("Mpesa Payment Failed with unknown reason")

        except Exception:
            _logger.exception("Mpesa Payment Failed during authentication")

    async def get_account_no_from_payee_fa(self, fa: str) -> str:
        return fa[fa.find(":") + 1 : fa.rfind(".")]
