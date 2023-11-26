from datetime import datetime
from typing import List, Optional

from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.models import BaseORMModelWithTimes
from sqlalchemy import DateTime, Enum, String, select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from g2p_cash_transfer_bridge_core.models.disburse import (
    SingleDisburseRequest,
    SingleDisburseStatusEnum,
)
from g2p_cash_transfer_bridge_core.models.msg_header import MsgStatusEnum


class PaymentListItem(BaseORMModelWithTimes):
    __tablename__ = "payment_list"

    batch_id: Mapped[str] = mapped_column(String())
    request_id: Mapped[str] = mapped_column(String())
    request_timestamp: Mapped[datetime] = mapped_column(DateTime())
    from_fa: Mapped[Optional[str]] = mapped_column(String())
    to_fa: Mapped[str] = mapped_column(String())
    amount: Mapped[str] = mapped_column(String())
    currency: Mapped[str] = mapped_column(String())
    status: Mapped[MsgStatusEnum] = mapped_column(
        Enum(MsgStatusEnum, native_enum=False)
    )
    file: Mapped[Optional[str]] = mapped_column(String())
    error_code: Mapped[Optional[SingleDisburseStatusEnum]] = mapped_column(
        Enum(SingleDisburseStatusEnum, native_enum=False)
    )
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
    ) -> "PaymentListItem":
        payment_item = None
        async_session_maker = async_sessionmaker(dbengine.get())
        async with async_session_maker() as session:
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

    @classmethod
    async def get_by_batch_id(cls, batch_id: str) -> List["PaymentListItem"]:
        response = []
        async_session_maker = async_sessionmaker(dbengine.get())
        async with async_session_maker() as session:
            stmt = select(cls).where(cls.batch_id == batch_id).order_by(cls.id.asc())
            result = await session.execute(stmt)

            response = list(result.scalars())
        return response

    @classmethod
    async def get_by_request_ids(
        cls, request_ids: List[str]
    ) -> List["PaymentListItem"]:
        response = []
        async_session_maker = async_sessionmaker(dbengine.get())
        async with async_session_maker() as session:
            stmt = (
                select(cls).where(cls.request_id in request_ids).order_by(cls.id.asc())
            )
            result = await session.execute(stmt)

            response = list(result.scalars())
        return response
