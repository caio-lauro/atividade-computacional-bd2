from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    DB_HOST: str = Field(init=False)
    DB_USER: str = Field(init=False)
    DB_PASSWORD: str = Field(init=False)
    DATABASE: str = Field(init=False)
