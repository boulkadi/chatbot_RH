"""
Modèles de données Pydantic pour validation et typage.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


# ============================================
# TYPES PERSONNALISÉS
# ============================================

ProfileType = Literal["CDI", "CDD", "Intérim", "Cadre", "Non-Cadre", "Stagiaire"]
DomaineType = Literal["Congés", "Avantages", "Transport", "Temps de travail", "Paie"]


# ============================================
# MODÈLES DE DONNÉES RH
# ============================================

class RHQuestion(BaseModel):
    """Représentation d'une question/réponse RH depuis le CSV"""
    
    question_id: int = Field(..., description="Identifiant unique de la question")
    profil: ProfileType = Field(..., description="Type de profil concerné")
    domaine: DomaineType = Field(..., description="Domaine RH")
    question: str = Field(..., min_length=5, description="Question posée")
    reponse: str = Field(..., min_length=10, description="Réponse associée")
    
    @field_validator("question", "reponse")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Valide que les champs ne sont pas vides après strip"""
        if not v.strip():
            raise ValueError("Le champ ne peut pas être vide")
        return v.strip()


# ============================================
# MODÈLES DE REQUÊTE API
# ============================================

class UserQuery(BaseModel):
    """Requête utilisateur pour l'API"""
    
    query: str = Field(
        ..., 
        min_length=3, 
        max_length=500,
        description="Question de l'utilisateur"
    )
    user_profile: ProfileType = Field(
        ..., 
        description="Type de contrat de l'utilisateur"
    )
    domaine: Optional[DomaineType] = Field(
        None, 
        description="Domaine RH spécifique (optionnel)"
    )
    thread_id: Optional[str] = Field(
        None,
        description="ID de conversation pour la mémoire"
    )
    
    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Nettoie et valide la requête"""
        cleaned = v.strip()
        if len(cleaned) < 3:
            raise ValueError("La question doit contenir au moins 3 caractères")
        return cleaned


class AgentResponse(BaseModel):
    """Réponse de l'agent RH"""
    
    response: str = Field(..., description="Réponse de l'agent")
    thread_id: str = Field(..., description="ID de la conversation")
    sources_used: bool = Field(
        default=False, 
        description="Indique si des sources ont été trouvées"
    )
    error: Optional[str] = Field(
        None, 
        description="Message d'erreur si applicable"
    )


# ============================================
# MODÈLES POUR LES OUTILS LANGCHAIN
# ============================================

class RHSearchInput(BaseModel):
    """
    Input pour l'outil de recherche RH.
    Utilisé par LangChain pour valider les arguments.
    """
    
    query: str = Field(
        ..., 
        description="La question de l'utilisateur"
    )
    user_profile: ProfileType = Field(
        ..., 
        description="Le type de contrat de l'utilisateur"
    )
    domaine: Optional[DomaineType] = Field(
        None, 
        description="Le domaine RH concerné par la question"
    )


# ============================================
# MODÈLES DE STATISTIQUES
# ============================================

class AgentStats(BaseModel):
    """Statistiques d'utilisation de l'agent"""
    
    total_queries: int = 0
    successful_responses: int = 0
    failed_responses: int = 0
    average_response_time: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calcule le taux de succès"""
        if self.total_queries == 0:
            return 0.0
        return (self.successful_responses / self.total_queries) * 100


# ============================================
# MODÈLES DE CONFIGURATION STREAMLIT
# ============================================

class StreamlitSession(BaseModel):
    """État de la session Streamlit"""
    
    user_profile: Optional[ProfileType] = None
    thread_id: str = Field(default_factory=lambda: f"session_{id(object())}")
    conversation_history: list[dict] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True