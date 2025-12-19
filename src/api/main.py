"""
Application FastAPI pour l'assistant RH.
Point d'entrée de l'API REST.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config.settings import settings
from src.agents.rh_agent import get_rh_agent
from src.core.exceptions import RHAssistantException, handle_exception


# ============================================
# LIFECYCLE MANAGEMENT
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    # Startup
    print("🚀 Démarrage de l'API RH Assistant...")
    
    try:
        # Initialiser l'agent au démarrage
        agent = get_rh_agent()
        print("✅ Agent RH initialisé")
        
    except Exception as e:
        print(f"❌ Erreur d'initialisation: {e}")
        raise
    
    yield
    
    # Shutdown
    print("🛑 Arrêt de l'API...")


# ============================================
# APPLICATION FASTAPI
# ============================================

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan
)

# ============================================
# MIDDLEWARE CORS
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# EXCEPTION HANDLERS
# ============================================

@app.exception_handler(RHAssistantException)
async def rh_exception_handler(request, exc: RHAssistantException):
    """Gère les exceptions personnalisées de l'application"""
    message, details = handle_exception(exc)
    return JSONResponse(
        status_code=400,
        content={
            "error": message,
            "details": details
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Gère les exceptions non prévues"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Une erreur interne s'est produite",
            "details": {"type": type(exc).__name__, "message": str(exc)}
        }
    )


# ============================================
# HEALTH CHECK
# ============================================

@app.get("/", tags=["Health"])
async def root():
    """Point d'entrée de l'API"""
    return {
        "message": "API RH Assistant - Safran",
        "version": settings.API_VERSION,
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Vérification de l'état de l'API"""
    try:
        # Vérifier que l'agent est accessible
        agent = get_rh_agent()
        
        return {
            "status": "healthy",
            "agent": "ready",
            "vectorstore": "operational"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )


# ============================================
# IMPORT DES ROUTES
# ============================================

from src.api.routes import router as api_router

app.include_router(api_router, prefix="/api/v1", tags=["RH Assistant"])


# ============================================
# MAIN (pour exécution directe)
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )