from typing import List

from g2p_cash_transfer_bridge_core.config import Settings
from pydantic import BaseModel, model_validator


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
    response_sender_id: str = "g2p.cash.transfer.bridge.openg2p"
    get_backend_name_from_translate: bool = True

    # TODO: Convert this to ORM Model rather than config
    multiplex_fa_backend_mapping: List[FaBackendMapping] = []

    @model_validator(mode="after")
    def sort_fa_mappings(self) -> "Settings":
        self.multiplex_fa_backend_mapping.sort(key=lambda x: x.order)
        return self
