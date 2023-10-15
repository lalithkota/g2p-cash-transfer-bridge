import asyncio
import logging
import re
import uuid
from typing import Dict, List

from openg2p_fastapi_common.errors.http_exceptions import BadRequestError
from openg2p_fastapi_common.service import BaseService
from pydantic import BaseModel

from ..config import Settings
from ..models.disburse import (
    DisburseRequest,
    DisburseTxnStatusRequest,
    DisburseTxnStatusResponse,
    SingleDisburseRequest,
    SingleDisburseResponse,
    SingleDisburseTxnStatusResponse,
    TxnStatusAttributeTypeEnum,
)
from .payment_backend import BasePaymentBackendService

_config = Settings.get_config()
_logger = logging.getLogger(__name__)


class TransactionQueueItem(BaseModel):
    txn_id: str
    chunk_txn_id: str
    backend_name: str


class PaymentMultiplexerService(BaseService):
    """
    The main goal of this multiplexer service is to
    split a transaction containing multiple payments
    into n different chunks of transactions, one for
    each payment backend type (example: mpesa, bank transfer, etc)

    And then each chunk is sent to the respective
    payment backend service.

    The payment backend service is responsible for its
    own disbursement and status queries fetching and
    maintenance of these chunks.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transaction_queue: Dict[str, List[TransactionQueueItem]] = {}
        """
        The transaction queue dictionary looks like this
        {
            "root_txn_id_0": [
                {
                    "txn_id": "root_txn_id_0",
                    "chunk_txn_id": "0_0",
                    "backend_name": "abc1",
                }
            ],
            "root_txn_id_1": [
                {
                    "txn_id": "root_txn_id_1",
                    "chunk_txn_id": "1_0",
                    "backend_name": "abc1",
                },
                {
                    "txn_id": "root_txn_id_1",
                    "chunk_txn_id": "1_1",
                    "backend_name": "abc2",
                }
            ]
        }
        """
        self.reference_ids_list: Dict[str, TransactionQueueItem] = {}
        """
        The reference ids list looks like this
        {
            "ref_id_0_0_0": {
                "txn_id": "0",
                "chunk_txn_id": "0_0",
                "backend_name": "abc1"
            }
            "ref_id_1_0_1": {
                "txn_id": "1",
                "chunk_txn_id": "1_0",
                "backend_name": "abc1"
            },
            "ref_id_1_1_1": {
                "txn_id": "1",
                "chunk_txn_id": "1_1",
                "backend_name": "abc2"
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
        payment_batch_by_backend_name: Dict[str, List[SingleDisburseRequest]] = {}
        for disbursement in disburse_request.disbursements:
            backend_name = await self.get_payment_backend_from_fa(disbursement.payee_fa)
            if backend_name not in payment_batch_by_backend_name:
                payment_batch_by_backend_name[backend_name] = [
                    disbursement,
                ]
            else:
                payment_batch_by_backend_name[backend_name].append(disbursement)

        self.transaction_queue[disburse_request.transaction_id] = []
        for backend_name, disbursements in payment_batch_by_backend_name.items():
            chunk_txn_id = str(uuid.uuid4())
            txn_queue_item = TransactionQueueItem(
                txn_id=disburse_request.transaction_id,
                chunk_txn_id=chunk_txn_id,
                backend_name=backend_name,
            )
            self.transaction_queue[disburse_request.transaction_id].append(
                txn_queue_item
            )
            self.reference_ids_list.update(
                {dis.reference_id: txn_queue_item for dis in disbursements}
            )
            payment_backend_service = BasePaymentBackendService.get_component(
                name=backend_name
            )
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

    async def disbursement_status(
        self, status_request: DisburseTxnStatusRequest
    ) -> DisburseTxnStatusResponse:
        if (
            status_request.txnstatus_request.attribute_type
            == TxnStatusAttributeTypeEnum.reference_id_list
        ):
            ref_ids = status_request.txnstatus_request.attribute_value
            if not isinstance(ref_ids, list):
                raise BadRequestError(
                    "GPB-PMS-350", "attribute_value is supposed to be a list."
                )
            response = DisburseTxnStatusResponse(
                transaction_id=status_request.transaction_id,
                correlation_id=str(uuid.uuid4()),
                txnstatus_response=SingleDisburseTxnStatusResponse(
                    txn_type="disburse",
                    txn_status=[None for _ in range(len(ref_ids))],
                ),
            )
            backend_to_refs = {}
            for ref in ref_ids:
                ref_txn = self.reference_ids_list.get(ref, None)
                if not ref_txn:
                    continue
                backend_name = ref_txn.backend_name
                if backend_name not in backend_to_refs:
                    backend_to_refs[backend_name] = [
                        ref,
                    ]
                else:
                    backend_to_refs[backend_name].append(ref)
            all_chunk_responses: List[SingleDisburseResponse] = []
            for backend_name in backend_to_refs:
                payment_backend_service = BasePaymentBackendService.get_component(
                    name=backend_name
                )
                if not payment_backend_service:
                    _logger.error(
                        "Didnt find any payment backend implementation for the given name"
                    )
                    continue
                all_chunk_responses += (
                    await payment_backend_service.disburse_status_by_ref_ids(
                        backend_to_refs[backend_name]
                    )
                )
            for i, ref in enumerate(ref_ids):
                for each_chunk in all_chunk_responses:
                    if each_chunk.reference_id == ref:
                        response.txnstatus_response.txn_status[i] = each_chunk
                        break
            return response
        raise NotImplementedError()
