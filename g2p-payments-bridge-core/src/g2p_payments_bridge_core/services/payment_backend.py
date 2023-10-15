from typing import List

from openg2p_fastapi_common.service import BaseService

from ..models.disburse import DisburseRequest, DisburseResponse, SingleDisburseResponse


class BasePaymentBackendService(BaseService):
    async def disburse(self, disbursement_request: DisburseRequest):
        """
        Perform disbursement for the given request
        """
        raise NotImplementedError()

    async def disburse_status(self, transaction_id: str) -> DisburseResponse:
        """
        get disbursement transaction of the given request
        """
        raise NotImplementedError()

    async def disburse_status_by_ref_ids(
        self, ref_ids: List[str]
    ) -> List[SingleDisburseResponse]:
        """
        get disbursement transaction of the given request
        """
        raise NotImplementedError()
