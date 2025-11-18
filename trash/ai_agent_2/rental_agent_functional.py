"""
Advanced Rental Agreement Agent with Functional API
This version uses LangGraph's Functional API for more fluid conversation flow
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from pydantic import BaseModel, Field

from langgraph.func import entrypoint, task
from langgraph.graph import add_messages


# Initialize LLM
llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0.3)


# ===== Pydantic Models =====
class ExtractedData(BaseModel):
    """Extracted data from user message."""

    bailleur_nom: Optional[str] = Field(None, description="Nom du bailleur")
    bailleur_adresse: Optional[str] = Field(None, description="Adresse du bailleur")
    bailleur_email: Optional[str] = Field(None, description="Email du bailleur")
    bailleur_type: Optional[str] = Field(
        None, description="Type de personne (physique/morale)"
    )

    locataire_nom: Optional[str] = Field(None, description="Nom du locataire")
    locataire_email: Optional[str] = Field(None, description="Email du locataire")

    logement_adresse: Optional[str] = Field(None, description="Adresse du logement")
    logement_surface: Optional[float] = Field(None, description="Surface en m²")
    logement_pieces: Optional[int] = Field(None, description="Nombre de pièces")
    logement_type: Optional[str] = Field(None, description="Type d'habitat")
    logement_dpe: Optional[str] = Field(None, description="Classe énergétique")

    loyer_montant: Optional[float] = Field(None, description="Montant du loyer HC")
    charges_montant: Optional[float] = Field(None, description="Montant des charges")
    depot_garantie: Optional[float] = Field(
        None, description="Montant du dépôt de garantie"
    )

    date_effet: Optional[str] = Field(None, description="Date de prise d'effet")
    duree_bail: Optional[str] = Field(None, description="Durée du bail")

    ville_signature: Optional[str] = Field(None, description="Ville de signature")
    date_signature: Optional[str] = Field(None, description="Date de signature")

    has_parking: Optional[bool] = Field(None, description="Parking inclus")
    has_cave: Optional[bool] = Field(None, description="Cave incluse")
    has_balcon: Optional[bool] = Field(None, description="Balcon inclus")

    needs_clarification: List[str] = Field(
        default_factory=list, description="Points à clarifier"
    )
    suspicious_values: Dict[str, str] = Field(
        default_factory=dict, description="Valeurs suspectes"
    )


class NextQuestion(BaseModel):
    """Next question to ask."""

    question: str = Field(description="Question principale")
    examples: Optional[str] = Field(None, description="Exemples de réponse")
    section: str = Field(description="Section concernée")
    priority: str = Field(description="Priorité (high/medium/low)")


# ===== Helper Functions =====
class RentalAgreementManager:
    """Manager for rental agreement data."""

    def __init__(self):
        self.data = self._load_template()
        self.progress = {}

    def _load_template(self) -> Dict[str, Any]:
        """Load the JSON template."""
        # Template structure
        return {
            "meta_donnees": {
                "type_document": {
                    "valeur": "Bail de location",
                    "requis": True,
                    "type": "fixe",
                },
                "date_creation": {"valeur": "", "requis": True, "type": "date"},
            },
            "designation_parties": {
                "bailleur": {
                    "nom_prenom_ou_denomination": {
                        "valeur": "",
                        "requis": True,
                        "type": "texte",
                    },
                    "adresse_siege_social": {
                        "valeur": "",
                        "requis": True,
                        "type": "texte",
                    },
                    "email": {"valeur": "", "requis": False, "type": "email"},
                    "type_personne": {"valeur": "", "requis": True, "type": "choix"},
                },
                "locataires": {
                    "liste": [
                        {
                            "nom_prenom": {
                                "valeur": "",
                                "requis": True,
                                "type": "texte",
                            },
                            "email": {"valeur": "", "requis": False, "type": "email"},
                        }
                    ]
                },
            },
            "objet_contrat": {
                "logement": {
                    "adresse_complete": {"valeur": "", "requis": True, "type": "texte"},
                    "surface_habitable_m2": {
                        "valeur": None,
                        "requis": True,
                        "type": "nombre",
                    },
                    "nombre_pieces_principales": {
                        "valeur": None,
                        "requis": True,
                        "type": "nombre",
                    },
                    "type_habitat": {"valeur": "", "requis": True, "type": "choix"},
                    "performance_energetique": {
                        "classe_dpe": {"valeur": "", "requis": True, "type": "choix"}
                    },
                }
            },
            "duree_contrat": {
                "date_prise_effet": {"valeur": "", "requis": True, "type": "date"},
                "duree_bail": {"valeur": "", "requis": True, "type": "texte"},
            },
            "conditions_financieres": {
                "loyer": {
                    "montant_hors_charges": {
                        "valeur": None,
                        "requis": True,
                        "type": "nombre",
                    }
                },
                "charges": {
                    "montant": {"valeur": None, "requis": True, "type": "nombre"}
                },
            },
            "garanties": {
                "montant_depot_garantie": {
                    "valeur": None,
                    "requis": True,
                    "type": "nombre",
                }
            },
            "signature": {
                "ville": {"valeur": "", "requis": True, "type": "texte"},
                "date": {"valeur": "", "requis": True, "type": "date"},
            },
        }

    def update_from_extraction(self, extracted: ExtractedData):
        """Update the JSON data from extracted information."""
        updates = []

        # Bailleur information
        if extracted.bailleur_nom:
            self.data["designation_parties"]["bailleur"]["nom_prenom_ou_denomination"][
                "valeur"
            ] = extracted.bailleur_nom
            updates.append("Nom du bailleur")

        if extracted.bailleur_adresse:
            self.data["designation_parties"]["bailleur"]["adresse_siege_social"][
                "valeur"
            ] = extracted.bailleur_adresse
            updates.append("Adresse du bailleur")

        if extracted.bailleur_email:
            self.data["designation_parties"]["bailleur"]["email"][
                "valeur"
            ] = extracted.bailleur_email
            updates.append("Email du bailleur")

        if extracted.bailleur_type:
            self.data["designation_parties"]["bailleur"]["type_personne"][
                "valeur"
            ] = extracted.bailleur_type
            updates.append("Type de personne")

        # Locataire information
        if extracted.locataire_nom:
            self.data["designation_parties"]["locataires"]["liste"][0]["nom_prenom"][
                "valeur"
            ] = extracted.locataire_nom
            updates.append("Nom du locataire")

        if extracted.locataire_email:
            self.data["designation_parties"]["locataires"]["liste"][0]["email"][
                "valeur"
            ] = extracted.locataire_email
            updates.append("Email du locataire")

        # Logement information
        if extracted.logement_adresse:
            self.data["objet_contrat"]["logement"]["adresse_complete"][
                "valeur"
            ] = extracted.logement_adresse
            updates.append("Adresse du logement")

        if extracted.logement_surface:
            self.data["objet_contrat"]["logement"]["surface_habitable_m2"][
                "valeur"
            ] = extracted.logement_surface
            updates.append("Surface habitable")

        if extracted.logement_pieces:
            self.data["objet_contrat"]["logement"]["nombre_pieces_principales"][
                "valeur"
            ] = extracted.logement_pieces
            updates.append("Nombre de pièces")

        if extracted.logement_type:
            self.data["objet_contrat"]["logement"]["type_habitat"][
                "valeur"
            ] = extracted.logement_type
            updates.append("Type d'habitat")

        if extracted.logement_dpe:
            self.data["objet_contrat"]["logement"]["performance_energetique"][
                "classe_dpe"
            ]["valeur"] = extracted.logement_dpe
            updates.append("Classe énergétique")

        # Financial information
        if extracted.loyer_montant:
            self.data["conditions_financieres"]["loyer"]["montant_hors_charges"][
                "valeur"
            ] = extracted.loyer_montant
            updates.append("Montant du loyer")

        if extracted.charges_montant:
            self.data["conditions_financieres"]["charges"]["montant"][
                "valeur"
            ] = extracted.charges_montant
            updates.append("Montant des charges")

        if extracted.depot_garantie:
            self.data["garanties"]["montant_depot_garantie"][
                "valeur"
            ] = extracted.depot_garantie
            updates.append("Dépôt de garantie")

        # Dates
        if extracted.date_effet:
            self.data["duree_contrat"]["date_prise_effet"][
                "valeur"
            ] = extracted.date_effet
            updates.append("Date de prise d'effet")

        if extracted.duree_bail:
            self.data["duree_contrat"]["duree_bail"]["valeur"] = extracted.duree_bail
            updates.append("Durée du bail")

        # Signature
        if extracted.ville_signature:
            self.data["signature"]["ville"]["valeur"] = extracted.ville_signature
            updates.append("Ville de signature")

        if extracted.date_signature:
            self.data["signature"]["date"]["valeur"] = extracted.date_signature
            updates.append("Date de signature")

        return updates

    def get_missing_required(self) -> List[Dict[str, Any]]:
        """Get list of missing required fields."""
        missing = []

        def check_fields(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key

                    if isinstance(value, dict) and "requis" in value:
                        if value["requis"] and (
                            value.get("valeur") == "" or value.get("valeur") is None
                        ):
                            missing.append(
                                {
                                    "path": new_path,
                                    "type": value.get("type", "texte"),
                                    "section": new_path.split(".")[0],
                                }
                            )
                    else:
                        check_fields(value, new_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_fields(item, f"{path}[{i}]")

        check_fields(self.data)
        return missing

    def calculate_progress(self) -> Dict[str, float]:
        """Calculate completion progress by section."""
        sections = [
            "designation_parties",
            "objet_contrat",
            "duree_contrat",
            "conditions_financieres",
            "garanties",
            "signature",
        ]
        progress = {}

        for section in sections:
            if section in self.data:
                total = self._count_required(self.data[section])
                filled = self._count_filled(self.data[section])
                progress[section] = (filled / total * 100) if total > 0 else 0

        return progress

    def _count_required(self, obj) -> int:
        """Count required fields."""
        count = 0
        if isinstance(obj, dict):
            for value in obj.values():
                if isinstance(value, dict) and "requis" in value:
                    if value["requis"]:
                        count += 1
                else:
                    count += self._count_required(value)
        elif isinstance(obj, list):
            for item in obj:
                count += self._count_required(item)
        return count

    def _count_filled(self, obj) -> int:
        """Count filled required fields."""
        count = 0
        if isinstance(obj, dict):
            for value in obj.values():
                if isinstance(value, dict) and "requis" in value:
                    if value["requis"] and value.get("valeur") not in ["", None]:
                        count += 1
                else:
                    count += self._count_filled(value)
        elif isinstance(obj, list):
            for item in obj:
                count += self._count_filled(item)
        return count

    def save_to_file(self) -> str:
        """Save the completed JSON to a file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/home/claude/bail_completed_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

        return filename


# ===== Task Functions =====
@task
def extract_from_message(message: str, context: Dict[str, Any]) -> ExtractedData:
    """Extract information from user message."""

    prompt = f"""
    Extract rental agreement information from this message.
    Current context: {json.dumps(context, ensure_ascii=False)}
    User message: {message}
    
    Extract all relevant information. For dates, convert to DD/MM/YYYY format.
    For amounts, extract numeric values. Flag any suspicious values.
    """

    structured_llm = llm.with_structured_output(ExtractedData)
    return structured_llm.invoke(prompt)


@task
def generate_question(
    missing_fields: List[Dict[str, Any]], progress: Dict[str, float]
) -> NextQuestion:
    """Generate the next question based on missing fields."""

    # Group by section
    by_section = {}
    for field in missing_fields:
        section = field["section"]
        if section not in by_section:
            by_section[section] = []
        by_section[section].append(field)

    # Prioritize sections
    priority_order = [
        "designation_parties",
        "objet_contrat",
        "conditions_financieres",
        "duree_contrat",
        "garanties",
        "signature",
    ]

    current_section = None
    for section in priority_order:
        if section in by_section:
            current_section = section
            break

    if not current_section:
        return NextQuestion(
            question="Toutes les informations requises sont remplies !",
            section="complete",
            priority="low",
        )

    # Generate contextual question
    fields_in_section = by_section[current_section][
        :3
    ]  # Ask about up to 3 fields at once

    prompt = f"""
    Generate a natural, friendly question to get these missing rental agreement fields:
    Section: {current_section}
    Missing fields: {json.dumps(fields_in_section, ensure_ascii=False)}
    Progress in this section: {progress.get(current_section, 0):.1f}%
    
    Make the question conversational and include examples if helpful.
    Group related fields together.
    """

    structured_llm = llm.with_structured_output(NextQuestion)
    return structured_llm.invoke(prompt)


@task
def validate_and_confirm(extracted: ExtractedData) -> Optional[str]:
    """Validate extracted data and generate confirmation if needed."""

    if extracted.suspicious_values:
        confirmations = []
        for field, issue in extracted.suspicious_values.items():
            confirmations.append(f"• {field}: {issue}")

        return f"""
⚠️ **J'ai détecté des valeurs qui pourraient nécessiter une vérification :**

{chr(10).join(confirmations)}

**Confirmez-vous ces valeurs ?** (répondez 'oui' pour confirmer ou donnez les valeurs corrigées)
"""

    return None


@task
def format_progress_message(progress: Dict[str, float], updates: List[str]) -> str:
    """Format a progress update message."""

    overall = sum(progress.values()) / len(progress) if progress else 0

    message = f"""
✅ **Informations enregistrées :**
{chr(10).join(['• ' + u for u in updates])}

📊 **Progression :** {overall:.1f}% complété
"""

    # Add section details if needed
    if overall < 100:
        incomplete = [s for s, p in progress.items() if p < 100]
        if incomplete:
            message += f"\n⏳ Sections à compléter : {', '.join(incomplete)}"

    return message


# ===== Main Agent Function =====
@entrypoint()
def rental_agreement_agent(messages: List[BaseMessage]):
    """Main agent for completing rental agreements."""

    # Initialize manager
    manager = RentalAgreementManager()

    # Initial greeting if no messages
    if not messages:
        greeting = AIMessage(
            content="""
🏠 **Bienvenue dans l'assistant de création de bail de location !**

Je vais vous aider à remplir votre contrat de location étape par étape.

Commençons par les informations essentielles. Pour gagner du temps, vous pouvez me donner plusieurs informations à la fois !

**📝 Informations sur le bailleur (propriétaire) :**
Pouvez-vous me donner :
- Le nom complet
- L'adresse
- L'email (optionnel)
- S'il s'agit d'une personne physique ou d'une société

Exemple : "Jean Dupont, 15 rue de la Paix 75001 Paris, jean.dupont@email.com, personne physique"
"""
        )
        return [greeting]

    # Process last user message
    last_message = messages[-1]

    if isinstance(last_message, HumanMessage):
        # Extract information
        context = {
            "current_data": manager.data,
            "progress": manager.calculate_progress(),
        }

        extracted = extract_from_message(last_message.content, context).result()

        # Check for confirmation of suspicious values
        if (
            "confirmer" in last_message.content.lower()
            or "oui" in last_message.content.lower()
        ):
            extracted.suspicious_values = {}

        # Validate if needed
        confirmation_msg = (
            validate_and_confirm(extracted).result()
            if extracted.suspicious_values
            else None
        )

        if confirmation_msg:
            return add_messages(messages, AIMessage(content=confirmation_msg))

        # Update data
        updates = manager.update_from_extraction(extracted)

        # Show progress
        progress = manager.calculate_progress()
        overall_progress = sum(progress.values()) / len(progress) if progress else 0

        response_parts = []

        if updates:
            progress_msg = format_progress_message(progress, updates).result()
            response_parts.append(progress_msg)

        # Check if complete
        missing = manager.get_missing_required()

        if not missing or overall_progress >= 100:
            # Save the file
            filename = manager.save_to_file()
            completion_msg = f"""
🎉 **Félicitations ! Votre bail est complet !**

📁 Fichier sauvegardé : `{filename}`

**Récapitulatif :**
- Bailleur : {manager.data['designation_parties']['bailleur']['nom_prenom_ou_denomination']['valeur']}
- Locataire : {manager.data['designation_parties']['locataires']['liste'][0]['nom_prenom']['valeur']}
- Logement : {manager.data['objet_contrat']['logement']['adresse_complete']['valeur']}
- Loyer : {manager.data['conditions_financieres']['loyer']['montant_hors_charges']['valeur']}€/mois

Le bail est prêt à être imprimé et signé !
"""
            response_parts.append(completion_msg)
        else:
            # Generate next question
            next_q = generate_question(missing, progress).result()

            if next_q.section != "complete":
                question_msg = f"""
{next_q.question}

{next_q.examples if next_q.examples else ''}

💡 Progression totale : {overall_progress:.1f}%
"""
                response_parts.append(question_msg)

        # Combine response parts
        full_response = "\n\n".join(response_parts)
        return add_messages(messages, AIMessage(content=full_response))

    return messages


# ===== Interactive Demo =====
def interactive_demo():
    """Run an interactive demo."""

    print("\n" + "=" * 70)
    print(" " * 10 + "🏠 ASSISTANT BAIL DE LOCATION (Functional API) 🏠")
    print("=" * 70)
    print(
        """
Cette version utilise l'API Fonctionnelle de LangGraph pour une
conversation plus fluide et naturelle.

Instructions :
- Répondez naturellement aux questions
- Donnez plusieurs informations à la fois pour aller plus vite
- Tapez 'quit' pour quitter
"""
    )
    print("=" * 70 + "\n")

    messages = []

    # Get initial greeting
    result = rental_agreement_agent.invoke(messages)
    messages = result

    # Display greeting
    print(f"🤖 Assistant:\n{messages[-1].content}\n")
    print("-" * 70)

    # Main loop
    while True:
        try:
            # Get user input
            user_input = input("\n👤 Vous: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n👋 Au revoir !")
                break

            # Add user message
            messages.append(HumanMessage(content=user_input))

            # Get agent response
            print("\n⏳ Traitement...")
            result = rental_agreement_agent.invoke(messages)
            messages = result

            # Display response
            print("-" * 70)
            print(f"\n🤖 Assistant:\n{messages[-1].content}")
            print("-" * 70)

            # Check if complete
            if (
                "Félicitations" in messages[-1].content
                and "complet" in messages[-1].content
            ):
                print("\n✅ Bail complété avec succès !")
                break

        except KeyboardInterrupt:
            print("\n\n⚠️ Interruption...")
            break
        except Exception as e:
            print(f"\n❌ Erreur: {str(e)}")

    print("\n" + "=" * 70)
    print("Fin de la session")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    interactive_demo()
