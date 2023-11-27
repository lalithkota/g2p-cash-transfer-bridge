from openg2p_common_g2pconnect_id_mapper.config import Settings as IdMapperSettings
from openg2p_fastapi_common.config import Settings
from pydantic_settings import SettingsConfigDict


class Settings(IdMapperSettings, Settings):
    model_config = SettingsConfigDict(
        env_prefix="gctb_id_translate_", env_file=".env", extra="allow"
    )
    callback_api_common_prefix: str = "/internal/callback"
