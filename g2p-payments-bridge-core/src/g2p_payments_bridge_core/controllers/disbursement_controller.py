from openg2p_fastapi_common.controller import BaseController

from ..models.disburse import DisburseHttpRequest, DisburseHttpResponse
from ..models.msg_header import MsgResponseHeader
from ..services.id_translate_service import IdTranslateService
from ..services.payment_backend import BasePaymentBackendService


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
        self.payment_backend_service = BasePaymentBackendService.get_component()

    async def post_dsbt_sync_disburse(self, request: DisburseHttpRequest):
        # Validate the message signature here

        disburse_txn = request.message.model_copy()
        for disburse in disburse_txn.disbursements:
            disburse.payee_fa = self.id_translate_service.translate(disburse.payee_fa)
        disburse_txn_response = self.payment_backend_service.disburse(disburse_txn)

        return DisburseHttpResponse(
            signature=request.signature,
            header=MsgResponseHeader(),
            message=disburse_txn_response,
        )
