from openg2p_fastapi_common.controller import BaseController

from ..config import Settings
from ..models.disburse import DisburseHttpRequest, DisburseHttpResponse
from ..models.msg_header import MsgResponseHeader
from ..services.id_translate_service import IdTranslateService
from ..services.payment_backend import BasePaymentBackendService

_config = Settings.get_config()


class DisbursementController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.add_api_route(
            "/disburse/sync/disburse",
            self.post_dsbt_sync_disburse,
            responses={200: {"model": DisburseHttpResponse}},
            methods=["POST"],
        )
        self.id_translate_service = IdTranslateService.get_component()

    async def post_dsbt_sync_disburse(self, request: DisburseHttpRequest):
        # Validate the message signature here
        self.payment_backend_service = BasePaymentBackendService.get_component()
        disburse_txn = request.message.model_copy()
        if _config.enable_id_translation:
            for disburse in disburse_txn.disbursements:
                disburse.payee_fa = self.id_translate_service.translate(
                    disburse.payee_fa
                )
        disburse_txn_response = self.payment_backend_service.disburse(disburse_txn)

        return DisburseHttpResponse(
            signature=request.signature,
            header=MsgResponseHeader(
                message_id="",
                message_ts="datetime.now()",
                action="",
                status="paid",
                satus_reason_code="GPB-MSP-001",
                status_reason_message="",
                total_count="",
                completed_count="",
                sender_id=request.receiver_id,
                receiver_id=request.sender_id,
                is_msg_encrypted=False,
                meta={},
            ),
            message=disburse_txn_response,
        )
