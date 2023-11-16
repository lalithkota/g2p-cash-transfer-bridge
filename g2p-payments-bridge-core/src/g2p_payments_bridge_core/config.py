from typing import List

from openg2p_fastapi_common.config import Settings
from pydantic import BaseModel, model_validator
from pydantic_settings import SettingsConfigDict


class PayerFaPayeeFaMapping(BaseModel):
    order: int
    """
    Order of payer fa mapping
    """

    regex: str
    """
    regex to match the payee fa
    """

    payer_fa: str
    """
    Payer Fa , if the payee fa matches the given regex
    """


class FaBackendMapping(BaseModel):
    order: int
    """
    Order of payment backends to be queried.
    """

    regex: str
    """
    regex to match the
    """

    name: str
    """
    Name of the Payment backend.
    """


class Settings(Settings):
    model_config = SettingsConfigDict(
        env_prefix="gpb_core_", env_file=".env", extra="allow"
    )

    openapi_title: str = "G2P Payments Bridge"
    openapi_description: str = """
    This module implements G2P Connect Disburse APIs.
    It contains API layer and multiplexer for different payment backends.

    ***********************************
    Further details goes here
    ***********************************
    """
    openapi_version: str = "0.1.0"
    db_dbname: str = "gpbdb"

    response_sender_id: str = "g2p.payments.bridge.openg2p"

    enable_id_translation: bool = True

    # TODO: Convert this to ORM Model rather than config
    multiplex_fa_backend_mapping: List[FaBackendMapping] = []
    multiplex_payerfa_payeefa_mapping: List[PayerFaPayeeFaMapping] = []

    @model_validator(mode="after")
    def sort_fa_mappings(self) -> "Settings":
        self.multiplex_fa_backend_mapping.sort(key=lambda x: x.order)
        self.multiplex_payerfa_payeefa_mapping.sort(key=lambda x: x.order)
        return self
