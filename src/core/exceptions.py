"""
Exceptions personnalisées pour l'application RH Assistant.
Permet une gestion d'erreurs claire et structurée.
"""


class RHAssistantException(Exception):
    """Exception de base pour toutes les erreurs de l'application"""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Détails: {self.details}"
        return self.message


# ============================================
# EXCEPTIONS DE CONFIGURATION
# ============================================

class ConfigurationError(RHAssistantException):
    """Erreur de configuration (fichiers manquants, variables d'env, etc.)"""
    pass


class MissingAPIKeyError(ConfigurationError):
    """Clé API manquante ou invalide"""
    
    def __init__(self, key_name: str):
        super().__init__(
            f"Clé API manquante: {key_name}",
            {"key_name": key_name, "help": "Vérifiez votre fichier .env"}
        )


# ============================================
# EXCEPTIONS DE DONNÉES
# ============================================

class DataError(RHAssistantException):
    """Erreur liée aux données (CSV, vectorstore, etc.)"""
    pass


class CSVLoadError(DataError):
    """Erreur lors du chargement du fichier CSV"""
    
    def __init__(self, file_path: str, original_error: Exception):
        super().__init__(
            f"Impossible de charger le fichier CSV: {file_path}",
            {
                "file_path": file_path,
                "error_type": type(original_error).__name__,
                "error_message": str(original_error)
            }
        )


class VectorStoreError(DataError):
    """Erreur liée au vectorstore (FAISS, Chroma, etc.)"""
    pass


class InvalidDataFormatError(DataError):
    """Format de données invalide (colonnes manquantes, types incorrects, etc.)"""
    
    def __init__(self, expected_format: str, received_format: str):
        super().__init__(
            "Format de données invalide",
            {
                "expected": expected_format,
                "received": received_format
            }
        )


# ============================================
# EXCEPTIONS D'AGENT
# ============================================

class AgentError(RHAssistantException):
    """Erreur lors de l'exécution de l'agent"""
    pass


class NoAnswerFoundError(AgentError):
    """Aucune réponse trouvée pour la requête"""
    
    def __init__(self, query: str, profile: str, domaine: str = None):
        message = (
            "Désolé, je ne peux pas répondre à cette question précisément "
            "avec les données actuelles. Veuillez contacter le service RH."
        )
        details = {
            "query": query,
            "profile": profile,
            "domaine": domaine,
            "action": "contact_rh"
        }
        super().__init__(message, details)


class ProfileNotProvidedError(AgentError):
    """Le profil utilisateur n'a pas été fourni"""
    
    def __init__(self):
        super().__init__(
            "Profil utilisateur manquant. Veuillez spécifier votre type de contrat "
            "(CDI, CDD, Intérim, Cadre, Non-Cadre, Stagiaire).",
            {"action": "request_profile"}
        )


class InvalidProfileError(AgentError):
    """Profil utilisateur invalide"""
    
    def __init__(self, provided_profile: str, valid_profiles: list[str]):
        super().__init__(
            f"Profil invalide: {provided_profile}",
            {
                "provided": provided_profile,
                "valid_profiles": valid_profiles
            }
        )


# ============================================
# EXCEPTIONS API
# ============================================

class APIError(RHAssistantException):
    """Erreur générale de l'API"""
    pass


class RateLimitError(APIError):
    """Limite de taux d'API atteinte"""
    
    def __init__(self, retry_after: int = 60):
        super().__init__(
            "Limite de requêtes atteinte. Veuillez réessayer plus tard.",
            {"retry_after_seconds": retry_after}
        )


class ValidationError(APIError):
    """Erreur de validation des données d'entrée"""
    
    def __init__(self, field: str, reason: str):
        super().__init__(
            f"Validation échouée pour le champ '{field}'",
            {"field": field, "reason": reason}
        )


# ============================================
# EXCEPTIONS LLM
# ============================================

class LLMError(RHAssistantException):
    """Erreur lors de l'appel au LLM (Gemini, etc.)"""
    pass


class LLMTimeoutError(LLMError):
    """Le LLM n'a pas répondu dans le délai imparti"""
    
    def __init__(self, timeout_seconds: int):
        super().__init__(
            f"Le modèle n'a pas répondu dans les {timeout_seconds} secondes",
            {"timeout": timeout_seconds}
        )


class LLMQuotaExceededError(LLMError):
    """Quota d'utilisation du LLM dépassé"""
    
    def __init__(self):
        super().__init__(
            "Quota d'utilisation de l'API dépassé",
            {"action": "check_api_limits"}
        )


# ============================================
# HELPER FUNCTIONS
# ============================================

def handle_exception(exc: Exception) -> tuple[str, dict]:
    """
    Convertit une exception en message utilisateur friendly.
    
    Returns:
        tuple: (message_utilisateur, détails_techniques)
    """
    if isinstance(exc, RHAssistantException):
        return exc.message, exc.details
    
    # Exception générique non gérée
    return (
        "Une erreur inattendue s'est produite. Veuillez réessayer.",
        {"error_type": type(exc).__name__, "message": str(exc)}
    )