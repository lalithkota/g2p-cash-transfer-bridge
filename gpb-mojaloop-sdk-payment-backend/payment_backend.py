#!/usr/bin/env python3
# ruff: noqa: E402

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

import httpx
from fastapi import FastAPI
from g2p_payments_bridge_core.models.disburse import (
    SingleDisburseStatusEnum,
)
from g2p_payments_bridge_core.models.msg_header import MsgStatusEnum
from g2p_payments_bridge_core.models.orm.payment_list import PaymentListItem
from g2p_payments_bridge_core.services.id_translate_service import IdTranslateService
from openg2p_fastapi_common.config import Settings as BaseSettings
from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.service import BaseService
from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="gpb_mojaloop_sdk_", env_file=".env", extra="allow"
    )
    openapi_title: str = "GPB Mojaloop SDK Adapter Payment Backend"
    openapi_description: str = """
    Payment Backend for Mojaloop SDK Adapter  of G2P Payments Bridge.

    ***********************************
    Further details goes here
    ***********************************
    """
    openapi_version: str = "0.1.0"

    payment_backend_name: str = "mojaloop"
    db_dbname: str = "gpbdb"

    api_timeout: int = 10
    transfers_url: str = ""
    payer_id_type: str = ""
    payer_id_value: str = ""
    payee_id_type: str = ""
    transfer_note: str = "GPB benefit transfer"
    translate_id_to_fa: bool = True


_config = Settings.get_config()
_logger = logging.getLogger("openg2p_fastapi_common.app")


class ReferenceIdStatus(BaseModel):
    txn_id: str
    ref_id: str
    status: MsgStatusEnum


class MojaloopSdkPaymentBackendService(BaseService):
    def __init__(self, name="", **kwargs):
        super().__init__(name if name else _config.payment_backend_name, **kwargs)
        self._id_translate_service = IdTranslateService.get_component()

    @property
    def id_translate_service(self):
        if not self._id_translate_service:
            self._id_translate_service = IdTranslateService.get_component()
        return self._id_translate_service

    def post_init(self):
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
                            PaymentListItem.status.in_(
                                [
                                    MsgStatusEnum[status]
                                    for status in _config.dsbmt_loop_filter_status
                                ]
                            ),
                        )
                    )
                elif _config.dsbmt_loop_filter_backend_name:
                    stmt = stmt.where(
                        PaymentListItem.backend_name == _config.payment_backend_name
                    )
                elif _config.dsbmt_loop_filter_status:
                    stmt = stmt.where(
                        PaymentListItem.status.in_(
                            [
                                MsgStatusEnum[status]
                                for status in _config.dsbmt_loop_filter_status
                            ]
                        )
                    )
                stmt = stmt.order_by(PaymentListItem.id.asc())
                result = await session.execute(stmt)

                db_response = list(result.scalars())
                if db_response:
                    _logger.info("GPB Mojaloop - processing payment from payment list.")
                    await self.disburse(db_response, session)
                else:
                    _logger.info(
                        "GPB Mojaloop - no records found in payment list table."
                    )

            await asyncio.sleep(_config.dsbmt_loop_interval_secs)

    async def disburse(self, payments: List[PaymentListItem], session: AsyncSession):
        for payment in payments:
            payee_acc_no = ""
            if _config.translate_id_to_fa:
                payee_acc_no = self.id_translate_service.translate(payment.to_fa)
            else:
                payee_acc_no = payment.to_fa
            data = {
                "homeTransactionId": payment.request_id,
                "from": {
                    "idType": _config.payer_id_type,
                    "idValue": _config.payer_id_value,
                },
                "to": {
                    "idType": _config.payee_id_type,
                    "idValue": await self.get_payee_id_value_from_payee_fa(
                        payee_acc_no
                    ),
                },
                "currency": payment.currency,
                "amount": float(payment.amount),
                "note": _config.transfer_note,
                "transactionType": "TRANSFER",
                "amountType": "SEND",
            }
            try:
                response = httpx.post(
                    _config.transfers_url,
                    json=data,
                    timeout=_config.api_timeout,
                )
                _logger.info(
                    "Mojaloop SDK Payment Transfer response: %s", response.content
                )
                response.raise_for_status()

                # TODO: Do Status check rather than hardcoding
                payment.updated_at = datetime.utcnow()
                payment.status = MsgStatusEnum.succ
            except Exception:
                _logger.exception("Mojaloop Payment Failed with unknown reason")
                payment.updated_at = datetime.utcnow()
                payment.status = MsgStatusEnum.rjct
                payment.error_code = SingleDisburseStatusEnum.rjct_payment_failed
                payment.error_msg = "Mojaloop Payment Failed with unknown reason"

            await session.commit()

    async def get_payee_id_value_from_payee_fa(self, fa: str) -> str:
        return fa[fa.find(":") + 1 : fa.rfind("@")]


from gpb_translate_id_fa.app import Initializer as TranslateIdInitializer
from openg2p_common_g2pconnect_id_mapper.app import (
    Initializer as G2pConnectMapperInitializer,
)
from openg2p_fastapi_common.app import Initializer


class PaymentBackendInitializer(Initializer):
    def initialize(self, **kwargs):
        MojaloopSdkPaymentBackendService()

    @asynccontextmanager
    async def fastapi_app_lifespan(self, app: FastAPI):
        self.payment_backend.post_init()
        yield
        await dbengine.get().dispose()


if __name__ == "__main__":
    main_init = PaymentBackendInitializer()
    G2pConnectMapperInitializer()
    TranslateIdInitializer()
    main_init.main()
