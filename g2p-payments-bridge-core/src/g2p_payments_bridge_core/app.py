# ruff: noqa: E402

import asyncio

from .config import Settings
from .models.orm.payment_list import PaymentListItem

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

    def migrate_database(self, args):
        super().migrate_database(args)

        async def migrate():
            await PaymentListItem.create_migrate()

        asyncio.run(migrate())
