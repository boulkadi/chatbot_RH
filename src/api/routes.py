"""
Routes et endpoints de l'API RH Assistant.
"""

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.agents.rh_agent import get_rh_agent
from src.core.models import UserQuery, AgentResponse, ProfileType, DomaineType
from src.config.settings import settings


router = APIRouter()


# ============================================
# MODÈLES DE REQUÊTE/RÉPONSE SUPPLÉMENTAIRES
# ============================================

class ChatRequest(BaseModel):
    """Requête pour le chat"""
    message: str = Field(..., min_length=3, description="Message de l'utilisateur")
    user_profile: ProfileType = Field(..., description="Profil du salarié")
    domaine: DomaineType | None = Field(None, description="Domaine RH")
    thread_id: str | None = Field(None, description="ID de conversation")


class ChatResponse(BaseModel):
    """Réponse du chat"""
    response: str = Field(..., description="Réponse de l'agent")
    thread_id: str = Field(..., description="ID de la conversation")
    sources_used: bool = Field(..., description="Sources trouvées")


class ProfilesResponse(BaseModel):
    """Liste des profils disponibles"""
    profiles: List[str]


class DomainsResponse(BaseModel):
    """Liste des domaines disponibles"""
    domains: List[str]


# ============================================
# ENDPOINTS
# ============================================

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint principal pour chatter avec l'agent RH.
    
    Permet de poser une question à l'assistant RH en spécifiant
    le profil du salarié et optionnellement le domaine concerné.
    """
    try:
        agent = get_rh_agent()
        
        # Créer la requête
        query = UserQuery(
            query=request.message,
            user_profile=request.user_profile,
            domaine=request.domaine,
            thread_id=request.thread_id
        )
        
        # Appeler l'agent
        response = agent.invoke(query)
        
        return ChatResponse(
            response=response.response,
            thread_id=response.thread_id,
            sources_used=response.sources_used
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement: {str(e)}"
        )


@router.post("/query", response_model=AgentResponse)
async def query(request: UserQuery):
    """
    Endpoint alternatif avec modèle UserQuery complet.
    
    Permet un contrôle plus fin sur la requête.
    """
    try:
        agent = get_rh_agent()
        response = agent.invoke(request)
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement: {str(e)}"
        )


@router.get("/profiles", response_model=ProfilesResponse)
async def get_profiles():
    """
    Retourne la liste des profils de salariés disponibles.
    """
    return ProfilesResponse(profiles=settings.VALID_PROFILES)


@router.get("/domains", response_model=DomainsResponse)
async def get_domains():
    """
    Retourne la liste des domaines RH disponibles.
    """
    return DomainsResponse(domains=settings.VALID_DOMAINS)


@router.get("/config")
async def get_config():
    """
    Retourne la configuration publique de l'API.
    
    Utile pour les clients qui veulent connaître les options disponibles.
    """
    return {
        "profiles": settings.VALID_PROFILES,
        "domains": settings.VALID_DOMAINS,
        "model": settings.LLM_MODEL,
        "max_results": settings.VECTORSTORE_K
    }


# ============================================
# ENDPOINTS DE TEST
# ============================================

@router.get("/test/simple")
async def test_simple():
    """
    Test simple de l'agent avec une question prédéfinie.
    """
    try:
        agent = get_rh_agent()
        
        response = agent.chat(
            message="Bonjour, comment puis-je vous aider ?",
            user_profile="CDI",
            thread_id="test"
        )
        
        return {
            "status": "success",
            "message": "Agent opérationnel",
            "test_response": response
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Test échoué: {str(e)}"
        )