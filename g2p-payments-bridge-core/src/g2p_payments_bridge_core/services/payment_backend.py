from openg2p_fastapi_common.service import BaseService

from ..models.disburse import (
    DisbursementTransactionRequest,
    DisbursementTransactionResponse,
)


class BasePaymentBackendService(BaseService):
    def disburse(
        self, disbursements: DisbursementTransactionRequest
    ) -> DisbursementTransactionResponse:
        """
        Get an ID and return it.
        This method should be implemented in concrete subclasses.
        """
        raise NotImplementedError()
