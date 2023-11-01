from datetime import datetime
from typing import Optional

from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.models import BaseORMModelWithTimes
from sqlalchemy import DateTime, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from g2p_payments_bridge_core.models.disburse import SingleDisburseRequest


class PaymentListItem(BaseORMModelWithTimes):
    __tablename__ = "payment_list"

    batch_id: Mapped[str] = mapped_column(String())
    request_id: Mapped[str] = mapped_column(String())
    request_timestamp: Mapped[datetime] = mapped_column(DateTime())
    from_fa: Mapped[Optional[str]] = mapped_column(String())
    to_fa: Mapped[str] = mapped_column(String())
    amount: Mapped[str] = mapped_column(String())
    currency: Mapped[str] = mapped_column(String())
    status: Mapped[str] = mapped_column(String())
    file: Mapped[Optional[str]] = mapped_column(String())
    error_code: Mapped[Optional[str]] = mapped_column(String())
    error_msg: Mapped[Optional[str]] = mapped_column(String())
    backend_name: Mapped[Optional[str]] = mapped_column(String())

    @classmethod
    async def insert(
        cls,
        batch_id: str,
        disburse_request: SingleDisburseRequest,
        backend_name: str = None,
        status: str = "rcvd",
        file: str = None,
        error_code: str = None,
        error_msg: str = None,
    ):
        payment_item = None
        async with AsyncSession(dbengine.get()) as session:
            payment_item = PaymentListItem(
                batch_id=batch_id,
                request_id=disburse_request.reference_id,
                request_timestamp=disburse_request.scheduled_timestamp.replace(
                    tzinfo=None
                ),
                from_fa=disburse_request.payer_fa,
                to_fa=disburse_request.payee_fa,
                amount=disburse_request.amount,
                currency=disburse_request.currency_code,
                status=status,
                file=file,
                error_code=error_code,
                error_msg=error_msg,
                backend_name=backend_name,
                active=True,
            )
            session.add(payment_item)
            await session.commit()
        return payment_item
