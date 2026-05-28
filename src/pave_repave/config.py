from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PAVE_")
    host: str = "localhost"
    http_502_max_retries: int = 5
    http_502_retry_delay: int = 30
    wait_state_max_retries: int = 20
    wait_state_initial_delay: int = 20
    wait_state_retry_delay: int = 30
    wait_state_settle_delay: int = 30
    port_forward: bool = False

# Load once at startup
config = AppConfig()