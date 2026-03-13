from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""

    app_name: str = "IPC PerfCalc"
    api_prefix: str = "/api/v1"

    # SQLite DB path; default to project root ipc_perfcalc.db
    sqlite_path: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
        / "ipc_perfcalc.db"
    )

    class Config:
        env_prefix = "IPC_"
        env_file = ".env"
        case_sensitive = False


settings = Settings()
