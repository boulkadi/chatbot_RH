"""
Configuration centralisée du projet RH Assistant.
Toutes les variables d'environnement et paramètres sont gérés ici.
"""

from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration de l'application RH Assistant"""
    
    # ============================================
    # PATHS - Adaptés pour Windows
    # ============================================
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_CSV_PATH: str = "data/RH_infos.csv"
    VECTORSTORE_PATH: str = "data/vectorstore"
    
    @property
    def csv_full_path(self) -> Path:
        """Chemin complet du CSV (compatible Windows)"""
        return self.BASE_DIR / self.DATA_CSV_PATH
    
    @property
    def vectorstore_full_path(self) -> Path:
        """Chemin complet du vectorstore (compatible Windows)"""
        return self.BASE_DIR / self.VECTORSTORE_PATH
    
    # ============================================
    # API KEYS
    # ============================================
    GEMINI_API_KEY: str
    
    # ============================================
    # LLM CONFIGURATION
    # ============================================
    LLM_MODEL: str = "gemini-2.5-flash"
    LLM_TEMPERATURE: float = 0.5
    SUMMARIZATION_MODEL: str = "gemini-2.5-flash"
    
    # ============================================
    # EMBEDDINGS
    # ============================================
    EMBEDDINGS_MODEL: str = "sentence-transformers/all-MiniLM-L12-v2"
    
    # ============================================
    # FASTAPI CONFIGURATION
    # ============================================
    API_HOST: str = "127.0.0.1"  # localhost pour Windows
    API_PORT: int = 8000
    API_RELOAD: bool = True
    API_TITLE: str = "RH Assistant API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "API pour l'assistant RH intelligent"
    
    # ============================================
    # STREAMLIT CONFIGURATION
    # ============================================
    STREAMLIT_PORT: int = 8501
    
    # ============================================
    # AGENT CONFIGURATION
    # ============================================
    AGENT_MAX_ITERATIONS: int = 10
    AGENT_MEMORY_TYPE: Literal["in_memory"] = "in_memory"
    AGENT_SUMMARY_TRIGGER_TOKENS: int = 1000
    AGENT_KEEP_MESSAGES: int = 5
    
    # ============================================
    # VECTOR SEARCH
    # ============================================
    VECTORSTORE_K: int = 4
    VECTORSTORE_TYPE: Literal["faiss"] = "faiss"
    
    # ============================================
    # LOGGING
    # ============================================
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    
    # ============================================
    # PROFILS ET DOMAINES RH
    # ============================================
    VALID_PROFILES: list[str] = [
        "CDI", "CDD", "Intérim", "Cadre", "Non-Cadre", "Stagiaire"
    ]
    
    VALID_DOMAINS: list[str] = [
        "Congés", "Avantages", "Transport", "Temps de travail", "Paie"
    ]
    
    # Configuration Pydantic pour charger depuis .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    def validate_paths(self) -> None:
        """Valide que les chemins critiques existent"""
        if not self.csv_full_path.exists():
            raise FileNotFoundError(
                f"Le fichier CSV n'existe pas: {self.csv_full_path}"
            )
        
        # Créer le dossier vectorstore s'il n'existe pas
        self.vectorstore_full_path.mkdir(parents=True, exist_ok=True)
    
    def __repr__(self) -> str:
        """Représentation sécurisée (masque l'API key)"""
        return (
            f"Settings("
            f"LLM={self.LLM_MODEL}, "
            f"CSV={self.csv_full_path.name}, "
            f"API_PORT={self.API_PORT})"
        )


# Instance globale singleton
settings = Settings()


# Validation au démarrage
try:
    settings.validate_paths()
    print(f"✅ Configuration chargée avec succès: {settings}")
except Exception as e:
    print(f"⚠️ Avertissement de configuration: {e}")