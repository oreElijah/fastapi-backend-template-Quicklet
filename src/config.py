from pydantic_settings import BaseSettings, SettingsConfigDict

class Setting(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    REDIS_URL: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int   
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    DOMAIN: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_SECRET_KEY: str
    SUCCESS_URL: str
    CANCEL_URL: str
    STRIPE_WEBHOOK_SECRET: str
    B2_KEY_ID: str
    B2_APPLICATION_KEY: str
    B2_BUCKET_NAME: str = "Quicklet"
    B2_BUCKET_ID: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

Config = Setting()

