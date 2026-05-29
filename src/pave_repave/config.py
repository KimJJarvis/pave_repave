from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PAVE_")
    host: str = "localhost"
    http_502_max_retries: int = 5
    http_502_retry_delay: int = 30
    http_timeout_value: int = 30
    wait_state_max_retries: int = 20
    wait_state_initial_delay: int = 20
    wait_state_retry_delay: int = 30
    wait_state_settle_delay: int = 30
    switch_primary_secondary_max_retries: int = 10
    switch_primary_secondary_retry_delay: int = 30
    fail_over_max_retries: int = 10
    fail_over_retry_delay: int = 30
    port_forward: bool = False

# Load once at startup
config = AppConfig()