"""
French Lease Agent Builder using LangGraph
"""

import operator
from typing import List, Dict, Any, Literal, Optional
from langchain_core.messages import (
    AnyMessage,
    ToolMessage,
    HumanMessage,
    SystemMessage,
    AIMessage,
)
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

from agent.state import AgentState, ConversationMemory
from agent.tools import (
    get_global_progress,
    get_section_details,
    set_field_value,
    get_missing_required_fields,
    validate_document,
    extract_information_from_text,
    suggest_next_questions,
    get_field_descriptions,
    initialize_managers,
)
from utils.json_manager import JSONManager
from utils.memory_manager import MemoryManager


class InformationExtraction(BaseModel):
    """Schema for extracted information from user messages"""

    extracted_fields: Dict[str, Any] = Field(
        description="Fields extracted from the message with their values"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        description="Confidence level of the extraction"
    )
    needs_confirmation: bool = Field(
        description="Whether the extracted information needs user confirmation"
    )


class NextAction(BaseModel):
    """Schema for deciding next action"""

    action: Literal["ask_questions", "confirm_info", "provide_summary", "complete"] = (
        Field(description="Next action to take")
    )
    priority_fields: List[str] = Field(
        default_factory=list, description="Priority fields to ask about"
    )


def create_lease_agent(llm, json_manager: JSONManager, memory_manager: MemoryManager):
    """
    Creates the French Lease Agent with LangGraph
    """
    # Initialize tools with managers
    initialize_managers(json_manager, memory_manager)

    # Define tools
    tools = [
        get_global_progress,
        get_section_details,
        set_field_value,
        get_missing_required_fields,
        validate_document,
        extract_information_from_text,
        suggest_next_questions,
        get_field_descriptions,
    ]

    tools_by_name = {t.name: t for t in tools}
    llm_with_tools = llm.bind_tools(tools)

    # For structured outputs
    extraction_llm = llm.with_structured_output(InformationExtraction)
    action_llm = llm.with_structured_output(NextAction)

    # --- NODE DEFINITIONS ---

    def extract_info_node(state: AgentState) -> Dict[str, Any]:
        """Extract information from user message"""
        messages = state["messages"]
        if not messages:
            return {}

        last_message = messages[-1]
        if not isinstance(last_message, HumanMessage):
            return {}

        # Use LLM to extract structured information
        extraction_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Tu es un expert en extraction d'informations pour les baux de location français.
            Analyse le message de l'utilisateur et extrais toute information pertinente pour remplir un bail.
            
            Informations à rechercher:
            - Noms et prénoms (bailleur, locataire, garant)
            - Adresses
            - Montants (loyer, charges, dépôt de garantie)
            - Dates (début du bail, signature)
            - Surface et nombre de pièces
            - Type de logement (appartement, maison, studio)
            - Email et téléphone
            - Durée du bail
            
            Sois précis dans l'extraction et indique ton niveau de confiance.""",
                ),
                ("human", "{message}"),
            ]
        )

        extraction_chain = extraction_prompt | extraction_llm

        try:
            result = extraction_chain.invoke({"message": last_message.content})

            # Map extracted fields to JSON paths
            field_mapping = {
                "nom_bailleur": "designation_parties.bailleur.nom_prenom_ou_denomination.valeur",
                "adresse_bailleur": "designation_parties.bailleur.adresse_siege_social.valeur",
                "email_bailleur": "designation_parties.bailleur.email.valeur",
                "nom_locataire": "designation_parties.locataires.liste[0].nom_prenom.valeur",
                "email_locataire": "designation_parties.locataires.liste[0].email.valeur",
                "adresse_logement": "objet_contrat.logement.adresse_complete.valeur",
                "surface": "objet_contrat.logement.surface_habitable_m2.valeur",
                "pieces": "objet_contrat.logement.nombre_pieces_principales.valeur",
                "loyer": "conditions_financieres.loyer.montant_hors_charges.valeur",
                "charges": "conditions_financieres.charges.montant.valeur",
                "depot_garantie": "garanties.montant_depot_garantie.valeur",
                "date_debut": "duree_contrat.date_prise_effet.valeur",
                "duree_bail": "duree_contrat.duree_bail.valeur",
                "ville_signature": "signature.ville.valeur",
                "date_signature": "signature.date.valeur",
            }

            # Store extracted information
            extracted_data = {}
            for key, value in result.extracted_fields.items():
                if key in field_mapping:
                    extracted_data[field_mapping[key]] = value

            return {
                "last_tool_outputs": {
                    "extracted": extracted_data,
                    "confidence": result.confidence,
                    "needs_confirmation": result.needs_confirmation,
                }
            }
        except Exception as e:
            print(f"Extraction error: {e}")
            return {}

    def agent_node(state: AgentState) -> Dict[str, Any]:
        """Main agent logic - decides what to do next"""
        session_id = state["session_id"]

        # Check if we have extracted information to save
        if state.get("last_tool_outputs", {}).get("extracted"):
            extracted = state["last_tool_outputs"]["extracted"]

            # Save extracted fields
            messages_to_add = []
            for field_path, value in extracted.items():
                result = set_field_value.invoke(
                    {"session_id": session_id, "field_path": field_path, "value": value}
                )
                if result.get("status") == "success":
                    messages_to_add.append(
                        AIMessage(
                            content=f"✓ Enregistré: {field_path.split('.')[-1]} = {value}"
                        )
                    )

        # Get current status
        missing_fields = get_missing_required_fields.invoke({"session_id": session_id})
        progress = get_global_progress.invoke({"session_id": session_id})

        # Decide next action
        if missing_fields["total_missing"] == 0:
            # Document is complete
            response = AIMessage(
                content="🎉 Excellent! Toutes les informations requises ont été collectées. "
                "Le bail est maintenant complet et prêt à être généré.\n\n"
                f"Récapitulatif:\n{progress['overall_completion']} complété\n"
                "Voulez-vous revoir certaines informations avant la génération finale?"
            )
            return {"messages": [response], "next_action": "complete"}

        # Generate contextual response
        response_parts = []

        # Acknowledge what was collected
        if state.get("last_tool_outputs", {}).get("extracted"):
            response_parts.append("Merci pour ces informations, j'ai bien enregistré:")
            for field_path, value in state["last_tool_outputs"]["extracted"].items():
                field_name = field_path.split(".")[-1].replace("_", " ").title()
                response_parts.append(f"• {field_name}: {value}")
            response_parts.append("")

        # Show progress
        response_parts.append(f"📊 Progression: {progress['overall_completion']}")
        response_parts.append(
            f"Il reste {missing_fields['total_missing']} champs requis à remplir.\n"
        )

        # Ask for next information
        questions = suggest_next_questions.invoke({"session_id": session_id})
        if questions:
            response_parts.append(
                "Pour continuer, j'ai besoin des informations suivantes:"
            )
            for q in questions[:3]:  # Ask max 3 questions at a time
                response_parts.append(f"• {q}")

        response = AIMessage(content="\n".join(response_parts))

        # Call LLM with tools if needed for more complex reasoning
        llm_response = llm_with_tools.invoke(state["messages"] + [response])

        return {"messages": [llm_response], "next_action": "ask_questions"}

    def tool_node(state: AgentState) -> Dict[str, Any]:
        """Execute tools called by the agent"""
        tool_calls = state["messages"][-1].tool_calls
        tool_messages = []

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            if tool_name in tools_by_name:
                tool = tools_by_name[tool_name]

                # Add session_id to args if not present
                args = tool_call["args"]
                if "session_id" not in args and "session_id" in state:
                    args["session_id"] = state["session_id"]

                try:
                    result = tool.invoke(args)
                    tool_messages.append(
                        ToolMessage(content=str(result), tool_call_id=tool_call["id"])
                    )
                except Exception as e:
                    tool_messages.append(
                        ToolMessage(
                            content=f"Error: {str(e)}", tool_call_id=tool_call["id"]
                        )
                    )

        return {"messages": tool_messages}

    def update_memory_node(state: AgentState) -> Dict[str, Any]:
        """Update conversation memory"""
        if not state.get("session_id"):
            return {}

        session_id = state["session_id"]
        messages = state["messages"]

        if len(messages) >= 2:
            # Get last user and assistant messages
            user_msg = None
            assistant_msg = None

            for msg in reversed(messages):
                if isinstance(msg, HumanMessage) and not user_msg:
                    user_msg = msg.content
                elif isinstance(msg, AIMessage) and not assistant_msg:
                    assistant_msg = msg.content

                if user_msg and assistant_msg:
                    break

            if user_msg and assistant_msg:
                # Update memory
                extracted_info = state.get("last_tool_outputs", {}).get("extracted", {})
                memory_manager.add_conversation_turn(
                    session_id, user_msg, assistant_msg, extracted_info
                )

        return {}

    # --- ROUTING LOGIC ---

    def should_continue(state: AgentState) -> Literal["tools", "memory", END]:
        """Determine next step in the workflow"""
        last_message = state["messages"][-1] if state["messages"] else None

        if (
            last_message
            and hasattr(last_message, "tool_calls")
            and last_message.tool_calls
        ):
            return "tools"
        elif state.get("next_action") == "complete":
            return "memory"
        else:
            return "memory"

    def route_after_memory(state: AgentState) -> Literal[END, "agent"]:
        """Route after memory update"""
        if state.get("next_action") == "complete":
            return END
        return END  # For now, end after each turn

    # --- BUILD GRAPH ---

    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("extract", extract_info_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("memory", update_memory_node)

    # Add edges
    workflow.add_edge(START, "extract")
    workflow.add_edge("extract", "agent")
    workflow.add_conditional_edges(
        "agent", should_continue, {"tools": "tools", "memory": "memory", END: END}
    )
    workflow.add_edge("tools", "agent")
    workflow.add_conditional_edges(
        "memory", route_after_memory, {END: END, "agent": "agent"}
    )

    # Add memory checkpointer for conversation persistence
    checkpointer = MemorySaver()
    agent = workflow.compile(checkpointer=checkpointer)

    return agent


def get_system_message() -> str:
    """Get the system message for the agent"""
    return """Tu es un assistant expert en création de baux de location français.
    
    Ton rôle est d'aider l'utilisateur à remplir complètement un bail de location en collectant
    toutes les informations nécessaires de manière conversationnelle et naturelle.
    
    Principes directeurs:
    1. Sois amical et professionnel
    2. Pose des questions claires et spécifiques
    3. Confirme les informations importantes
    4. Guide l'utilisateur à travers toutes les sections du bail
    5. Explique les termes légaux si nécessaire
    6. Assure-toi que toutes les informations obligatoires sont collectées
    
    Process:
    1. Commence par te présenter et demander le contexte général (bailleur ou locataire)
    2. Collecte les informations section par section
    3. Utilise les outils pour sauvegarder les informations au fur et à mesure
    4. Vérifie régulièrement la progression avec get_global_progress
    5. Demande confirmation pour les informations critiques (montants, dates, noms)
    6. Une fois complet, propose une révision finale
    
    Utilise les outils disponibles pour:
    - Vérifier la progression (get_global_progress)
    - Voir les détails d'une section (get_section_details)
    - Sauvegarder les informations (set_field_value)
    - Identifier les champs manquants (get_missing_required_fields)
    - Valider le document (validate_document)
    
    Rappel: Tu dois TOUJOURS passer le session_id dans les appels d'outils."""
