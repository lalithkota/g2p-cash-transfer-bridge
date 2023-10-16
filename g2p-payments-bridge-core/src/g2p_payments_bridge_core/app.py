# ruff: noqa: E402

from .config import Settings

_config = Settings.get_config()

from openg2p_fastapi_common.app import Initializer

from .controllers.disbursement_controller import DisbursementController
from .services.payment_multiplexer import PaymentMultiplexerService


class Initializer(Initializer):
    def initialize(self, **kwargs):
        super().initialize()
        # Initialize all Services, Controllers, any utils here.
        PaymentMultiplexerService()
        DisbursementController().post_init()
