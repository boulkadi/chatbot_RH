"""
Outils LangChain pour l'agent RH.
Définit les capacités de recherche de l'agent.
"""

from typing import Optional
from langchain.tools import tool

from src.config.settings import settings
from src.core.models import RHSearchInput
from src.core.exceptions import NoAnswerFoundError
from src.data.vectorstore import get_vectorstore


class RHTools:
    """Collection d'outils pour l'agent RH"""
    
    def __init__(self):
        """Initialise les outils avec le vectorstore"""
        self.vectorstore = None
        self._initialize_vectorstore()
    
    def _initialize_vectorstore(self):
        """Initialise ou charge le vectorstore"""
        try:
            print(" Initialisation du vectorstore pour les outils...")
            self.vectorstore = get_vectorstore(force_recreate=False)
            print(" Vectorstore prêt")
        except Exception as e:
            print(f"❌ Erreur initialisation vectorstore: {e}")
            raise
    
    def search_rh_knowledge(
        self,
        query: str,
        user_profile: str,
        domaine: Optional[str] = None
    ) -> str:
        """
        Recherche dans la base de connaissances RH.
        
        Args:
            query: Question de l'utilisateur
            user_profile: Profil du salarié (CDI, CDD, etc.)
            domaine: Domaine RH optionnel (Congés, Paie, etc.)
            
        Returns:
            Résultats de recherche formatés ou message d'erreur
        """
        try:
            # Construction du filtre
            search_filter = {"profil": user_profile}
            if domaine:
                search_filter["domaine"] = domaine
            
            # Recherche dans le vectorstore
            from src.data.vectorstore import RHVectorStore
            vs = RHVectorStore()
            vs.vectorstore = self.vectorstore
            
            docs = vs.search(
                query=query,
                k=settings.VECTORSTORE_K,
                filter_dict=search_filter
            )
            
            # Si aucun résultat
            if not docs:
                return (
                    "ERREUR_NOT_FOUND: Je ne trouve pas de procédure spécifique "
                    "pour votre profil et cette question. "
                    "Veuillez contacter le service RH ou consulter le portail SAP."
                )
            
            # Formater les résultats
            results = []
            for i, doc in enumerate(docs, 1):
                results.append(f"--- Résultat {i} ---")
                results.append(doc.page_content)
                results.append(f"(Profil: {doc.metadata.get('profil')}, "
                             f"Domaine: {doc.metadata.get('domaine')})")
                results.append("")
            
            return "\n".join(results)
            
        except Exception as e:
            return (
                f"ERREUR_TECHNIQUE: Une erreur s'est produite lors de la recherche. "
                f"Détails: {str(e)}"
            )


# ============================================
# OUTIL LANGCHAIN AVEC VALIDATION PYDANTIC
# ============================================

# Instance globale des outils
_rh_tools_instance = None

def get_rh_tools() -> RHTools:
    """Retourne l'instance singleton des outils RH"""
    global _rh_tools_instance
    if _rh_tools_instance is None:
        _rh_tools_instance = RHTools()
    return _rh_tools_instance


@tool(args_schema=RHSearchInput)
def search_rh_expert(query: str, user_profile: str, domaine: str = None) -> str:
    """
    Recherche précise par profil et domaine RH (Congés, Paie, etc.).
    
    Cet outil permet de trouver des réponses spécifiques aux questions RH
    en filtrant par profil de salarié et domaine concerné.
    
    Args:
        query: La question de l'utilisateur
        user_profile: Le type de contrat (CDI, CDD, Intérim, Cadre, Non-Cadre, Stagiaire)
        domaine: Le domaine RH (Congés, Avantages, Transport, Temps de travail, Paie)
    
    Returns:
        Réponses pertinentes de la base de connaissances RH
    """
    tools = get_rh_tools()
    return tools.search_rh_knowledge(query, user_profile, domaine)


# ============================================
# LISTE DES OUTILS DISPONIBLES
# ============================================

def get_tools_list():
    """Retourne la liste des outils disponibles pour l'agent"""
    return [search_rh_expert]


# ============================================
# EXEMPLE D'UTILISATION
# ============================================

if __name__ == "__main__":
    print("=== Test des outils RH ===\n")
    
    try:
        # Initialiser les outils
        tools = RHTools()
        
        # Test 1: Recherche avec profil CDI
        print("Test 1: Congés CDI")
        result = tools.search_rh_knowledge(
            query="Combien de jours de congés payés ?",
            user_profile="CDI",
            domaine="Congés"
        )
        print(result)
        print("\n" + "="*50 + "\n")
        
        # Test 2: Recherche sans domaine
        print("Test 2: Question générale CDD")
        result = tools.search_rh_knowledge(
            query="Comment demander un arrêt maladie ?",
            user_profile="CDD"
        )
        print(result)
        print("\n" + "="*50 + "\n")
        
        # Test 3: Via l'outil LangChain
        print("Test 3: Utilisation via l'outil LangChain")
        from langchain.tools import tool
        
        # Simuler un appel de l'outil
        result = search_rh_expert.invoke({
            "query": "transport",
            "user_profile": "Cadre",
            "domaine": "Transport"
        })
        print(result)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()