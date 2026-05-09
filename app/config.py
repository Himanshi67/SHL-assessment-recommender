from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="SHL Assessment Recommender", alias="APP_NAME")
    env: str = Field(default="development", alias="ENV")
    raw_catalog_path: str = Field(
        default="data/raw/shl_product_catalog.json", alias="RAW_CATALOG_PATH"
    )
    cleaned_json_path: str = Field(
        default="data/processed/shl_catalog_clean.json", alias="CLEANED_JSON_PATH"
    )
    cleaned_csv_path: str = Field(
        default="data/processed/shl_catalog_clean.csv", alias="CLEANED_CSV_PATH"
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
