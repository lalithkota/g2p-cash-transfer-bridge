#!/usr/bin/env python3
# ruff: noqa: E402

import asyncio
import logging
from datetime import datetime
from typing import List

import httpx
from g2p_cash_transfer_bridge_core.models.disburse import (
    SingleDisburseStatusEnum,
)
from g2p_cash_transfer_bridge_core.models.msg_header import MsgStatusEnum
from g2p_cash_transfer_bridge_core.models.orm.payment_list import PaymentListItem
from openg2p_fastapi_common.config import Settings as BaseSettings
from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.service import BaseService
from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="gctb_mojaloop_sdk_", env_file=".env", extra="allow"
    )
    openapi_title: str = "GCTB Mojaloop SDK Adapter Payment Backend"
    openapi_description: str = """
    Payment Backend for Mojaloop SDK Adapter  of G2P Cash Transfer Bridge.

    ***********************************
    Further details goes here
    ***********************************
    """
    openapi_version: str = "0.1.0"
    payment_backend_name: str = "mojaloop"
    db_dbname: str = "gctbdb"

    dsbmt_loop_interval_secs: int = 10
    dsbmt_loop_filter_backend_name: bool = True
    dsbmt_loop_filter_status: List[str] = ["rcvd", "fail"]
    translate_id_to_fa: bool = True

    api_timeout: int = 10
    transfers_url: str = "https://bank1.mec.openg2p.net/api/outbound/transfers"
    payer_id_type: str = "ACCOUNT_ID"
    payer_id_value: str = "1212121212"
    payee_id_type: str = "ACCOUNT_ID"
    payer_display_name: str = "Government Treasury Bank"
    transfer_note: str = "GCTB benefit transfer"
    translate_id_to_fa: bool = True

    mapper_registry_url: str = (
        "http://mapper-registry.spar/api/v1/FinancialAddressMapper/search"
    )


_config = Settings.get_config()
_logger = logging.getLogger("openg2p_fastapi_common.app")


class ReferenceIdStatus(BaseModel):
    txn_id: str
    ref_id: str
    status: MsgStatusEnum


class MojaloopSdkPaymentBackendService(BaseService):
    def __init__(self, name="", **kwargs):
        super().__init__(name if name else _config.payment_backend_name, **kwargs)

    async def disburse_loop(self):
        while True:
            db_response = []
            async_session_maker = async_sessionmaker(
                dbengine.get(), expire_on_commit=False
            )
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
                    _logger.info(
                        "GCTB Mojaloop - processing payment from payment list."
                    )
                    await self.disburse(db_response, session)
                else:
                    _logger.info(
                        "GCTB Mojaloop - no records found in payment list table."
                    )

            await asyncio.sleep(_config.dsbmt_loop_interval_secs)

    async def disburse(self, payments: List[PaymentListItem], session: AsyncSession):
        for payment in payments:
            payee_acc_no = ""
            if _config.translate_id_to_fa:
                try:
                    payee_acc_no = await self.get_fa_from_reg(payment.to_fa)
                except Exception:
                    _logger.exception("Mojaloop Payment Failed couldnot get FA from ID")
            else:
                payee_acc_no = payment.to_fa
            data = {
                "homeTransactionId": payment.request_id,
                "from": {
                    "idType": _config.payer_id_type,
                    "idValue": _config.payer_id_value,
                    "displayName": _config.payer_display_name,
                },
                "to": {
                    "idType": _config.payee_id_type,
                    "idValue": self.get_payee_id_value_from_payee_fa(payee_acc_no),
                },
                "currency": "USD",
                "amount": float(payment.amount),
                "note": _config.transfer_note,
                "transactionType": "TRANSFER",
                "amountType": "SEND",
            }
            print(f"data data {data}")
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

    async def get_fa_from_reg(self, id_):
        res = httpx.post(
            _config.mapper_registry_url,
            json={"filters": {"id": {"eq": id_}}, "limit": 1},
        )
        res.raise_for_status()
        resp = res
        res = res.json()
        if res:
            res = res[0]
        if res and "fa" in res:
            res = res["fa"]
        print(f"res res {res} {resp}")
        return res

    def get_payee_id_value_from_payee_fa(self, fa: str) -> str:
        return fa[fa.find(":") + 1 : fa.rfind("@")]


from openg2p_fastapi_common.app import Initializer


class PaymentBackendInitializer(Initializer):
    def initialize(self, **kwargs):
        super().initialize(**kwargs)
        self.payment_backend = MojaloopSdkPaymentBackendService()


if __name__ == "__main__":
    main_init = PaymentBackendInitializer()
    asyncio.run(main_init.payment_backend.disburse_loop())
