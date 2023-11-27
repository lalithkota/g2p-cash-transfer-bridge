from openg2p_fastapi_common.service import BaseService

from ..models.disburse import (
    DisburseRequest,
    DisburseTxnStatusRequest,
    DisburseTxnStatusResponse,
)


class PaymentMultiplexerService(BaseService):
    async def disburse(self, disburse_request: DisburseRequest):
        raise NotImplementedError()

    async def disbursement_status(
        self, status_request: DisburseTxnStatusRequest
    ) -> DisburseTxnStatusResponse:
        raise NotImplementedError()
