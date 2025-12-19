"""
Outils LangChain pour l'agent RH.
Version optimisée avec vectorstore singleton.
"""

from typing import Optional
from langchain.tools import tool

from src.config.settings import settings
from src.core.models import RHSearchInput
from src.data.vectorstore import get_vectorstore


class RHTools:
    """Outils RH (singleton)"""

    def __init__(self):
        print(" Initialisation RHTools")
        self.vs = get_vectorstore()

    def search_rh_knowledge(
        self,
        query: str,
        user_profile: str,
        domaine: Optional[str] = None
    ) -> str:
        try:
            search_filter = {"profil": user_profile}
            if domaine:
                search_filter["domaine"] = domaine

            docs = self.vs.search(
                query=query,
                k=settings.VECTORSTORE_K,
                filter_dict=search_filter
            )

            if not docs:
                return "ERREUR_NOT_FOUND"

            responses = []
            for i, doc in enumerate(docs, 1):
                responses.append(
                    f"### Résultat {i}\n"
                    f"{doc.page_content}\n\n"
                    f"*Profil:* {doc.metadata.get('profil')} | "
                    f"*Domaine:* {doc.metadata.get('domaine')}"
                )

            return "\n\n---\n\n".join(responses)

        except Exception as e:
            return f"ERREUR_TECHNIQUE: {str(e)}"


# =========================
# SINGLETON OUTILS
# =========================

_RH_TOOLS_INSTANCE: Optional[RHTools] = None


def get_rh_tools() -> RHTools:
    global _RH_TOOLS_INSTANCE
    if _RH_TOOLS_INSTANCE is None:
        _RH_TOOLS_INSTANCE = RHTools()
    return _RH_TOOLS_INSTANCE


# =========================
# OUTIL LANGCHAIN
# =========================

@tool(args_schema=RHSearchInput)
def search_rh_expert(query: str, user_profile: str, domaine: str = None) -> str:
    """
    Recherche RH par profil et domaine.
    """
    tools = get_rh_tools()
    return tools.search_rh_knowledge(query, user_profile, domaine)


def get_tools_list():
    return [search_rh_expert]
