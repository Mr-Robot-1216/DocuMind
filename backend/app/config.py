from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    chat_model: str = "qwen3:8b"
    embed_model: str = "nomic-embed-text"

    chroma_persist_dir: str = "./data/chroma_db"
    sqlite_db_path: str = "./data/documind.db"

    cors_origins: str = "http://localhost:5173"

    chunk_size: int = 800
    chunk_overlap: int = 100

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
