import asyncio
import uuid

from openg2p_fastapi_common.controller import BaseController

from ..config import Settings
from ..models.disburse import (
    DisburseHttpRequest,
    DisburseHttpResponse,
    DisburseResponse,
    SingleDisburseResponse,
)
from ..models.msg_header import MsgResponseHeader, MsgStatusEnum
from ..services.id_translate_service import IdTranslateService
from ..services.payment_multiplexer import PaymentMultiplexerService

_config = Settings.get_config()


class DisbursementController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._id_translate_service = IdTranslateService.get_component()
        self.payment_multiplexer = PaymentMultiplexerService.get_component()

        self.router.add_api_route(
            "/disburse/sync/disburse",
            self.post_dsbt_sync_disburse,
            responses={200: {"model": DisburseHttpResponse}},
            methods=["POST"],
        )

    @property
    def id_translate_service(self):
        if not self._id_translate_service:
            self._id_translate_service = IdTranslateService.get_component()
        return self._id_translate_service

    async def post_dsbt_sync_disburse(self, request: DisburseHttpRequest):
        # Perform any extra validations here
        if not request.message.transaction_id:
            request.message.transaction_id = str(uuid.uuid4())

        async def process_disbursement():
            disburse_txn = request.message.model_copy()
            if _config.enable_id_translation:
                payee_fa_responses = await self.id_translate_service.translate(
                    [dis.payee_fa for dis in disburse_txn.disbursements]
                )
                for i, dis in enumerate(disburse_txn.disbursements):
                    dis.payee_fa = payee_fa_responses[i]
            await self.payment_multiplexer.make_disbursements(disburse_txn)

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
