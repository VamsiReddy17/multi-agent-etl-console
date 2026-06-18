"""
Pipeline Configuration

Centralised config loaded from environment variables / .env file.
Provides defaults for local development.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

# Load .env if present
load_dotenv()


@dataclass
class DatabaseConfig:
    host: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
    user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "postgres"))
    password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", "postgres_password"))
    database: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "dataware"))

    @property
    def url(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    @property
    def dsn(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "dbname": self.database,
        }


@dataclass
class KafkaConfig:
    broker: str = field(default_factory=lambda: os.getenv("KAFKA_BROKER", "localhost:9092"))
    topics: List[str] = field(default_factory=lambda: [
        os.getenv("KAFKA_TOPIC_ORDERS", "orders"),
        os.getenv("KAFKA_TOPIC_CUSTOMERS", "customers"),
    ])
    group_id: str = field(default_factory=lambda: os.getenv("KAFKA_GROUP_ID", "prod-pipeline-group"))
    auto_offset_reset: str = "earliest"
    poll_timeout_ms: int = 1000
    batch_size: int = field(default_factory=lambda: int(os.getenv("KAFKA_BATCH_SIZE", "100")))


@dataclass
class BigQueryConfig:
    project_id: str = field(default_factory=lambda: os.getenv("GCP_PROJECT_ID"))
    dataset: str = field(default_factory=lambda: os.getenv("BQ_DATASET", "solar_core_analytics"))
    credentials_path: str = field(default_factory=lambda: os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))


@dataclass
class PipelineConfig:
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    kafka: KafkaConfig = field(default_factory=KafkaConfig)
    bq: BigQueryConfig = field(default_factory=BigQueryConfig)
    load_target: str = field(default_factory=lambda: os.getenv("LOAD_TARGET", "postgres"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    pipeline_name: str = "streaming-etl"
    max_retries: int = 3
    retry_delay_seconds: int = 5

    def get_log_level(self) -> int:
        return getattr(logging, self.log_level.upper(), logging.INFO)


# Singleton-style default config
default_config = PipelineConfig()
