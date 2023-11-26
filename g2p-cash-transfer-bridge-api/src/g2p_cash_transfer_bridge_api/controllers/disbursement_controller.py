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
