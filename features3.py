import os
import asyncio
from typing import Dict, List, Optional, TypedDict, Annotated
from dataclasses import dataclass, asdict
import logging
from datetime import datetime

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Monitoring
from langfuse import Langfuse
#from langfuse.langchain import CallbackHandler

# Streamlit (si vous gardez l'interface)
import streamlit as st
from dotenv import load_dotenv

# Vos prompts existants
from prompts import (
    BASE_CONNAISSANCES_BLOOM,
    BASE_CONNAISSANCES_PEDAGOGIQUES,
    PROMPT_CLASSIFICATION_BLOOM,
    PROMPT_EVALUATION_OBJECTIFS,
    PROMPT_AUTO_EVAL_EVALUATION,
    PROMPT_AMELIORER_OBJECTIFS,
    PROMPT_AUTO_EVAL_SUGGESTIONS,
    PROMPT_SYNTHESE,
    PROMPT_RECAPITULATIF
)

load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration Langfuse
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST")
)
"""
langfuse_handler = CallbackHandler(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST")
)"""

# Configuration des modèles
@dataclass
class ModelConfig:
    api_key: str
    model_name: str = "gemini-2.5-flash"
    temperature: float = 0.4
    max_output_tokens: int = 2024

# État du graphe
class AgentState(TypedDict):
    # Données d'entrée
    nom_cours: str
    niveau: str
    public: str
    objectif_general: str
    objectifs_specifiques: List[str]
    
    # Résultats intermédiaires
    bloom_classification: Optional[str]
    evaluation_objectifs: Optional[str]
    evaluation_revisee: Optional[str]
    suggestions: Optional[str]
    suggestions_revisees: Optional[str]
    synthese_finale: Optional[str]
    
    # Métadonnées
    messages: Annotated[List, add_messages]
    errors: List[str]
    current_step: str
    retry_count: int
    max_retries: int
    
    # Résultat final
    rapport_final: Optional[Dict]

class PedagogicalAgent:
    def __init__(self):
        self.models = {
            "classification": self._create_model(os.getenv("GEMINI_API_KEY_CLASSIFICATION")),
            "evaluation": self._create_model(os.getenv("GEMINI_API_KEY_EVALUATION")),
            "suggestion": self._create_model(os.getenv("GEMINI_API_KEY_SUGGESTION")),
            "synthese": self._create_model(os.getenv("GEMINI_API_KEY_RECAP_SYNTHESE"))
        }
        
        # Création du graphe
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile(
            checkpointer=MemorySaver(),
            interrupt_before=[],  # Pas d'interruption par défaut
            debug=True
        )
    
    def _create_model(self, api_key: str) -> ChatGoogleGenerativeAI:
        """Crée un modèle configuré avec gestion d'erreurs"""
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0.4,
            max_output_tokens=2024,
            #callbacks=[langfuse_handler]
        )
    
    def _create_workflow(self) -> StateGraph:
        """Crée le workflow LangGraph"""
        workflow = StateGraph(AgentState)
        
        # Ajout des nœuds (sans auto_eval_suggestions selon le code original)
        workflow.add_node("classify_bloom", self._classify_bloom_node)
        workflow.add_node("evaluate_objectives", self._evaluate_objectives_node)
        workflow.add_node("auto_eval_evaluation", self._auto_eval_evaluation_node)
        workflow.add_node("generate_suggestions", self._generate_suggestions_node)
        workflow.add_node("create_synthesis", self._create_synthesis_node)
        workflow.add_node("handle_error", self._handle_error_node)
        workflow.add_node("finalize_report", self._finalize_report_node)
        
        # Définition des arêtes
        workflow.add_edge(START, "classify_bloom")
        workflow.add_conditional_edges(
            "classify_bloom",
            self._should_continue_or_retry,
            {
                "continue": "evaluate_objectives",
                "retry": "classify_bloom",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "evaluate_objectives",
            self._should_continue_or_retry,
            {
                "continue": "auto_eval_evaluation",
                "retry": "evaluate_objectives",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "auto_eval_evaluation",
            self._should_continue_or_retry,
            {
                "continue": "generate_suggestions",
                "retry": "auto_eval_evaluation",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "generate_suggestions",
            self._should_continue_or_retry,
            {
                "continue": "create_synthesis",  # Passer directement à la synthèse
                "retry": "generate_suggestions",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "create_synthesis",
            self._should_continue_or_retry,
            {
                "continue": "finalize_report",
                "retry": "create_synthesis",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("finalize_report", END)
        workflow.add_edge("handle_error", END)
        
        return workflow
    
    def _should_continue_or_retry(self, state: AgentState) -> str:
        """Décide si on continue, retry ou gère l'erreur"""
        current_step = state["current_step"]
        
        # Vérifier si l'étape actuelle a produit un résultat
        step_results = {
            "classify_bloom": state.get("bloom_classification"),
            "evaluate_objectives": state.get("evaluation_objectifs"),
            "auto_eval_evaluation": state.get("evaluation_revisee"),
            "generate_suggestions": state.get("suggestions"),
            "create_synthesis": state.get("synthese_finale")
        }
        
        current_result = step_results.get(current_step)
        
        if current_result is not None and current_result.strip():
            return "continue"
        elif state["retry_count"] < state["max_retries"]:
            return "retry"
        else:
            return "error"
    
    async def _classify_bloom_node(self, state: AgentState) -> AgentState:
        """Nœud de classification Bloom"""
        state["current_step"] = "classify_bloom"
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "Tu es un expert en taxonomie de Bloom révisée."),
                ("human", PROMPT_CLASSIFICATION_BLOOM)
            ])
            
            chain = prompt | self.models["classification"] | StrOutputParser()
            
            result = await chain.ainvoke({
                "base_connaissances": BASE_CONNAISSANCES_BLOOM,
                "objectif_general": state["objectif_general"],
                "objectifs_specifiques": "\n".join(f"- {obj}" for obj in state["objectifs_specifiques"])
            })
            
            state["bloom_classification"] = result
            state["messages"].append(AIMessage(content=f"Classification Bloom terminée: {len(result)} caractères"))
            logger.info("Classification Bloom réussie")
            
        except Exception as e:
            state["errors"].append(f"Erreur classification Bloom: {str(e)}")
            state["retry_count"] += 1
            logger.error(f"Erreur classification Bloom: {e}")
            
        return state
    
    async def _evaluate_objectives_node(self, state: AgentState) -> AgentState:
        """Nœud d'évaluation des objectifs"""
        state["current_step"] = "evaluate_objectives"
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "Tu es un expert en pédagogie universitaire."),
                ("human", PROMPT_EVALUATION_OBJECTIFS)
            ])
            
            chain = prompt | self.models["evaluation"] | StrOutputParser()
            
            result = await chain.ainvoke({
                "base_connaissances": BASE_CONNAISSANCES_PEDAGOGIQUES,
                "nom_cours": state["nom_cours"],
                "niveau": state["niveau"],
                "public": state["public"],
                "bloom_classification": state["bloom_classification"]
            })
            
            state["evaluation_objectifs"] = result
            state["messages"].append(AIMessage(content="Évaluation des objectifs terminée"))
            logger.info("Évaluation des objectifs réussie")
            
        except Exception as e:
            state["errors"].append(f"Erreur évaluation objectifs: {str(e)}")
            state["retry_count"] += 1
            logger.error(f"Erreur évaluation objectifs: {e}")
            
        return state
    
    async def _auto_eval_evaluation_node(self, state: AgentState) -> AgentState:
        """Nœud d'auto-évaluation de l'évaluation"""
        state["current_step"] = "auto_eval_evaluation"
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "Tu es un expert en pédagogie universitaire."),
                ("human", PROMPT_AUTO_EVAL_EVALUATION)
            ])
            
            chain = prompt | self.models["evaluation"] | StrOutputParser()
            
            result = await chain.ainvoke({
                "base_connaissances": BASE_CONNAISSANCES_PEDAGOGIQUES,
                "evaluation": state["evaluation_objectifs"]
            })
            
            state["evaluation_revisee"] = result
            state["messages"].append(AIMessage(content="Auto-évaluation terminée"))
            logger.info("Auto-évaluation réussie")
            
        except Exception as e:
            state["errors"].append(f"Erreur auto-évaluation: {str(e)}")
            state["retry_count"] += 1
            logger.error(f"Erreur auto-évaluation: {e}")
            
        return state
    
    async def _generate_suggestions_node(self, state: AgentState) -> AgentState:
        """Nœud de génération de suggestions"""
        state["current_step"] = "generate_suggestions"
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "Tu es un expert en pédagogie universitaire."),
                ("human", PROMPT_AMELIORER_OBJECTIFS)
            ])
            
            chain = prompt | self.models["suggestion"] | StrOutputParser()
            
            result = await chain.ainvoke({
                "base_connaissances": BASE_CONNAISSANCES_PEDAGOGIQUES,
                "nom_cours": state["nom_cours"],
                "niveau": state["niveau"],
                "public": state["public"],
                "evaluation_objectifs": state["evaluation_revisee"]
            })
            
            state["suggestions"] = result
            state["messages"].append(AIMessage(content="Suggestions générées"))
            logger.info("Génération de suggestions réussie")
            
        except Exception as e:
            state["errors"].append(f"Erreur génération suggestions: {str(e)}")
            state["retry_count"] += 1
            logger.error(f"Erreur génération suggestions: {e}")
            
        return state
    
    async def _auto_eval_suggestions_node(self, state: AgentState) -> AgentState:
        """Nœud d'auto-évaluation des suggestions"""
        state["current_step"] = "auto_eval_suggestions"
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "Tu es un expert en pédagogie universitaire."),
                ("human", PROMPT_AUTO_EVAL_SUGGESTIONS)
            ])
            
            chain = prompt | self.models["suggestion"] | StrOutputParser()
            
            result = await chain.ainvoke({
                "base_connaissances": BASE_CONNAISSANCES_PEDAGOGIQUES,
                "suggestions": state["suggestions"]
            })
            
            state["suggestions_revisees"] = result
            state["messages"].append(AIMessage(content="Auto-évaluation des suggestions terminée"))
            logger.info("Auto-évaluation des suggestions réussie")
            
        except Exception as e:
            state["errors"].append(f"Erreur auto-évaluation suggestions: {str(e)}")
            state["retry_count"] += 1
            logger.error(f"Erreur auto-évaluation suggestions: {e}")
            
        return state
    
    async def _create_synthesis_node(self, state: AgentState) -> AgentState:
        """Nœud de création de synthèse"""
        state["current_step"] = "create_synthesis"
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "Tu es un expert en pédagogie universitaire."),
                ("human", PROMPT_SYNTHESE)
            ])
            
            chain = prompt | self.models["synthese"] | StrOutputParser()
            
            # Utiliser les suggestions finales comme rapport (comme dans le code original)
            rapport = state["suggestions"]
            
            result = await chain.ainvoke({
                "nom_cours": state["nom_cours"],
                "niveau": state["niveau"],
                "public": state["public"],
                "rapport": rapport
            })
            
            state["synthese_finale"] = result
            state["messages"].append(AIMessage(content="Synthèse finale créée"))
            logger.info("Création de synthèse réussie")
            
        except Exception as e:
            state["errors"].append(f"Erreur création synthèse: {str(e)}")
            state["retry_count"] += 1
            logger.error(f"Erreur création synthèse: {e}")
            
        return state
    
    async def _finalize_report_node(self, state: AgentState) -> AgentState:
        """Nœud de finalisation du rapport - Format identique au code original"""
        try:
            # Format exact du code original
            rapport = f"""
            {state["suggestions"]}
            """
            
            resultat_final = {
                "informations_cours": f"""
                **Cours :** {state["nom_cours"]}
                **Niveau :** {state["niveau"]}
                **Public cible :** {state["public"]} 
                **Objectif général :** 
                    {state["objectif_general"]}
                **Objectifs specifiques :** 
                    {state["objectifs_specifiques"]}
                """,
                "aperçu": state["synthese_finale"],
                "details": rapport
            }
            
            state["rapport_final"] = resultat_final
            state["messages"].append(AIMessage(content="Rapport final créé avec succès"))
            logger.info("Rapport final créé avec succès")
            
        except Exception as e:
            state["errors"].append(f"Erreur finalisation rapport: {str(e)}")
            logger.error(f"Erreur finalisation rapport: {e}")
            
        return state
    
    async def _handle_error_node(self, state: AgentState) -> AgentState:
        """Nœud de gestion des erreurs"""
        error_msg = f"Erreur dans l'étape {state['current_step']}: {'; '.join(state['errors'])}"
        
        state["rapport_final"] = {
            "error": True,
            "message": "❌ Une erreur est survenue lors de l'analyse.",
            "details": error_msg,
            "current_step": state["current_step"],
            "retry_count": state["retry_count"],
            "timestamp": datetime.now().isoformat()
        }
        
        state["messages"].append(AIMessage(content=error_msg))
        logger.error(error_msg)
        
        return state
    
    async def run_analysis(self, **kwargs) -> Dict:
        """Lance l'analyse pédagogique"""
        initial_state = {
            "nom_cours": kwargs.get("nom_cours", ""),
            "niveau": kwargs.get("niveau", ""),
            "public": kwargs.get("public", ""),
            "objectif_general": kwargs.get("objectif_general", ""),
            "objectifs_specifiques": kwargs.get("objectifs_specifiques", []),
            "bloom_classification": None,
            "evaluation_objectifs": None,
            "evaluation_revisee": None,
            "suggestions": None,
            "suggestions_revisees": None,
            "synthese_finale": None,
            "messages": [HumanMessage(content="Début de l'analyse pédagogique")],
            "errors": [],
            "current_step": "",
            "retry_count": 0,
            "max_retries": 3,
            "rapport_final": None
        }
        
        config = {"configurable": {"thread_id": f"analysis_{datetime.now().timestamp()}"}}
        
        try:
            # Exécution asynchrone du workflow
            async for event in self.app.astream(initial_state, config=config):
                if hasattr(st, 'info'):  # Si Streamlit est disponible
                    for node_name, node_state in event.items():
                        if node_name != "__end__":
                            step_name = {
                                "classify_bloom": "Classification selon Bloom",
                                "evaluate_objectives": "Évaluation des objectifs",
                                "auto_eval_evaluation": "Révision de l'évaluation",
                                "generate_suggestions": "Génération de recommandations",
                                "create_synthesis": "Création de la synthèse",
                                "finalize_report": "Finalisation du rapport"
                            }.get(node_name, node_name)
                            
                            st.info(f"🔄 {step_name}...")
            
            # Récupération du résultat final
            final_state = await self.app.aget_state(config)
            return final_state.values.get("rapport_final", {
                "error": True,
                "message": "Aucun résultat produit"
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du workflow: {e}")
            return {
                "error": True,
                "message": f"❌ Erreur lors de l'exécution: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

# Fonction d'interface pour Streamlit
def assistant_pedagogique(nom_cours, niveau, public, objectif_general, objectifs_specifiques):
    """Interface pour Streamlit utilisant LangGraph"""
    agent = PedagogicalAgent()
    
    # Exécution synchrone pour Streamlit
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            agent.run_analysis(
                nom_cours=nom_cours,
                niveau=niveau,
                public=public,
                objectif_general=objectif_general,
                objectifs_specifiques=objectifs_specifiques
            )
        )
        return result
    finally:
        loop.close()

# Fonction pour récapitulatif (identique au code original)
async def recapitulatif(rapport: str, api_key: str) -> str:
    """Fonction récapitulatif identique au code original"""
    prompt = f"""
    Tu es un assistant pédagogique expert. À partir du rapport suivant, génère une synthèse structurée dans un dictionnaire Python avec les éléments suivants :
        
    - **points_forts** : une liste des éléments positifs remarqués dans la formulation des objectifs (clarté, niveau de Bloom, adéquation au contenu du cours, etc.)

    - **axes_amelioration** : une liste synthétique des améliorations générales suggérées (par exemple : "Certains objectifs ne sont pas assez précis, ce qui rend leur compréhension et leur évaluation difficiles.", "Certains verbes utilisés ne reflètent pas le niveau attendu selon la taxonomie de Bloom.", etc.)

    - **objectifs_total** : le nombre total d'objectifs analysés.

    - **objectifs_conformes** :
        - `nbre_total` : nombre d'objectifs conformes,
        - `liste` : une liste de dictionnaires, chacun contenant :
            - `num` : le numéro de l'objectif,
            - `objectif` : le texte de l'objectif,
            - `niveau_bloom` : le niveau de la taxonomie de Bloom identifié.

    - **objectifs_a_ameliorer** :
        - `nbre_total` : nombre d'objectifs à corriger,
        - `liste` : une liste de dictionnaires, chacun contenant :
            - `num` : le numéro de l'objectif,
            - `objectif` : le texte original,
            - `probleme_resume` : résumé du défaut,
            - `suggestion` : résumé de la proposition de reformulation ou d'amélioration.

    - **recommandations** : un résumé, sous forme de liste, des recommandations générales à l'intention de l'enseignant pour améliorer la formulation des objectifs.

    - **niveaux_bloom_utilises** : une liste récapitulative des niveaux de la taxonomie de Bloom identifiés dans l'ensemble des objectifs, qu'ils soient objectif général comme spécifique, conforme comme à améliorer. Ex : ['Connaître', 'Comprendre', etc]
    
    Les objectifs conformes sont ceux qui ont 5/5 pour tous les critères.
    Les objectifs à améliorer sont ceux qui n'ont pas obtenu 5/5 pour tous les critères.
    
    Voici le rapport à analyser :

    {rapport}

    Réponds uniquement avec un objet Python de type `dict` valide. Aucune explication. Pas de texte hors du dictionnaire.
    """
    
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=api_key,
        temperature=0.4,
        max_output_tokens=2024,
        #callbacks=[langfuse_handler]
    )
    
    return await model.ainvoke(prompt)

# Exemple d'utilisation
if __name__ == "__main__":
    # Test avec données d'exemple
    test_data = {
        "nom_cours": "Introduction à la Programmation Python",
        "niveau": "Licence 1",
        "public": "Étudiants débutants en informatique",
        "objectif_general": "Maîtriser les bases de la programmation Python",
        "objectifs_specifiques": [
            "Comprendre la syntaxe de base de Python",
            "Savoir utiliser les structures de contrôle",
            "Être capable de créer des fonctions simples"
        ]
    }
    
    # Exécution asynchrone
    async def main():
        result = await run_pedagogical_analysis(**test_data)
        print("Résultat de l'analyse:")
        print(result)
    
    asyncio.run(main())