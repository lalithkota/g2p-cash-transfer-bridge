from openg2p_fastapi_common.config import Settings
from pydantic_settings import SettingsConfigDict


class Settings(Settings):
    model_config = SettingsConfigDict(env_prefix="gpb_core_")

    openapi_title: str = "G2P Payments Bridge"
    openapi_description: str = """
    This module implements G2P Connect Disburse APIs.\
    It contains API layer and multiplexer for different payment backends.

    ***********************************
    Further details goes here
    ***********************************
    """
    openapi_version: str = "0.1.0"
