import asyncio
import logging
from datetime import datetime
from typing import List

import httpx
from g2p_payments_bridge_core.models.disburse import (
    SingleDisburseStatusEnum,
)
from g2p_payments_bridge_core.models.msg_header import MsgStatusEnum
from g2p_payments_bridge_core.models.orm.payment_list import PaymentListItem
from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.service import BaseService
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(__name__)


class ReferenceIdStatus(BaseModel):
    txn_id: str
    ref_id: str
    status: MsgStatusEnum


class SimpleMpesaPaymentBackendService(BaseService):
    def __init__(self, name="", **kwargs):
        super().__init__(name if name else _config.payment_backend_name, **kwargs)
        asyncio.create_task(self.disburse_loop())

    async def disburse_loop(self):
        while True:
            db_response = []
            async_session_maker = async_sessionmaker(dbengine.get())
            async with async_session_maker() as session:
                stmt = select(PaymentListItem)
                if (
                    _config.dsbmt_loop_filter_backend_name
                    and _config.dsbmt_loop_filter_status
                ):
                    stmt = stmt.where(
                        and_(
                            PaymentListItem.backend_name
                            == _config.payment_backend_name,
                            PaymentListItem.status in _config.dsbmt_loop_filter_status,
                        )
                    )
                elif _config.dsbmt_loop_filter_backend_name:
                    stmt = stmt.where(
                        PaymentListItem.backend_name == _config.payment_backend_name
                    )
                elif _config.dsbmt_loop_filter_status:
                    stmt = stmt.where(
                        PaymentListItem.status in _config.dsbmt_loop_filter_status
                    )
                stmt = stmt.order_by(PaymentListItem.id.asc())

                result = await session.execute(stmt)

                db_response = list(result.scalars())

                self.disburse(db_response, session)

            await asyncio.sleep(_config.dsbmt_loop_interval_secs)

    async def disburse(self, payments: List[PaymentListItem], session: AsyncSession):
        try:
            # from_fa field will be ignored in this payment_backend
            data = {"email": _config.agent_email, "password": _config.agent_password}

            response = httpx.post(
                _config.auth_url,
                data=data,
                timeout=_config.api_timeout,
            )
            response.raise_for_status()
            response_data = response.json()
            auth_token = response_data.get("token")

        except Exception:
            _logger.exception("Mpesa Payment Failed during authentication")
            for payment in payments:
                payment.updated_at = datetime.utcnow()
                payment.status = MsgStatusEnum.rjct
                payment.error_code = SingleDisburseStatusEnum.rjct_payment_failed
                payment.error_msg = "Mpesa Payment Failed during authentication"

        else:
            for payment in payments:
                headers = {
                    "Authorization": f"Bearer {auth_token}",
                }
                data = {
                    "amount": int(float(payment.amount)),
                    "accountNo": await self.get_account_no_from_payee_fa(payment.to_fa),
                    "customerType": _config.customer_type,
                }
                try:
                    response = httpx.post(
                        _config.payment_url,
                        headers=headers,
                        data=data,
                        timeout=_config.api_timeout,
                    )
                    _logger.info(
                        "MPesa Payment Transfer response: %s", response.content
                    )
                    response.raise_for_status()

                    # TODO: Do proper Status check here.
                    payment.updated_at = datetime.utcnow()
                    payment.status = MsgStatusEnum.succ
                except Exception:
                    _logger.exception("Mpesa Payment Failed with unknown reason")
                    payment.updated_at = datetime.utcnow()
                    payment.status = MsgStatusEnum.rjct
                    payment.error_code = SingleDisburseStatusEnum.rjct_payment_failed
                    payment.error_msg = "Mpesa Payment Failed with unknown reason"

        session.commit()

    async def get_account_no_from_payee_fa(self, fa: str) -> str:
        return fa[fa.find(":") + 1 : fa.rfind(".")]
