"""
Agent RH principal utilisant LangGraph.
Gère la conversation et la recherche d'informations RH.
"""

from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langgraph.checkpoint.memory import InMemorySaver

from src.config.settings import settings
from src.core.models import UserQuery, AgentResponse
from src.core.exceptions import (
    AgentError,
    ProfileNotProvidedError,
    LLMError
)
from src.agents.tools import get_tools_list


class RHAgent:
    """Agent RH intelligent avec LangGraph"""
    
    # Prompt système pour l'agent
    SYSTEM_PROMPT = """Tu es l'assistant RH intelligent de Safran.
Ton rôle est d'informer les collaborateurs sur les congés, la paie, le transport, etc.

### RÈGLES DE RÉPONSE ET SÉCURITÉ :

1. **UTILISATION DES OUTILS** : Tu ne peux répondre qu'en utilisant l'outil 'search_rh_expert'.

2. **PROFILAGE OBLIGATOIRE** : Pour utiliser cet outil, tu DOIS connaître le profil (CDI, CDD, Intérim, Cadre, Non-Cadre, Stagiaire).
   - Si le profil est inconnu, demande-le poliment avant toute recherche.
   - Exemple: "Pour vous aider au mieux, pouvez-vous me préciser votre type de contrat ?"

3. **DOMAINE** : Identifie le domaine concerné (Congés, Paie, Transport, Temps de travail, Avantages) pour affiner la recherche.

4. **GESTION DES ERREURS (STRICT)** :
   - Si l'outil renvoie "ERREUR_NOT_FOUND", tu dois répondre exactement :
     "Désolé, je ne peux pas répondre à cette question précisément avec les données actuelles. Veuillez contacter le service RH."
   - Si l'outil renvoie "ERREUR_TECHNIQUE", informe l'utilisateur qu'un problème technique est survenu.

5. **FORMAT** :
   - Réponds de manière concise, professionnelle et claire
   - Utilise des listes à puces pour les informations multiples
   - Utilise des tableaux Markdown pour les chiffres comparatifs
   - Reste courtois et empathique

6. **LIMITES** :
   - Ne réponds JAMAIS sans utiliser l'outil
   - N'invente JAMAIS d'information
   - Si tu n'es pas sûr, renvoie vers le service RH

### EXEMPLES DE BONNES RÉPONSES :

**Question:** "Combien de jours de congés j'ai ?"
**Réponse:** "Pour vous répondre précisément, j'ai besoin de connaître votre type de contrat. Êtes-vous en CDI, CDD, Intérim, Cadre, Non-Cadre ou Stagiaire ?"

**Question (avec profil):** "Je suis en CDI, combien de jours de congés ?"
**Action:** Utilise search_rh_expert avec profil="CDI" et domaine="Congés"
**Réponse:** [Résultats de l'outil formatés de manière claire]
"""
    
    def __init__(
        self,
        api_key: str = None,
        model_name: str = None,
        temperature: float = None
    ):
        """
        Initialise l'agent RH.
        
        Args:
            api_key: Clé API Gemini (utilise settings par défaut)
            model_name: Nom du modèle (utilise settings par défaut)
            temperature: Température du modèle (utilise settings par défaut)
        """
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.LLM_MODEL
        self.temperature = temperature or settings.LLM_TEMPERATURE
        
        # Initialiser le LLM
        self.llm = self._initialize_llm()
        
        # Initialiser le LLM de summarization
        self.summarization_llm = ChatGoogleGenerativeAI(
            model=settings.SUMMARIZATION_MODEL,
            google_api_key=self.api_key
        )
        
        # Initialiser la mémoire
        self.memory = InMemorySaver()
        
        # Middleware de summarization
        self.summary_middleware = SummarizationMiddleware(
            model=self.summarization_llm,
            trigger=("tokens", settings.AGENT_SUMMARY_TRIGGER_TOKENS),
            keep=("messages", settings.AGENT_KEEP_MESSAGES)
        )
        
        # Créer l'agent
        self.agent_executor = self._create_agent()
        
        print("✅ Agent RH initialisé")
    
    def _initialize_llm(self) -> ChatGoogleGenerativeAI:
        """Initialise le modèle LLM"""
        try:
            return ChatGoogleGenerativeAI(
                model=self.model_name,
                temperature=self.temperature,
                google_api_key=self.api_key
            )
        except Exception as e:
            raise LLMError(
                f"Erreur d'initialisation du LLM: {e}",
                {"model": self.model_name}
            )
    
    def _create_agent(self):
        """Crée l'agent LangGraph avec les outils"""
        try:
            tools = get_tools_list()
            
            agent = create_agent(
                model=self.llm,
                tools=tools,
                system_prompt=self.SYSTEM_PROMPT,
                checkpointer=self.memory,
                middleware=[self.summary_middleware]
            )
            
            return agent
            
        except Exception as e:
            raise AgentError(
                f"Erreur de création de l'agent: {e}"
            )
    
    def invoke(
        self,
        query: UserQuery,
        config: Dict[str, Any] = None
    ) -> AgentResponse:
        """
        Invoque l'agent avec une requête utilisateur.
        
        Args:
            query: Requête utilisateur validée
            config: Configuration optionnelle (thread_id, etc.)
            
        Returns:
            Réponse de l'agent
        """
        try:
            # Configuration par défaut
            if config is None:
                config = {
                    "configurable": {
                        "thread_id": query.thread_id or "default"
                    }
                }
            
            # Construire le message avec le profil
            user_message = query.query
            if query.user_profile:
                user_message = f"[Profil: {query.user_profile}] {query.query}"
            
            # Appeler l'agent
            result = self.agent_executor.invoke(
                {"messages": [("user", user_message)]},
                config
            )
            
            # Extraire la réponse
            response_content = self._extract_response(result)
            
            # Vérifier si des sources ont été utilisées
            sources_used = "ERREUR_NOT_FOUND" not in response_content
            
            return AgentResponse(
                response=response_content,
                thread_id=config["configurable"]["thread_id"],
                sources_used=sources_used,
                error=None
            )
            
        except Exception as e:
            error_msg = str(e)
            
            # Réponse d'erreur friendly
            return AgentResponse(
                response=(
                    "Je rencontre une difficulté technique. "
                    "Veuillez réessayer ou contacter le service RH."
                ),
                thread_id=config.get("configurable", {}).get("thread_id", "error"),
                sources_used=False,
                error=error_msg
            )
    
    def _extract_response(self, result: Dict[str, Any]) -> str:
        """
        Extrait le contenu de la réponse de l'agent.
        
        Args:
            result: Résultat brut de l'agent
            
        Returns:
            Contenu de la réponse nettoyé
        """
        try:
            last_msg_content = result['messages'][-1].content
            
            # Gestion du format liste ou string
            if isinstance(last_msg_content, list) and len(last_msg_content) > 0:
                return last_msg_content[0].get('text', str(last_msg_content))
            elif isinstance(last_msg_content, str):
                return last_msg_content
            else:
                return str(last_msg_content)
                
        except Exception as e:
            raise AgentError(f"Erreur d'extraction de la réponse: {e}")
    
    def chat(
        self,
        message: str,
        user_profile: str,
        domaine: Optional[str] = None,
        thread_id: str = "default"
    ) -> str:
        """
        Interface simplifiée pour chatter avec l'agent.
        
        Args:
            message: Message de l'utilisateur
            user_profile: Profil du salarié
            domaine: Domaine RH optionnel
            thread_id: ID du fil de conversation
            
        Returns:
            Réponse de l'agent en string
        """
        query = UserQuery(
            query=message,
            user_profile=user_profile,
            domaine=domaine,
            thread_id=thread_id
        )
        
        response = self.invoke(query)
        return response.response


# ============================================
# FONCTION HELPER
# ============================================

_agent_instance = None

def get_rh_agent() -> RHAgent:
    """Retourne l'instance singleton de l'agent RH"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = RHAgent()
    return _agent_instance


# ============================================
# EXEMPLE D'UTILISATION
# ============================================

if __name__ == "__main__":
    print("=== Test de l'Agent RH ===\n")
    
    try:
        # Initialiser l'agent
        agent = RHAgent()
        
        # Test 1: Question avec profil
        print("Test 1: Question sur les congés (CDI)")
        response = agent.chat(
            message="Combien de jours de congés payés j'ai ?",
            user_profile="CDI",
            domaine="Congés",
            thread_id="test_1"
        )
        print(f"Agent: {response}")
        print("\n" + "="*70 + "\n")
        
        # Test 2: Question de suivi (même thread)
        print("Test 2: Question de suivi")
        response = agent.chat(
            message="Et comment je les pose ?",
            user_profile="CDI",
            thread_id="test_1"  # Même thread = mémoire
        )
        print(f"Agent: {response}")
        print("\n" + "="*70 + "\n")
        
        # Test 3: Nouvelle conversation
        print("Test 3: Question transport (Cadre)")
        response = agent.chat(
            message="Quels sont les avantages transport ?",
            user_profile="Cadre",
            domaine="Transport",
            thread_id="test_2"
        )
        print(f"Agent: {response}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()