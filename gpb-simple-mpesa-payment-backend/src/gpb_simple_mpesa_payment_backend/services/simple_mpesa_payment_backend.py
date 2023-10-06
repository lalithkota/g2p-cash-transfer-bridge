import logging
from datetime import datetime

import httpx
from g2p_payments_bridge_core.models.disburse import (
    DisburseHttpResponse,
    DisbursementTransactionRequest,
    DisbursementTransactionResponse,
)
from g2p_payments_bridge_core.models.msg_header import MsgResponseHeader
from g2p_payments_bridge_core.services.payment_backend import BasePaymentBackendService

from ..config import Settings

_config = Settings.get_config()

_logger = logging.getLogger(__name__)


class SimpleMpesaPaymentBackendService(BasePaymentBackendService):
    def disburse(
        self, disbursement_txn: DisbursementTransactionRequest
    ) -> DisbursementTransactionResponse:
        """
        Get an ID and return it.
        This method should be implemented in concrete subclasses.
        """
        try:
            data = {"email": _config.agent_email, "password": _config.agent_password}
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            response = httpx.post(
                _config.auth_url,
                data=data,
                headers=headers,
                timeout=_config.api_timeout,
            )
            response.raise_for_status()
            response_data = response.json()
            auth_token = response_data.get("token")

            completed_payments = 0

            for disbursement in disbursement_txn.disbursements:
                payee_id_value = disbursement.payee_fa.split(":")[-1]
                amount = int(disbursement.amount)
                auth_header = "Bearer " + auth_token
                headers = {
                    "Authorization": auth_header,
                    "Content-Type": "application/x-www-form-urlencoded",
                }
                data = {
                    "amount": amount,
                    "accountNo": payee_id_value,
                    "customerType": self.customer_type,
                }
                try:
                    response = httpx.post(
                        self.payment_endpoint_url,
                        headers=headers,
                        data=data,
                        timeout=self.api_timeout,
                    )
                    _logger.info(
                        "MPesa Payment Transfer response: %s", response.content
                    )
                    response.raise_for_status()

                    # TODO: Do Status check rather than hardcoding
                    completed_payments += 1
                except Exception:
                    _logger.exception("Mpesa Payment Failed with unknown reason")

        except Exception:
            _logger.exception("Mpesa Payment Failed during authentication")

        disbursement_response = DisbursementTransactionResponse(
            reference_id="",
            timestamp=datetime.now(),
            status="paid",
            status_reason_code="GPB-MSP-001",
            status_reason_message="",
            instruction="",
            amount=DisbursementTransactionRequest,
            payer_fa="",
            payer_name="",
            payee_fa="",
            payee_name="",
            currency_code="",
            locale="",
        )

        return DisburseHttpResponse(
            signature="",
            header=MsgResponseHeader(
                message_id="",
                message_ts=datetime.now(),
                action="response_action",
                status="paid",
                status_reason_code="GPB-MSP-001",
                status_reason_message="",
                total_count="",
                completed_count="",
                sender_id="response_sender",
                receiver_id="response_receiver",
                is_msg_encrypted=True,
                meta={"response_key": "response_value"},
            ),
            message=disbursement_response,
        )
