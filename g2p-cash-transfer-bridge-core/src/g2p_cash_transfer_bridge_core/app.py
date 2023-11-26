import asyncio

from openg2p_fastapi_common.app import Initializer

from .models.orm.payment_list import PaymentListItem


class Initializer(Initializer):
    def migrate_database(self, args):
        super().migrate_database(args)

        async def migrate():
            await PaymentListItem.create_migrate()

        asyncio.run(migrate())
