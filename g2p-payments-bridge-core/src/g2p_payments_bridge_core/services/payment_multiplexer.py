import logging
import re

from openg2p_fastapi_common.service import BaseService

from g2p_payments_bridge_core.models.orm.payment_list import PaymentListItem

from ..config import Settings
from ..models.disburse import (
    DisburseRequest,
    DisburseTxnStatusRequest,
    DisburseTxnStatusResponse,
)
from .id_translate_service import IdTranslateService

_config = Settings.get_config()
_logger = logging.getLogger(__name__)


class PaymentMultiplexerService(BaseService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._id_translate_service = IdTranslateService.get_component()

    @property
    def id_translate_service(self):
        if not self._id_translate_service:
            self._id_translate_service = IdTranslateService.get_component()
        return self._id_translate_service

    async def get_payment_backend_from_fa(self, fa: str):
        for mapping in _config.multiplex_fa_backend_mapping:
            if re.search(mapping.regex, fa):
                return mapping.name
        return None

    async def make_disbursements(self, disburse_request: DisburseRequest):
        # TODO:
        payee_fa_list = []
        try:
            payee_fa_list = await self.id_translate_service.translate(
                [
                    disbursement.payee_fa
                    for disbursement in disburse_request.disbursements
                ]
            )
        except:
            # TODO: handle the failures
            pass

        for i, disbursement in enumerate(disburse_request.disbursements):
            try:
                backend_name = await self.get_payment_backend_from_fa(
                    payee_fa_list[i] or ""
                )
            except:
                # TODO : handle the failures
                pass
            await PaymentListItem.insert(
                disburse_request.transaction_id, disbursement, backend_name=backend_name
            )

    async def disbursement_status(
        self, status_request: DisburseTxnStatusRequest
    ) -> DisburseTxnStatusResponse:
        pass
