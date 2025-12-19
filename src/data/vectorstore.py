"""
Gestion du vectorstore FAISS pour la recherche sémantique RH.
Version singleton (chargement unique).
"""

from pathlib import Path
from typing import List, Dict, Optional

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from src.config.settings import settings
from src.core.exceptions import VectorStoreError
from src.data.loader import RHDataLoader


class RHVectorStore:
    """Gestion centralisée du vectorstore FAISS"""

    def __init__(self):
        self.persist_directory: Path = settings.vectorstore_full_path
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDINGS_MODEL
        )

        self.vectorstore: Optional[FAISS] = None

    # =========================
    # INITIALISATION
    # =========================

    def load_or_create(self, force_recreate: bool = False) -> FAISS:
        index_path = self.persist_directory / "index.faiss"

        if index_path.exists() and not force_recreate:
            return self._load()

        return self._create_from_csv()

    def _load(self) -> FAISS:
        try:
            print(" Chargement du vectorstore FAISS...")
            self.vectorstore = FAISS.load_local(
                folder_path=str(self.persist_directory),
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True
            )
            print("✅ Vectorstore chargé")
            return self.vectorstore

        except Exception as e:
            raise VectorStoreError(f"Erreur chargement vectorstore: {e}")

    def _create_from_csv(self) -> FAISS:
        try:
            print("🧱 Création du vectorstore depuis le CSV...")

            loader = RHDataLoader()
            loader.load_csv()
            documents = loader.to_documents()

            self.vectorstore = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings
            )

            self.vectorstore.save_local(str(self.persist_directory))
            print(" Vectorstore créé et sauvegardé")

            return self.vectorstore

        except Exception as e:
            raise VectorStoreError(f"Erreur création vectorstore: {e}")

    # =========================
    # RECHERCHE
    # =========================

    def search(
        self,
        query: str,
        k: int,
        filter_dict: Dict[str, str]
    ) -> List[Document]:
        if not self.vectorstore:
            raise VectorStoreError("Vectorstore non initialisé")

        return self.vectorstore.similarity_search(
            query=query,
            k=k,
            filter=filter_dict
        )


# =========================
# SINGLETON GLOBAL
# =========================

_VECTORSTORE_INSTANCE: Optional[RHVectorStore] = None


def get_vectorstore(force_recreate: bool = False) -> RHVectorStore:
    global _VECTORSTORE_INSTANCE

    if _VECTORSTORE_INSTANCE is None:
        print(" Initialisation singleton vectorstore")
        _VECTORSTORE_INSTANCE = RHVectorStore()
        _VECTORSTORE_INSTANCE.load_or_create(force_recreate)

    return _VECTORSTORE_INSTANCE
