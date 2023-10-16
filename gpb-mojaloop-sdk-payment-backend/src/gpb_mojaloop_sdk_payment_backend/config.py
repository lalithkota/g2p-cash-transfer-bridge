from openg2p_fastapi_common.config import Settings
from pydantic_settings import SettingsConfigDict


class Settings(Settings):
    model_config = SettingsConfigDict(
        env_prefix="gpb_mojaloop_sdk_", env_file=".env", extra="allow"
    )

    payment_backend_name: str = "mojaloop"

    api_timeout: int = 10
    transfers_url: str = ""
    payer_id_type: str = ""
    payer_id_value: str = ""
    payee_id_type: str = ""
