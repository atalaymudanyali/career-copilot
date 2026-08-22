from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    data_dir: Path = Path("data")

    @property
    def cv_path(self) -> Path:
        return self.data_dir / "cv.json"

    @property
    def projects_dir(self) -> Path:
        return self.data_dir / "projects"


settings = Settings()
