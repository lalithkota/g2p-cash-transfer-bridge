from openg2p_fastapi_common.service import BaseService

from ..models.disburse import (
    DisburseRequest,
)


class BasePaymentBackendService(BaseService):
    async def disburse(self, disbursement_request: DisburseRequest):
        """
        Get an ID and return it.
        This method should be implemented in concrete subclasses.
        """
        raise NotImplementedError()
