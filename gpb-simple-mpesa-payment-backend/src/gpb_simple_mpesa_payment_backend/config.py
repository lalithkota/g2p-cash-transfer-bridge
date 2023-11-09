from typing import List

from openg2p_fastapi_common.config import Settings
from pydantic_settings import SettingsConfigDict


class Settings(Settings):
    model_config = SettingsConfigDict(
        env_prefix="gpb_simple_mpesa_", env_file=".env", extra="allow"
    )

    payment_backend_name: str = "mpesa"

    agent_email: str = ""
    agent_password: str = ""
    auth_url: str = ""
    payment_url: str = ""
    api_timeout: int = 10
    customer_type: str = "subscriber"
    dsbmt_loop_interval_secs: int = 10
    dsbmt_loop_filter_backend_name: bool = True
    dsbmt_loop_filter_status: List[str] = ["rcvd", "fail"]
