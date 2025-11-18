"""
Rental Agreement Completion Agent using LangGraph
This agent helps users complete a French rental agreement (bail de location) JSON template
by asking intelligent questions progressively from basic to advanced.
"""

import json
import os
import re
from typing import Dict, Any, List, Tuple, Optional, Literal, Annotated
from datetime import datetime
from pathlib import Path
import operator

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt


# Initialize the LLM
llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0.3)


# ===== State Definition =====
class ConversationState(TypedDict):
    """State for the rental agreement completion conversation."""

    messages: Annotated[List[BaseMessage], operator.add]
    json_data: Dict[str, Any]
    current_section: str
    missing_required_fields: List[Tuple[str, str]]  # (field_path, field_type)
    completed_sections: List[str]
    validation_errors: List[str]
    needs_confirmation: bool
    confirmation_context: Optional[Dict[str, Any]]
    completion_status: Dict[str, float]  # Section completion percentages
    conversation_phase: Literal[
        "initial", "basic", "detailed", "validation", "complete"
    ]


# ===== Pydantic Models for Structured Outputs =====
class FieldExtraction(BaseModel):
    """Model for extracting field values from user responses."""

    extracted_fields: Dict[str, Any] = Field(
        description="Dictionary of field paths and their extracted values"
    )
    needs_clarification: List[str] = Field(
        default_factory=list, description="Fields that need clarification from the user"
    )
    validation_issues: List[str] = Field(
        default_factory=list,
        description="Validation issues found in the extracted data",
    )


class QuestionGeneration(BaseModel):
    """Model for generating the next question."""

    question: str = Field(description="The next question to ask the user")
    context: str = Field(description="Context or explanation for the question")
    expected_format: str = Field(description="Expected format of the answer")
    priority: Literal["high", "medium", "low"] = Field(
        description="Priority of this question"
    )


# ===== Helper Functions =====
def load_template() -> Dict[str, Any]:
    """Load the JSON template."""
    template_path = "bail_template.json"
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # Return the template structure from the user's input
        return json.loads(TEMPLATE_JSON)


def get_all_required_fields(
    data: Dict[str, Any], path: str = ""
) -> List[Tuple[str, str, Any]]:
    """Recursively get all required fields from the JSON structure."""
    required_fields = []

    for key, value in data.items():
        current_path = f"{path}.{key}" if path else key

        if isinstance(value, dict):
            if "requis" in value and value["requis"] is True:
                field_type = value.get("type", "texte")
                current_value = value.get("valeur")
                if current_value == "" or current_value is None:
                    required_fields.append((current_path, field_type, current_value))
            else:
                # Recurse into nested dictionaries
                required_fields.extend(get_all_required_fields(value, current_path))
        elif isinstance(value, list):
            # Handle lists (like locataires)
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    required_fields.extend(
                        get_all_required_fields(item, f"{current_path}[{i}]")
                    )

    return required_fields


def update_nested_dict(data: Dict[str, Any], path: str, value: Any) -> Dict[str, Any]:
    """Update a nested dictionary value using a dot-separated path."""
    keys = path.split(".")
    current = data

    for i, key in enumerate(keys[:-1]):
        # Handle list indices
        if "[" in key and "]" in key:
            base_key = key[: key.index("[")]
            index = int(key[key.index("[") + 1 : key.index("]")])
            if base_key not in current:
                current[base_key] = []
            while len(current[base_key]) <= index:
                current[base_key].append({})
            current = current[base_key][index]
        else:
            if key not in current:
                current[key] = {}
            current = current[key]

    # Set the final value
    final_key = keys[-1]
    if "[" in final_key and "]" in final_key:
        base_key = final_key[: final_key.index("[")]
        index = int(final_key[final_key.index("[") + 1 : final_key.index("]")])
        if base_key not in current:
            current[base_key] = []
        while len(current[base_key]) <= index:
            current[base_key].append({})
        current[base_key][index] = value
    else:
        if isinstance(current.get(final_key), dict) and "valeur" in current[final_key]:
            current[final_key]["valeur"] = value
        else:
            current[final_key] = value

    return data


def calculate_completion_status(data: Dict[str, Any]) -> Dict[str, float]:
    """Calculate completion percentage for each section."""
    status = {}
    sections = [
        "meta_donnees",
        "designation_parties",
        "objet_contrat",
        "duree_contrat",
        "conditions_financieres",
        "travaux",
        "garanties",
        "colocation",
        "honoraires_location",
        "signature",
    ]

    for section in sections:
        if section in data:
            total_fields = count_fields(data[section])
            filled_fields = count_filled_fields(data[section])
            status[section] = (
                (filled_fields / total_fields * 100) if total_fields > 0 else 0
            )

    return status


def count_fields(data: Any) -> int:
    """Count total number of fields in a structure."""
    if isinstance(data, dict):
        count = 0
        for key, value in data.items():
            if "valeur" in value and isinstance(value, dict):
                count += 1
            else:
                count += count_fields(value)
        return count
    elif isinstance(data, list):
        return sum(count_fields(item) for item in data)
    return 0


def count_filled_fields(data: Any) -> int:
    """Count number of filled fields in a structure."""
    if isinstance(data, dict):
        count = 0
        for key, value in data.items():
            if "valeur" in value and isinstance(value, dict):
                val = value.get("valeur")
                if val not in ["", None]:
                    count += 1
            else:
                count += count_filled_fields(value)
        return count
    elif isinstance(data, list):
        return sum(count_filled_fields(item) for item in data)
    return 0


def validate_field(
    field_type: str, value: Any, field_name: str
) -> Tuple[bool, Optional[str]]:
    """Validate a field value based on its type."""
    if value is None or value == "":
        return False, f"Le champ '{field_name}' est requis mais vide"

    if field_type == "email":
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, str(value)):
            return False, f"L'email '{value}' n'est pas valide"

    elif field_type == "nombre":
        try:
            float(value)
            return True, None
        except:
            return False, f"La valeur '{value}' n'est pas un nombre valide"

    elif field_type == "date":
        try:
            datetime.strptime(str(value), "%d/%m/%Y")
            return True, None
        except:
            return False, f"La date '{value}' doit être au format JJ/MM/AAAA"

    elif field_type == "annee":
        try:
            year = int(value)
            if 1900 <= year <= 2100:
                return True, None
            return False, f"L'année {value} semble incorrecte"
        except:
            return False, f"L'année '{value}' n'est pas valide"

    return True, None


# ===== LangGraph Nodes =====


def initialize_conversation(state: ConversationState) -> Dict[str, Any]:
    """Initialize the conversation with the template and greeting."""
    template = load_template()

    greeting = AIMessage(
        content="""🏠 **Bienvenue dans l'assistant de création de bail de location !**

Je vais vous aider à remplir votre contrat de location étape par étape. 

Nous allons procéder de manière progressive :
1. D'abord les informations essentielles (parties, logement, loyer)
2. Puis les détails spécifiques
3. Enfin, nous vérifierons que tout est complet

💡 **Conseil** : Vous pouvez me donner plusieurs informations à la fois pour aller plus vite !

Commençons par les informations de base.

**Qui est le bailleur (propriétaire) ?**
Merci de me donner :
- Nom complet (personne ou société)
- Adresse complète
- Email (optionnel)
- S'agit-il d'une personne physique ou morale ?"""
    )

    return {
        "messages": [greeting],
        "json_data": template,
        "current_section": "designation_parties",
        "missing_required_fields": get_all_required_fields(template),
        "completed_sections": [],
        "validation_errors": [],
        "needs_confirmation": False,
        "completion_status": calculate_completion_status(template),
        "conversation_phase": "initial",
    }


def extract_information(state: ConversationState) -> Dict[str, Any]:
    """Extract information from the user's last message and update the JSON."""
    if len(state["messages"]) < 2:
        return {}

    last_user_message = state["messages"][-1]
    if not isinstance(last_user_message, HumanMessage):
        return {}

    # Create extraction prompt
    extraction_prompt = f"""
    Tu es un assistant qui extrait des informations d'un message pour remplir un formulaire de bail de location.
    
    Message de l'utilisateur : {last_user_message.content}
    
    Section actuelle : {state['current_section']}
    
    Champs requis manquants dans cette section :
    {json.dumps([f for f in state['missing_required_fields'] if f[0].startswith(state['current_section'])], indent=2, ensure_ascii=False)}
    
    Structure JSON actuelle de la section :
    {json.dumps(state['json_data'].get(state['current_section'], {}), indent=2, ensure_ascii=False)}
    
    Extrait les informations pertinentes du message de l'utilisateur.
    Map les informations aux bons champs du formulaire.
    Pour les champs de type 'choix', essaye de matcher avec les options disponibles.
    Pour les dates, convertis au format JJ/MM/AAAA.
    Pour les nombres, extrait la valeur numérique.
    
    Si une valeur semble incorrecte (ex: loyer négatif, date impossible), signale-le dans validation_issues.
    """

    structured_llm = llm.with_structured_output(FieldExtraction)
    extraction_result = structured_llm.invoke(extraction_prompt)

    # Update JSON data with extracted fields
    updated_json = state["json_data"].copy()
    validation_errors = []

    for field_path, value in extraction_result.extracted_fields.items():
        # Find the field type from missing_required_fields
        field_type = "texte"
        for missing_field, ftype, _ in state["missing_required_fields"]:
            if missing_field == field_path:
                field_type = ftype
                break

        # Validate the field
        is_valid, error_msg = validate_field(field_type, value, field_path)

        if not is_valid and error_msg:
            validation_errors.append(error_msg)

        # Update the JSON regardless (user might confirm invalid values)
        updated_json = update_nested_dict(updated_json, field_path, value)

    # Check if we need confirmation for suspicious values
    needs_confirmation = (
        len(extraction_result.validation_issues) > 0 or len(validation_errors) > 0
    )

    confirmation_context = None
    if needs_confirmation:
        confirmation_context = {
            "extracted_fields": extraction_result.extracted_fields,
            "validation_issues": extraction_result.validation_issues
            + validation_errors,
        }

    return {
        "json_data": updated_json,
        "missing_required_fields": get_all_required_fields(updated_json),
        "validation_errors": validation_errors,
        "needs_confirmation": needs_confirmation,
        "confirmation_context": confirmation_context,
        "completion_status": calculate_completion_status(updated_json),
    }


def generate_next_question(state: ConversationState) -> Dict[str, Any]:
    """Generate the next question based on missing fields and conversation phase."""

    # Check if we need confirmation
    if state["needs_confirmation"] and state["confirmation_context"]:
        issues = state["confirmation_context"]["validation_issues"]
        confirmation_msg = AIMessage(
            content=f"""
⚠️ **Attention, j'ai détecté des valeurs qui pourraient être incorrectes :**

{chr(10).join(['• ' + issue for issue in issues])}

**Voulez-vous confirmer ces valeurs ou les corriger ?**
- Tapez "confirmer" pour garder ces valeurs
- Ou donnez-moi les valeurs corrigées
"""
        )
        return {"messages": [confirmation_msg], "needs_confirmation": True}

    # Get missing required fields
    missing = state["missing_required_fields"]

    if not missing:
        # All required fields are filled
        return {
            "messages": [
                AIMessage(
                    content="✅ Toutes les informations requises ont été remplies ! Le bail est prêt."
                )
            ],
            "conversation_phase": "complete",
        }

    # Group missing fields by section
    sections_missing = {}
    for field_path, field_type, _ in missing:
        section = field_path.split(".")[0]
        if section not in sections_missing:
            sections_missing[section] = []
        sections_missing[section].append((field_path, field_type))

    # Determine which section to focus on (prioritize order)
    section_priority = [
        "designation_parties",
        "objet_contrat",
        "duree_contrat",
        "conditions_financieres",
        "signature",
    ]

    current_section = None
    for section in section_priority:
        if section in sections_missing:
            current_section = section
            break

    if not current_section and sections_missing:
        current_section = list(sections_missing.keys())[0]

    # Generate question based on section
    question_prompt = f"""
    Génère une question naturelle et conviviale pour obtenir les informations manquantes.
    
    Section actuelle : {current_section}
    Champs manquants dans cette section : {sections_missing.get(current_section, [])}
    
    Phase de conversation : {state['conversation_phase']}
    
    Règles :
    - Si plusieurs champs sont liés (ex: nom et adresse), demande-les ensemble
    - Sois concis mais clair
    - Donne des exemples de format si nécessaire
    - Utilise des emojis pour rendre la conversation plus agréable
    - Si c'est la première fois dans une section, donne un contexte
    """

    structured_llm = llm.with_structured_output(QuestionGeneration)
    question = structured_llm.invoke(question_prompt)

    # Format the question message
    question_msg = AIMessage(
        content=f"""
{question.question}

{question.context if question.context else ''}

**Format attendu :** {question.expected_format}
"""
    )

    # Update phase if needed
    new_phase = state["conversation_phase"]
    completion = sum(state["completion_status"].values()) / len(
        state["completion_status"]
    )

    if completion < 30:
        new_phase = "basic"
    elif completion < 70:
        new_phase = "detailed"
    else:
        new_phase = "validation"

    return {
        "messages": [question_msg],
        "current_section": current_section,
        "conversation_phase": new_phase,
    }


def handle_confirmation(state: ConversationState) -> Dict[str, Any]:
    """Handle user confirmation of potentially incorrect values."""
    if not state["needs_confirmation"]:
        return {}

    last_message = state["messages"][-1]
    if not isinstance(last_message, HumanMessage):
        return {}

    user_response = last_message.content.lower().strip()

    if "confirmer" in user_response or "oui" in user_response or "ok" in user_response:
        # User confirms the values
        return {
            "needs_confirmation": False,
            "confirmation_context": None,
            "validation_errors": [],
            "messages": [
                AIMessage(
                    content="✅ Valeurs confirmées. Continuons avec les informations suivantes."
                )
            ],
        }
    else:
        # User wants to correct - treat as new information
        return {"needs_confirmation": False, "confirmation_context": None}


def save_completed_json(state: ConversationState) -> Dict[str, Any]:
    """Save the completed JSON to a file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"/home/claude/bail_completed_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(state["json_data"], f, ensure_ascii=False, indent=2)

    return {
        "messages": [
            AIMessage(
                content=f"""
🎉 **Félicitations ! Votre bail de location est complet !**

Le document a été sauvegardé sous : `{filename}`

**Résumé du bail créé :**
- Bailleur : {state['json_data'].get('designation_parties', {}).get('bailleur', {}).get('nom_prenom_ou_denomination', {}).get('valeur', 'Non renseigné')}
- Adresse du logement : {state['json_data'].get('objet_contrat', {}).get('logement', {}).get('adresse_complete', {}).get('valeur', 'Non renseigné')}
- Loyer mensuel : {state['json_data'].get('conditions_financieres', {}).get('loyer', {}).get('montant_hors_charges', {}).get('valeur', 'Non renseigné')}€
- Date de prise d'effet : {state['json_data'].get('duree_contrat', {}).get('date_prise_effet', {}).get('valeur', 'Non renseigné')}

✅ Toutes les informations obligatoires ont été remplies.

Vous pouvez maintenant imprimer ce bail ou le faire vérifier par un professionnel.
"""
            )
        ]
    }


def check_completion(
    state: ConversationState,
) -> Literal["continue", "save", "confirm"]:
    """Check if we should continue asking questions, save, or need confirmation."""
    if state["needs_confirmation"]:
        return "confirm"

    if state["conversation_phase"] == "complete":
        return "save"

    return "continue"


# ===== Build the Graph =====
def create_rental_agent():
    """Create and compile the rental agreement agent."""

    # Create the graph
    workflow = StateGraph(ConversationState)

    # Add nodes
    workflow.add_node("initialize", initialize_conversation)
    workflow.add_node("extract_info", extract_information)
    workflow.add_node("generate_question", generate_next_question)
    workflow.add_node("handle_confirmation", handle_confirmation)
    workflow.add_node("save_json", save_completed_json)

    # Add edges
    workflow.add_edge(START, "initialize")
    workflow.add_edge("initialize", "generate_question")

    # After extracting info, check what to do next
    workflow.add_conditional_edges(
        "extract_info",
        check_completion,
        {
            "continue": "generate_question",
            "confirm": "generate_question",
            "save": "save_json",
        },
    )

    workflow.add_edge("handle_confirmation", "extract_info")
    workflow.add_edge("generate_question", END)
    workflow.add_edge("save_json", END)

    # Compile with checkpointer for persistence
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    return app


# ===== Template JSON =====
TEMPLATE_JSON = """
{
  "meta_donnees": {
    "type_document": {
      "valeur": "Bail de location",
      "requis": true,
      "type": "fixe"
    },
    "date_creation": {
      "valeur": "",
      "requis": true,
      "type": "date"
    }
  },
  "designation_parties": {
    "bailleur": {
      "nom_prenom_ou_denomination": {
        "valeur": "",
        "requis": true,
        "type": "texte"
      },
      "adresse_siege_social": {
        "valeur": "",
        "requis": true,
        "type": "texte"
      },
      "email": {
        "valeur": "",
        "requis": false,
        "type": "email"
      },
      "type_personne": {
        "valeur": "",
        "requis": true,
        "type": "choix"
      },
      "societe_civile_familiale": {
        "valeur": null,
        "requis": false,
        "type": "booleen"
      },
      "mandataire": {
        "existe": {
          "valeur": null,
          "requis": true,
          "type": "booleen"
        },
        "details": {
          "nom_raison_sociale": {
            "valeur": "",
            "requis": false,
            "type": "texte"
          },
          "adresse": {
            "valeur": "",
            "requis": false,
            "type": "texte"
          },
          "numero_carte_pro": {
            "valeur": "",
            "requis": false,
            "type": "texte"
          }
        }
      }
    },
    "locataires": {
      "liste": [
        {
          "nom_prenom": {
            "valeur": "",
            "requis": true,
            "type": "texte"
          },
          "email": {
            "valeur": "",
            "requis": false,
            "type": "email"
          }
        }
      ]
    },
    "garants": {
      "liste": [
        {
          "noms": {
            "valeur": "",
            "requis": false,
            "type": "texte"
          },
          "adresse": {
            "valeur": "",
            "requis": false,
            "type": "texte"
          }
        }
      ]
    }
  },
  "objet_contrat": {
    "logement": {
      "adresse_complete": {
        "valeur": "",
        "requis": true,
        "type": "texte"
      },
      "identifiant_fiscal": {
        "valeur": "",
        "requis": false,
        "type": "texte"
      },
      "type_habitat": {
        "valeur": "",
        "requis": true,
        "type": "choix",
        "options": ["Immeuble collectif", "Individuel"]
      },
      "regime_juridique": {
        "valeur": "",
        "requis": true,
        "type": "choix",
        "options": ["Mono propriété", "Copropriété"]
      },
      "periode_construction": {
        "valeur": "",
        "requis": true,
        "type": "choix"
      },
      "surface_habitable_m2": {
        "valeur": null,
        "requis": true,
        "type": "nombre"
      },
      "nombre_pieces_principales": {
        "valeur": null,
        "requis": true,
        "type": "nombre"
      },
      "autres_parties": {
        "terrasse": {
          "valeur": null,
          "requis": false,
          "type": "booleen"
        },
        "balcon": {
          "valeur": null,
          "requis": false,
          "type": "booleen"
        },
        "cave": {
          "valeur": null,
          "requis": false,
          "type": "booleen"
        },
        "parking": {
          "valeur": null,
          "requis": false,
          "type": "booleen"
        }
      },
      "equipements_meubles": {
        "valeur": "",
        "requis": true,
        "type": "texte_long"
      },
      "chauffage": {
        "mode": {
          "valeur": "",
          "requis": true,
          "type": "choix",
          "options": ["Individuel", "Collectif"]
        },
        "si_collectif_repartition": {
          "valeur": "",
          "requis": false,
          "type": "texte"
        }
      },
      "eau_chaude": {
        "mode": {
          "valeur": "",
          "requis": true,
          "type": "choix",
          "options": ["Individuel", "Collectif"]
        },
        "si_collectif_repartition": {
          "valeur": "",
          "requis": false,
          "type": "texte"
        }
      },
      "performance_energetique": {
        "classe_dpe": {
          "valeur": "",
          "requis": true,
          "type": "choix",
          "options": ["A", "B", "C", "D", "E", "F", "G"]
        }
      }
    },
    "destination_locaux": {
      "usage": {
        "valeur": "",
        "requis": true,
        "type": "choix"
      }
    }
  },
  "duree_contrat": {
    "date_prise_effet": {
      "valeur": "",
      "requis": true,
      "type": "date"
    },
    "duree_bail": {
      "valeur": "",
      "requis": true,
      "type": "texte"
    }
  },
  "conditions_financieres": {
    "loyer": {
      "montant_hors_charges": {
        "valeur": null,
        "requis": true,
        "type": "nombre"
      },
      "zone_tendue_encadrement": {
        "soumis": {
          "valeur": null,
          "requis": true,
          "type": "booleen"
        },
        "loyer_reference": {
          "valeur": null,
          "requis": false,
          "type": "nombre"
        },
        "loyer_reference_majore": {
          "valeur": null,
          "requis": false,
          "type": "nombre"
        },
        "complement_loyer": {
          "valeur": null,
          "requis": false,
          "type": "nombre"
        }
      }
    },
    "revision_loyer": {
      "date_revision": {
        "valeur": "",
        "requis": true,
        "type": "texte"
      },
      "trimestre_reference_irl": {
        "valeur": "",
        "requis": true,
        "type": "texte"
      }
    },
    "charges": {
      "modalite_reglement": {
        "valeur": "",
        "requis": true,
        "type": "choix",
        "options": ["Forfait", "Provisions"]
      },
      "montant": {
        "valeur": null,
        "requis": true,
        "type": "nombre"
      }
    },
    "paiement": {
      "periodicite": {
        "valeur": "Mensuelle",
        "requis": true,
        "type": "fixe"
      },
      "type_paiement": {
        "valeur": "",
        "requis": true,
        "type": "choix",
        "options": ["À échoir", "À terme échu"]
      },
      "jour_paiement": {
        "valeur": null,
        "requis": true,
        "type": "nombre"
      }
    },
    "premier_versement": {
      "loyer": {
        "valeur": null,
        "requis": true,
        "type": "nombre"
      },
      "charges": {
        "valeur": null,
        "requis": true,
        "type": "nombre"
      },
      "montant_total": {
        "valeur": null,
        "requis": true,
        "type": "nombre"
      }
    },
    "depenses_energetiques": {
      "estimation_annuelle": {
        "valeur": "",
        "requis": true,
        "type": "texte"
      },
      "annee_reference": {
        "valeur": "",
        "requis": true,
        "type": "annee"
      }
    }
  },
  "travaux": {
    "effectues_depuis_dernier_bail": {
      "valeur": null,
      "requis": false,
      "type": "booleen"
    },
    "description": {
      "valeur": "",
      "requis": false,
      "type": "texte_long"
    },
    "montant": {
      "valeur": null,
      "requis": false,
      "type": "nombre"
    }
  },
  "garanties": {
    "montant_depot_garantie": {
      "valeur": null,
      "requis": true,
      "type": "nombre"
    }
  },
  "colocation": {
    "est_colocation": {
      "valeur": null,
      "requis": false,
      "type": "booleen"
    },
    "assurance_bailleur": {
      "valeur": null,
      "requis": false,
      "type": "booleen"
    },
    "montant_assurance": {
      "valeur": null,
      "requis": false,
      "type": "nombre"
    }
  },
  "honoraires_location": {
    "agence_impliquee": {
      "valeur": null,
      "requis": false,
      "type": "booleen"
    },
    "part_locataire": {
      "valeur": null,
      "requis": false,
      "type": "nombre"
    },
    "part_bailleur": {
      "valeur": null,
      "requis": false,
      "type": "nombre"
    }
  },
  "signature": {
    "ville": {
      "valeur": "",
      "requis": true,
      "type": "texte"
    },
    "date": {
      "valeur": "",
      "requis": true,
      "type": "date"
    }
  }
}
"""


# ===== Main interaction loop =====
def main():
    """Main function to run the rental agreement agent."""

    print("Initializing Rental Agreement Agent...")

    # Save the template
    with open("bail_template.json", "w", encoding="utf-8") as f:
        f.write(TEMPLATE_JSON)

    # Create the agent
    agent = create_rental_agent()

    # Configuration with thread ID for conversation persistence
    config = {"configurable": {"thread_id": "rental_agreement_session"}}

    print("\n" + "=" * 60)
    print("AGENT DE CRÉATION DE BAIL DE LOCATION")
    print("=" * 60)
    print("\nL'agent va vous guider pour remplir votre bail de location.")
    print("Répondez aux questions ou tapez 'quit' pour arrêter.\n")

    # Initialize conversation
    result = agent.invoke({"messages": []}, config)

    # Print the initial message
    for msg in result["messages"]:
        if isinstance(msg, AIMessage):
            print(f"\n🤖 Assistant:\n{msg.content}\n")

    # Main conversation loop
    while result.get("conversation_phase") != "complete":
        # Get user input
        user_input = input("👤 Vous: ")

        if user_input.lower() in ["quit", "exit", "stop"]:
            print("\n❌ Conversation interrompue. Le bail n'a pas été sauvegardé.")
            break

        # Process user message
        user_message = HumanMessage(content=user_input)

        # Extract information from user input
        result = agent.invoke({"messages": [user_message]}, config, debug=False)

        # Print progress
        if "completion_status" in result:
            overall_completion = sum(result["completion_status"].values()) / len(
                result["completion_status"]
            )
            print(f"\n📊 Progression globale: {overall_completion:.1f}%")

        # Handle confirmation if needed
        if result.get("needs_confirmation"):
            result = agent.invoke({"messages": []}, config)
        else:
            # Generate next question
            result = agent.invoke({"messages": []}, config)

        # Print the assistant's response
        for msg in result["messages"]:
            if isinstance(msg, AIMessage):
                print(f"\n🤖 Assistant:\n{msg.content}\n")

    print("\n" + "=" * 60)
    print("FIN DE LA SESSION")
    print("=" * 60)


if __name__ == "__main__":
    main()
