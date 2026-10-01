from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    app_name: str = "ComicCraft"
    environment: str = "development"
    debug: bool = True
    host: str = "127.0.0.1"
    port: int = 8000
    gemini_api_key: str | None = None
    gemini_flash_model: str = "models/gemini-1.5-flash"
    gemini_pro_model: str = "models/gemini-1.5-pro"
    image_provider: str = "mock"
    hf_api_key: str | None = None
    hf_image_model: str = "runwayml/stable-diffusion-v1-5"
    image_width: int = 768
    image_height: int = 768
    image_steps: int = 20
    panel_count: int = 5
    max_prompt_length: int = 2000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def static_dir(self) -> Path:
        path = BASE_DIR / "static"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def panels_dir(self) -> Path:
        path = self.static_dir / "panels"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def exports_dir(self) -> Path:
        path = self.static_dir / "exports"
        path.mkdir(parents=True, exist_ok=True)
        return path

@lru_cache
def get_settings() -> Settings:
    return Settings()
