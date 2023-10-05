from openg2p_fastapi_common.config import Settings
from pydantic_settings import SettingsConfigDict


class SettingsExtended(Settings):
    model_config = SettingsConfigDict(env_prefix="g2p_payments_bridge")
