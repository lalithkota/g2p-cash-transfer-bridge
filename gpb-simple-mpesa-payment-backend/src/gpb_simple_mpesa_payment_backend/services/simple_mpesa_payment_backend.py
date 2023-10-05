from g2p_payments_bridge_core.models.disburse import (
    DisbursementTransactionRequest,
    DisbursementTransactionResponse,
)
from g2p_payments_bridge_core.services.payment_backend import BasePaymentBackendService


class SimpleMpesaPaymentBackendService(BasePaymentBackendService):
    def disburse(
        self, disbursement_txn: DisbursementTransactionRequest
    ) -> DisbursementTransactionResponse:
        """
        Get an ID and return it.
        This method should be implemented in concrete subclasses.
        """
        pass
