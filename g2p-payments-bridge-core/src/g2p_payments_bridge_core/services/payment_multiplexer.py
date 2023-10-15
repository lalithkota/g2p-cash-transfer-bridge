import asyncio
import logging
import re
import uuid

from openg2p_fastapi_common.service import BaseService

from ..config import Settings
from ..models.disburse import DisburseRequest
from .payment_backend import BasePaymentBackendService

_config = Settings.get_config()
_logger = logging.getLogger(__name__)


class PaymentMultiplexerService(BaseService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transaction_queue = {}
        """
        The transaction queue dictionary looks like this
        {
            "root_txn_id_0": {
                "chunk_txn_id_0_0": "backend_name",
                "chunk_txn_id_0_1": "backend_name"
            },
            "root_txn_id_1": {
                "chunk_txn_id_1_0": "backend_name",
                "chunk_txn_id_1_1": "backend_name"
            }
        }
        """

    async def get_payment_backend_from_fa(self, fa: str):
        for mapping in _config.multiplex_fa_backend_mapping:
            if re.search(mapping.regex, fa):
                return mapping.name
        return None

    async def get_payerfa_from_payeefa(self, payee_fa: str):
        for mapping in _config.multiplex_payerfa_payeefa_mapping:
            if re.search(mapping.regex, payee_fa):
                return mapping.payer_fa
        return None

    async def make_disbursements(self, disburse_request: DisburseRequest):
        for disbursement in disburse_request.disbursements:
            if not disbursement.payer_fa:
                disbursement.payer_fa = await self.get_payerfa_from_payeefa(
                    disbursement.payee_fa
                )
        # TODO: Split into chunks based on different criteria. Based on bigger GPB architecture.
        # For now just matching based on the result of regex match of the get_payment_backend_from_fa method
        payment_batch_by_backend_name = {}
        for disbursement in disburse_request.disbursements:
            backend_name = await self.get_payment_backend_from_fa(disbursement.payee_fa)
            if backend_name not in payment_batch_by_backend_name:
                payment_batch_by_backend_name[backend_name] = [
                    disbursement,
                ]
            else:
                payment_batch_by_backend_name[backend_name].append(disbursement)

        self.transaction_queue[disburse_request.transaction_id] = {}
        for backend_name, disbursements in payment_batch_by_backend_name.items():
            payment_backend_service = BasePaymentBackendService.get_component(
                name=backend_name
            )
            chunk_txn_id = str(uuid.uuid4())
            self.transaction_queue[disburse_request.transaction_id][
                chunk_txn_id
            ] = backend_name
            if payment_backend_service:
                # TODO: Change this
                asyncio.create_task(
                    payment_backend_service.disburse(
                        DisburseRequest(
                            transaction_id=chunk_txn_id, disbursements=disbursements
                        )
                    )
                )
            else:
                _logger.error(
                    "Didnt find any payment backend implementation for the given name"
                )
