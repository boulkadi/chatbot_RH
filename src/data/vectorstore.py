"""
Gestion du vectorstore FAISS pour la recherche sémantique.
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
    """Gestion du vectorstore FAISS pour les données RH"""
    
    def __init__(
        self,
        embeddings_model: str = None,
        persist_directory: Path = None
    ):
        """
        Initialise le vectorstore.
        
        Args:
            embeddings_model: Nom du modèle d'embeddings
            persist_directory: Dossier de sauvegarde du vectorstore
        """
        self.embeddings_model = embeddings_model or settings.EMBEDDINGS_MODEL
        self.persist_directory = persist_directory or settings.vectorstore_full_path
        
        # Créer le dossier si nécessaire
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialiser les embeddings
        print(f" Initialisation des embeddings: {self.embeddings_model}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.embeddings_model
        )
        
        self.vectorstore: Optional[FAISS] = None
    
    def create_from_documents(
        self,
        documents: List[Document],
        save: bool = True
    ) -> FAISS:
        """
        Crée le vectorstore à partir des documents.
        
        Args:
            documents: Liste de Documents LangChain
            save: Si True, sauvegarde sur disque
            
        Returns:
            Instance FAISS du vectorstore
        """
        try:
            print(f" Création du vectorstore avec {len(documents)} documents...")
            
            self.vectorstore = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings
            )
            
            print("Vectorstore créé avec succès")
            
            if save:
                self.save()
            
            return self.vectorstore
            
        except Exception as e:
            raise VectorStoreError(
                f"Erreur lors de la création du vectorstore: {e}",
                {"error_type": type(e).__name__}
            )
    
    def load(self) -> FAISS:
        """
        Charge le vectorstore depuis le disque.
        
        Returns:
            Instance FAISS chargée
            
        Raises:
            VectorStoreError: Si le chargement échoue
        """
        try:
            index_path = self.persist_directory / "index.faiss"
            
            if not index_path.exists():
                raise FileNotFoundError(
                    f"Vectorstore non trouvé dans: {self.persist_directory}"
                )
            
            print(f" Chargement du vectorstore depuis: {self.persist_directory}")
            
            self.vectorstore = FAISS.load_local(
                folder_path=str(self.persist_directory),
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True  # Nécessaire pour FAISS
            )
            
            print(" Vectorstore chargé avec succès")
            return self.vectorstore
            
        except FileNotFoundError as e:
            raise VectorStoreError(
                f"Vectorstore non trouvé: {e}",
                {"persist_directory": str(self.persist_directory)}
            )
        except Exception as e:
            raise VectorStoreError(
                f"Erreur lors du chargement: {e}",
                {"error_type": type(e).__name__}
            )
    
    def save(self) -> None:
        """
        Sauvegarde le vectorstore sur disque.
        
        Raises:
            VectorStoreError: Si la sauvegarde échoue
        """
        if not self.vectorstore:
            raise VectorStoreError(
                "Aucun vectorstore à sauvegarder",
                {"action": "Créez d'abord le vectorstore avec create_from_documents()"}
            )
        
        try:
            print(f" Sauvegarde du vectorstore dans: {self.persist_directory}")
            
            self.vectorstore.save_local(
                folder_path=str(self.persist_directory)
            )
            
            print(" Vectorstore sauvegardé avec succès")
            
        except Exception as e:
            raise VectorStoreError(
                f"Erreur lors de la sauvegarde: {e}",
                {"persist_directory": str(self.persist_directory)}
            )
    
    def search(
        self,
        query: str,
        k: int = None,
        filter_dict: Dict[str, str] = None
    ) -> List[Document]:
        """
        Recherche sémantique dans le vectorstore.
        
        Args:
            query: Question de recherche
            k: Nombre de résultats à retourner
            filter_dict: Filtres sur les métadonnées (profil, domaine)
            
        Returns:
            Liste de Documents pertinents
        """
        if not self.vectorstore:
            raise VectorStoreError(
                "Vectorstore non initialisé",
                {"action": "Chargez ou créez le vectorstore"}
            )
        
        k = k or settings.VECTORSTORE_K
        
        try:
            results = self.vectorstore.similarity_search(
                query=query,
                k=k,
                filter=filter_dict
            )
            
            return results
            
        except Exception as e:
            raise VectorStoreError(
                f"Erreur lors de la recherche: {e}",
                {"query": query, "filter": filter_dict}
            )
    
    def get_or_create(self, force_recreate: bool = False) -> FAISS:
        """
        Charge le vectorstore existant ou le crée s'il n'existe pas.
        
        Args:
            force_recreate: Si True, recrée même si existe déjà
            
        Returns:
            Instance FAISS du vectorstore
        """
        index_path = self.persist_directory / "index.faiss"
        
        # Si existe et pas de recréation forcée, charger
        if index_path.exists() and not force_recreate:
            print("Vectorstore existant détecté, chargement...")
            return self.load()
        
        # Sinon, créer depuis les données CSV
        print(" Création d'un nouveau vectorstore...")
        
        # Charger les données
        loader = RHDataLoader()
        loader.load_csv()
        documents = loader.to_documents()
        
        # Créer le vectorstore
        return self.create_from_documents(documents, save=True)
    
    def add_documents(self, documents: List[Document]) -> None:
        """
        Ajoute des documents au vectorstore existant.
        
        Args:
            documents: Documents à ajouter
        """
        if not self.vectorstore:
            raise VectorStoreError(
                "Vectorstore non initialisé",
                {"action": "Chargez ou créez le vectorstore"}
            )
        
        try:
            self.vectorstore.add_documents(documents)
            print(f" {len(documents)} documents ajoutés")
            
        except Exception as e:
            raise VectorStoreError(
                f"Erreur lors de l'ajout de documents: {e}"
            )
    
    def delete(self) -> None:
        """Supprime le vectorstore du disque"""
        try:
            import shutil
            
            if self.persist_directory.exists():
                shutil.rmtree(self.persist_directory)
                print(f" Vectorstore supprimé: {self.persist_directory}")
                self.vectorstore = None
            else:
                print(" Aucun vectorstore à supprimer")
                
        except Exception as e:
            raise VectorStoreError(
                f"Erreur lors de la suppression: {e}"
            )


# ============================================
# FONCTION HELPER POUR USAGE SIMPLE
# ============================================

def get_vectorstore(force_recreate: bool = False) -> FAISS:
    """
    Fonction helper pour obtenir rapidement le vectorstore.
    
    Args:
        force_recreate: Forcer la recréation
        
    Returns:
        Instance FAISS du vectorstore
    """
    vs = RHVectorStore()
    return vs.get_or_create(force_recreate=force_recreate)


# ============================================
# EXEMPLE D'UTILISATION
# ============================================

if __name__ == "__main__":
    # Test du vectorstore
    try:
        print("=== Test RHVectorStore ===\n")
        
        # Option 1: Créer/Charger automatiquement
        vs = RHVectorStore()
        vectorstore = vs.get_or_create(force_recreate=False)
        
        # Test de recherche
        print("\n Test de recherche:")
        query = "congés payés CDI"
        results = vs.search(
            query=query,
            k=3,
            filter_dict={"profil": "CDI"}
        )
        
        print(f"\nRésultats pour '{query}':")
        for i, doc in enumerate(results, 1):
            print(f"\n{i}. {doc.metadata}")
            print(f"   {doc.page_content[:100]}...")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")