import asyncio
import uuid

from g2p_cash_transfer_bridge_core.models.disburse import (
    DisburseHttpRequest,
    DisburseHttpResponse,
    DisburseResponse,
    DisburseTxnStatusHttpRequest,
    DisburseTxnStatusHttpResponse,
    SingleDisburseResponse,
)
from g2p_cash_transfer_bridge_core.models.msg_header import (
    MsgResponseHeader,
    MsgStatusEnum,
)
from g2p_cash_transfer_bridge_core.services.payment_multiplexer import (
    PaymentMultiplexerService,
)
from openg2p_fastapi_common.controller import BaseController

from ..config import Settings

_config = Settings.get_config()


class DisbursementController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.payment_multiplexer = PaymentMultiplexerService.get_component()

        self.router.add_api_route(
            "/disburse/sync/disburse",
            self.disburse_sync_disburse,
            responses={200: {"model": DisburseHttpResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/disburse/sync/txn/status",
            self.disburse_sync_txn_status,
            responses={200: {"model": DisburseTxnStatusHttpResponse}},
            methods=["POST"],
        )

    async def disburse_sync_disburse(self, request: DisburseHttpRequest):
        """
        Make a disbursement request. (G2P Connect compliant API - sync).
        - This API does NOT perform the entire disursement process synchronously.
          It only receives the disbubrsement request and returns acknowledgement synchronously.
          Use the status API to get the actual status of disbursement.
        - The payee_fa field in message->disbursements[] can either be FA or ID of the payee,
          depending on the bridge configuration.
        - If bridge is configured to receive ID in payee_fa, then the bridge will translate ID
          to FA using a G2P Connect ID Mapper before making payment
          (Depends on the payment backend).
        - The payer_fa field in message->disbursements[] is optional in this impl of bridge.
          If payer_fa is not given, the bridge will take the default values configured
          (Depends on the payment backend).
        """
        # Perform any extra validations here
        if not request.message.transaction_id:
            request.message.transaction_id = str(uuid.uuid4())

        async def process_disbursement():
            disburse_txn = request.message.model_copy()
            await self.payment_multiplexer.disburse(disburse_txn)

        asyncio.create_task(process_disbursement())

        return DisburseHttpResponse(
            signature=request.signature,
            header=MsgResponseHeader(
                message_id=request.header.message_id,
                action="disburse",
                status=MsgStatusEnum.rcvd,
                sender_id=_config.response_sender_id,
                receiver_id=request.header.sender_id,
                total_count=len(request.message.disbursements),
                completed_count=0,
            ),
            message=DisburseResponse(
                transaction_id=request.message.transaction_id,
                disbursements_status=[
                    SingleDisburseResponse(
                        reference_id=dis.reference_id,
                        status=MsgStatusEnum.rcvd,
                        instruction=dis.instruction,
                        amount=dis.amount,
                        payer_fa=dis.payer_fa,
                        payer_name=dis.payer_name,
                        payee_fa=dis.payee_fa,
                        payee_name=dis.payee_name,
                        currency_code=dis.currency_code,
                    )
                    for dis in request.message.disbursements
                ],
            ),
        )

    async def disburse_sync_txn_status(self, request: DisburseTxnStatusHttpRequest):
        """
        Get status of a disbursement request. (G2P Connect compliant API - sync).
        - The current supported value for txn_type in message->txnstatus_request is "disburse".
        - The current supported values for attribute_type in message->txnstatus_request are
          "transaction_id" and "reference_id_list".
        - To get the status of a particular transaction, pass attribute_type as "transaction_id".
          Then attribute_value in message->txnstatus_request expects a transaction id (string).
        - To get the status of individual payments within transactions, pass attribute_type is
          "reference_id_list".
          Then attribute_value in message->txnstatus_request expects a list of reference
          ids (payment ids, list of strings).

        Errors:
        - Code: GCTB-PMS-350. HTTP: 400. Message: attribute_value is supposed to be a string.
        - Code: GCTB-PMS-350. HTTP: 400. Message: attribute_value is supposed to be a list.
        """
        disburse_status_response = await self.payment_multiplexer.disbursement_status(
            request.message
        )

        # TODO: compute other attributes. For now being hard coded
        final_status = MsgStatusEnum.succ
        final_status_code = None
        final_status_message = None
        total_count = 0
        completed_count = 0

        return DisburseTxnStatusHttpResponse(
            signature=request.signature,
            header=MsgResponseHeader(
                message_id=str(uuid.uuid4()),
                action="status",
                status=final_status,
                status_reason_code=final_status_code,
                status_reason_message=final_status_message,
                sender_id=_config.response_sender_id,
                receiver_id=request.header.sender_id,
                total_count=total_count,
                completed_count=completed_count,
            ),
            message=disburse_status_response,
        )
