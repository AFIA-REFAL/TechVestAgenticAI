"""
BVRIT Hyderabad College FAQ Chatbot - Configuration Module

Centralized configuration management using pydantic-settings.
Loads environment variables from .env file and provides typed,
validated configuration objects to all application modules.

Author: Senior GenAI Engineer
Version: 1.0.0
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict

# Determine project root directory (where config.py resides)
PROJECT_ROOT = Path(__file__).parent.absolute()
os.chdir(PROJECT_ROOT)  # Ensure all relative paths resolve correctly

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All configuration is centralized here for consistency.
    """

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ============================================================
    # OpenRouter API Configuration
    # ============================================================
    openrouter_api_key: str = Field(
        default="",
        description="OpenRouter API key for LLM and embedding access",
        validation_alias="OPENROUTER_API_KEY"
    )

    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL",
        validation_alias="OPENROUTER_BASE_URL"
    )

    # ============================================================
    # Model Configuration
    # ============================================================
    llm_model: str = Field(
        # BUG FIX: "gpt-4o-mini" is an OpenAI model name that does NOT map to
        # an OpenRouter route. The correct OpenRouter identifier is
        # "openai/gpt-4o-mini". Using the wrong name causes every LLM call
        # to fail with a 404, so the chatbot silently returns an error
        # answer for EVERY question, regardless of retrieval quality.
        default="openai/gpt-4o-mini",
        description="LLM model for answer generation (OpenRouter model string)",
        validation_alias="LLM_MODEL"
    )

    embedding_model: str = Field(
        # BUG FIX: Same issue — OpenRouter embedding route is
        # "openai/text-embedding-3-small", not "text-embedding-3-small".
        # A wrong embedding model name causes ALL vectors to be zero-vectors
        # (or an error), making similarity search completely random.
        default="openai/text-embedding-3-small",
        description="Embedding model for vector embeddings (OpenRouter model string)",
        validation_alias="EMBEDDING_MODEL"
    )

    # ============================================================
    # Document & Chunking Configuration
    # ============================================================
    document_path: str = Field(
        default="data/bvrit_college_info.docx",
        description="Path to the college knowledge base document (DOCX format with structured college info)",
        validation_alias="DOCUMENT_PATH"
    )

    knowledge_base_schema_version: int = Field(
        default=2,
        description="Metadata schema version used for knowledge base chunks"
    )

    image_index_path: str = Field(
        default="data/bvrit_image_index.json",
        description="Path to the scraped image index for source pages"
    )

    chunk_size: int = Field(
        # IMPROVEMENT: 800 characters is ~200 tokens. For a structured JSON KB
        # where each entry is a single coherent fact, this is actually too large
        # — it concatenates multiple unrelated facts into one chunk. 600 chars
        # (~150 tokens) is the sweet spot: one entry fully fits, with some room
        # for the section header. This keeps each chunk semantically tight.
        default=600,
        description="Number of characters per chunk",
        ge=100,
        le=2000,
        validation_alias="CHUNK_SIZE"
    )

    chunk_overlap: int = Field(
        # IMPROVEMENT: With the structured JSON KB, each entry is self-contained
        # so large overlap just duplicates content and inflates the index.
        # 100 chars is enough to catch split sentences at boundaries.
        default=100,
        description="Number of overlapping characters between chunks",
        ge=0,
        le=500,
        validation_alias="CHUNK_OVERLAP"
    )

    # ============================================================
    # Vector Database Configuration
    # ============================================================
    chroma_db_dir: str = Field(
        default="chroma_db",
        description="Directory for persistent ChromaDB storage",
        validation_alias="CHROMA_DB_DIR"
    )

    collection_name: str = Field(
        default="bvrit_knowledge_base",
        description="ChromaDB collection name"
    )

    # ============================================================
    # LLM Inference Configuration
    # ============================================================
    llm_temperature: float = Field(
        # IMPROVEMENT: Temperature 0.0 is more appropriate for a FAQ chatbot
        # that must stick strictly to the knowledge base. Higher temperature
        # increases hallucination risk on factual questions. 0.0 makes the
        # model deterministic and grounded.
        default=0.0,
        description="LLM temperature (0.0 = deterministic, good for fact retrieval)",
        ge=0.0,
        le=1.0,
        validation_alias="LLM_TEMPERATURE"
    )

    llm_max_tokens: int = Field(
        # IMPROVEMENT: 512 is too short for questions that require listing
        # multiple departments, programs, or detailed admission procedures.
        # 1024 is a better default; allows complete answers without truncation.
        default=1024,
        description="Maximum tokens for LLM response",
        ge=128,
        le=4096,
        validation_alias="LLM_MAX_TOKENS"
    )

    # ============================================================
    # Retriever Configuration
    # ============================================================
    top_k: int = Field(
        # BUG FIX: top_k=5 is too low for a college FAQ KB that has 25+
        # categories. With only 5 chunks, multi-topic questions (e.g.
        # "tell me about departments and placements") often miss one topic
        # entirely. 8 gives better coverage without exceeding the LLM
        # context window.
        default=8,
        description="Number of chunks to retrieve",
        ge=1,
        le=20,
        validation_alias="TOP_K"
    )

    use_mmr: bool = Field(
        # IMPROVEMENT: Maximal Marginal Relevance (MMR) diversifies the
        # retrieved chunks so they don't all say the same thing. Without MMR,
        # all 8 top chunks can be near-duplicates of the same paragraph,
        # wasting the context window and causing the LLM to repeat the same
        # partial fact.
        default=True,
        description="Use Maximal Marginal Relevance for diversified retrieval",
        validation_alias="USE_MMR"
    )

    mmr_fetch_k: int = Field(
        # Fetch 20 candidates, then pick the 8 most diverse among them.
        default=20,
        description="Number of candidates to fetch before MMR re-ranking",
        ge=1,
        le=50,
        validation_alias="MMR_FETCH_K"
    )

    mmr_lambda: float = Field(
        # 0.6 balances relevance (λ=1.0) and diversity (λ=0.0).
        default=0.6,
        description="MMR lambda — balance between relevance and diversity",
        ge=0.0,
        le=1.0,
        validation_alias="MMR_LAMBDA"
    )

    # ============================================================
    # Streamlit Configuration
    # ============================================================
    streamlit_server_port: int = Field(
        default=8501,
        description="Streamlit server port",
        validation_alias="STREAMLIT_SERVER_PORT"
    )

    streamlit_server_headless: bool = Field(
        default=False,
        description="Run Streamlit in headless mode",
        validation_alias="STREAMLIT_SERVER_HEADLESS"
    )

    # ============================================================
    # Evaluation Configuration
    # ============================================================
    test_cases_path: str = Field(
        default="tests/generated_testcases.json",
        description="Path to generated test cases"
    )

    evaluation_report_path: str = Field(
        default="reports/evaluation_report.json",
        description="Path to evaluation report (JSON)"
    )

    evaluation_csv_path: str = Field(
        default="reports/evaluation_report.csv",
        description="Path to evaluation report (CSV)"
    )

    # ============================================================
    # Application Metadata
    # ============================================================
    app_name: str = Field(
        default="BVRIT Hyderabad College FAQ Chatbot",
        description="Application name"
    )

    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )

    debug_mode: bool = Field(
        default=False,
        description="Enable debug mode for verbose logging",
        validation_alias="DEBUG_MODE"
    )

    @field_validator("openrouter_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate that the API key is not empty."""
        if not v:
            logger.warning(
                "OPENROUTER_API_KEY is not set. "
                "Please set it in your .env file."
            )
        return v

    @field_validator("chunk_size")
    @classmethod
    def validate_chunk_size(cls, v: int) -> int:
        """Validate chunk size rationale."""
        if v == 800:
            logger.info(
                "Chunk size = 800: Balances between semantic coherence "
                "and granular retrieval. Each chunk contains roughly "
                "1-2 paragraphs of meaningful content, sufficient for "
                "the LLM to understand context without exceeding token limits."
            )
        return v

    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v: int) -> int:
        """Validate chunk overlap rationale."""
        if v == 150:
            logger.info(
                "Chunk overlap = 150: Ensures continuity between chunks. "
                "~19% overlap prevents information loss at chunk boundaries "
                "while avoiding excessive redundancy."
            )
        return v

    @property
    def chroma_db_path(self) -> Path:
        """Get the full path to ChromaDB directory."""
        return Path(self.chroma_db_dir)

    @property
    def document_file_path(self) -> Path:
        """Get the full path to the document."""
        return Path(self.document_path)

    def model_post_init(self, __context) -> None:
        """Post-initialization validation and logging."""
        logger.info(f"✅ Configuration loaded: {self.app_name} v{self.app_version}")
        logger.info(f"   LLM Model: {self.llm_model}")
        logger.info(f"   Temperature: {self.llm_temperature}, Max Tokens: {self.llm_max_tokens}")
        logger.info(f"   Embedding Model: {self.embedding_model}")
        logger.info(f"   Chunk Size: {self.chunk_size}, Overlap: {self.chunk_overlap}")
        logger.info(f"   Top-K: {self.top_k}, MMR: {self.use_mmr}")
        logger.info(f"   ChromaDB Path: {self.chroma_db_path}")
        logger.info(f"   Document Path: {self.document_file_path}")


@lru_cache()
def get_settings() -> Settings:
    """
    Return cached application settings instance.
    Uses lru_cache to ensure singleton behavior across modules.

    Returns:
        Settings: Application configuration object
    """
    return Settings()


# Create paths
def ensure_directories(settings: Settings) -> None:
    """
    Ensure all required directories exist.

    Args:
        settings: Application settings instance
    """
    directories = [
        settings.chroma_db_path,
        Path("data"),
        Path("prompts"),
        Path("tests"),
        Path("reports"),
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory: {directory}")


# Initialize settings and directories on module import
settings = get_settings()
ensure_directories(settings)