from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    APP_ENV: str = "development"
    APP_NAME: str = "BankCRM"
    APP_VERSION: str = "0.1.0"

    #class Config:
        #env_file = ".env"

    model_config = SettingsConfigDict(env_file=".env") 

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()