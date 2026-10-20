from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://foe:foe@localhost:5432/foe"
    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    token_hours: int = 168
    data_dir: str = "./data"
    cors_origins: str = "http://localhost:5173"
    max_upload_mb: int = 50
    max_file_write_mb: int = 5
    command_timeout: int = 180
    agent_max_debug_rounds: int = 3

    class Config:
        env_prefix = "FOE_"


settings = Settings()
