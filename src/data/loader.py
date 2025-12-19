"""
Chargement et validation des données RH depuis le fichier CSV.
"""

import json
from pathlib import Path
from typing import List

import pandas as pd
from langchain_core.documents import Document

from src.config.settings import settings
from src.core.models import RHQuestion
from src.core.exceptions import (
    CSVLoadError,
    InvalidDataFormatError,
    DataError
)


class RHDataLoader:
    """Charge et valide les données RH depuis le CSV"""
    
    def __init__(self, csv_path: Path = None):
        """
        Initialise le loader avec le chemin du CSV.
        
        Args:
            csv_path: Chemin vers le CSV (utilise settings par défaut)
        """
        self.csv_path = csv_path or settings.csv_full_path
        self._data: List[RHQuestion] = []
        self._df: pd.DataFrame = None
    
    def load_csv(self) -> List[RHQuestion]:
        """
        Charge le CSV et le valide avec Pydantic.
        
        Returns:
            Liste de RHQuestion validées
            
        Raises:
            CSVLoadError: Si le fichier ne peut pas être chargé
            InvalidDataFormatError: Si le format est invalide
        """
        try:
            # Vérifier que le fichier existe
            if not self.csv_path.exists():
                raise FileNotFoundError(f"Fichier introuvable: {self.csv_path}")
            
            # Charger le CSV
            print(f"📂 Chargement du CSV: {self.csv_path}")
            self._df = pd.read_csv(
                self.csv_path,
                sep=",",
                engine="python",
                encoding="utf-8"
            )
            
            # Remplir les valeurs manquantes
            self._df = self._df.fillna("")
            
            # Vérifier les colonnes requises
            required_columns = ["question_id", "profil", "domaine", "question", "reponse"]
            missing_columns = set(required_columns) - set(self._df.columns)
            
            if missing_columns:
                raise InvalidDataFormatError(
                    expected_format=f"Colonnes requises: {required_columns}",
                    received_format=f"Colonnes manquantes: {missing_columns}"
                )
            
            # Valider et convertir chaque ligne en RHQuestion
            validated_data = []
            errors = []
            
            for index, row in self._df.iterrows():
                try:
                    question = RHQuestion(
                        question_id=int(row["question_id"]) if row["question_id"] else index + 1,
                        profil=str(row["profil"]).strip(),
                        domaine=str(row["domaine"]).strip(),
                        question=str(row["question"]).strip(),
                        reponse=str(row["reponse"]).strip()
                    )
                    validated_data.append(question)
                    
                except Exception as e:
                    errors.append({
                        "ligne": index + 2,  # +2 car index commence à 0 et ligne 1 = headers
                        "erreur": str(e)
                    })
            
            # Si trop d'erreurs, lever une exception
            if len(errors) > len(self._df) * 0.1:  # Plus de 10% d'erreurs
                raise InvalidDataFormatError(
                    expected_format="Données valides selon le modèle RHQuestion",
                    received_format=f"{len(errors)} erreurs de validation: {errors[:5]}"
                )
            
            # Afficher les warnings si quelques erreurs
            if errors:
                print(f"⚠️ {len(errors)} lignes ignorées (erreurs de validation)")
                for err in errors[:3]:  # Afficher les 3 premières
                    print(f"   Ligne {err['ligne']}: {err['erreur']}")
            
            self._data = validated_data
            print(f"✅ {len(self._data)} questions RH chargées avec succès")
            
            return self._data
            
        except FileNotFoundError as e:
            raise CSVLoadError(str(self.csv_path), e)
        except pd.errors.EmptyDataError as e:
            raise CSVLoadError(str(self.csv_path), e)
        except Exception as e:
            if isinstance(e, (CSVLoadError, InvalidDataFormatError)):
                raise
            raise CSVLoadError(str(self.csv_path), e)
    
    def to_documents(self) -> List[Document]:
        """
        Convertit les données RH en Documents LangChain.
        
        Returns:
            Liste de Documents avec métadonnées
        """
        if not self._data:
            raise DataError("Aucune donnée chargée. Appelez load_csv() d'abord.")
        
        documents = []
        
        for item in self._data:
            # Contenu pour le vectorstore
            page_content = f"Question: {item.question}\nRéponse: {item.reponse}"
            
            # Métadonnées pour le filtrage
            metadata = {
                "profil": item.profil,
                "domaine": item.domaine,
                "question_id": item.question_id
            }
            
            documents.append(
                Document(page_content=page_content, metadata=metadata)
            )
        
        print(f" {len(documents)} documents créés pour le vectorstore")
        return documents
    
    def to_json(self, output_path: Path = None) -> str:
        """
        Exporte les données en JSON (pour debug/backup).
        
        Args:
            output_path: Chemin du fichier JSON de sortie
            
        Returns:
            JSON string
        """
        if not self._data:
            raise DataError("Aucune donnée chargée. Appelez load_csv() d'abord.")
        
        json_data = [item.model_dump() for item in self._data]
        json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
        
        if output_path:
            output_path.write_text(json_str, encoding="utf-8")
            print(f"💾 Données exportées vers: {output_path}")
        
        return json_str
    
    def get_stats(self) -> dict:
        """
        Retourne des statistiques sur les données chargées.
        
        Returns:
            Dictionnaire de statistiques
        """
        if not self._data:
            return {"total": 0}
        
        stats = {
            "total": len(self._data),
            "par_profil": {},
            "par_domaine": {}
        }
        
        for item in self._data:
            # Compter par profil
            stats["par_profil"][item.profil] = stats["par_profil"].get(item.profil, 0) + 1
            
            # Compter par domaine
            stats["par_domaine"][item.domaine] = stats["par_domaine"].get(item.domaine, 0) + 1
        
        return stats
    
    @property
    def data(self) -> List[RHQuestion]:
        """Accès en lecture seule aux données"""
        return self._data.copy()


# ============================================
# FONCTION HELPER POUR USAGE SIMPLE
# ============================================

def load_rh_data() -> List[RHQuestion]:
    """
    Fonction helper pour charger rapidement les données RH.
    
    Returns:
        Liste de RHQuestion validées
    """
    loader = RHDataLoader()
    return loader.load_csv()


# ============================================
# EXEMPLE D'UTILISATION
# ============================================

if __name__ == "__main__":
    # Test du loader
    try:
        loader = RHDataLoader()
        data = loader.load_csv()
        
        print("\n📊 Statistiques:")
        stats = loader.get_stats()
        print(f"Total: {stats['total']} questions")
        print(f"Par profil: {stats['par_profil']}")
        print(f"Par domaine: {stats['par_domaine']}")
        
        # Test conversion en documents
        docs = loader.to_documents()
        print(f"\n✅ {len(docs)} documents prêts pour le vectorstore")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")