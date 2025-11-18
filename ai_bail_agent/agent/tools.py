"""
Tools for the French Lease Agent
"""

from typing import Dict, Any, List, Optional, Tuple
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from utils.json_manager import JSONManager
from utils.memory_manager import MemoryManager


# Initialize managers (will be properly initialized in agent)
json_manager = None
memory_manager = None


def initialize_managers(json_mgr: JSONManager, mem_mgr: MemoryManager):
    """Initialize the managers for tools"""
    global json_manager, memory_manager
    json_manager = json_mgr
    memory_manager = mem_mgr


# Tool argument schemas
class GlobalProgressArgs(BaseModel):
    """Arguments for getting global progress"""

    session_id: str = Field(description="The session ID for the conversation")


class SectionDetailsArgs(BaseModel):
    """Arguments for getting section details"""

    session_id: str = Field(description="The session ID for the conversation")
    section_name: str = Field(description="The name of the section to inspect")


class SetFieldArgs(BaseModel):
    """Arguments for setting a field value"""

    session_id: str = Field(description="The session ID for the conversation")
    field_path: str = Field(
        description="The dot-notation path to the field (e.g., 'bailleur.nom_prenom_ou_denomination')"
    )
    value: Any = Field(description="The value to set for the field")


class GetMissingRequiredArgs(BaseModel):
    """Arguments for getting missing required fields"""

    session_id: str = Field(description="The session ID for the conversation")
    section_filter: Optional[str] = Field(
        default=None, description="Optional section to filter by"
    )


class ValidateDocumentArgs(BaseModel):
    """Arguments for validating the document"""

    session_id: str = Field(description="The session ID for the conversation")


# Tool implementations
@tool(args_schema=GlobalProgressArgs)
def get_global_progress(session_id: str) -> Dict[str, Any]:
    """
    Get the global completion progress of the lease document.
    Returns percentages for each major section and overall completion.
    """
    if not json_manager:
        return {"error": "JSON manager not initialized"}

    try:
        status = json_manager.get_completion_status(session_id)

        # Format the response
        response = {
            "overall_completion": f"{status['overall_percentage']:.1f}%",
            "total_fields": status["total_fields"],
            "filled_fields": status["filled_fields"],
            "sections": {},
        }

        # Add section details
        for section, data in status["sections"].items():
            response["sections"][section] = {
                "completion": f"{data['percentage']:.1f}%",
                "filled": f"{data['filled']}/{data['total']}",
                "has_missing_required": len(data["required_missing"]) > 0,
            }

        return response
    except Exception as e:
        return {"error": str(e)}


@tool(args_schema=SectionDetailsArgs)
def get_section_details(session_id: str, section_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific section.
    Shows all fields in the section, their values, and what's missing.
    """
    if not json_manager:
        return {"error": "JSON manager not initialized"}

    try:
        data = json_manager.load_session_json(session_id)

        # Check if section exists
        if section_name not in data:
            available = [k for k in data.keys() if not k.startswith("_")]
            return {
                "error": f"Section '{section_name}' not found",
                "available_sections": available,
            }

        section_data = data[section_name]
        all_fields = json_manager.get_all_fields_flat({section_name: section_data})

        # Categorize fields
        filled_fields = []
        missing_required = []
        missing_optional = []

        for field_path, field_info in all_fields.items():
            field_name = field_path.replace(f"{section_name}.", "")

            if field_info["value"] not in [None, "", []]:
                filled_fields.append(
                    {
                        "field": field_name,
                        "value": field_info["value"],
                        "type": field_info["type"],
                    }
                )
            elif field_info["required"]:
                missing_required.append(
                    {"field": field_name, "type": field_info["type"]}
                )
            else:
                missing_optional.append(
                    {"field": field_name, "type": field_info["type"]}
                )

        return {
            "section": section_name,
            "filled_fields": filled_fields,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "completion": f"{len(filled_fields)}/{len(all_fields)} fields filled",
        }
    except Exception as e:
        return {"error": str(e)}


@tool(args_schema=SetFieldArgs)
def set_field_value(session_id: str, field_path: str, value: Any) -> Dict[str, Any]:
    """
    Set the value for a specific field in the lease document.
    Use dot notation for nested fields (e.g., 'bailleur.email').
    """
    if not json_manager:
        return {"error": "JSON manager not initialized"}

    try:
        # Clean up the field path
        field_path = field_path.strip()

        # Set the value
        success = json_manager.set_field_value(session_id, field_path, value)

        if success:
            # Update memory with collected information
            if memory_manager:
                memory = memory_manager.load_session(session_id)
                memory["collected_information"][field_path] = value
                memory_manager.save_session(session_id, memory)

            return {
                "status": "success",
                "field": field_path,
                "value": value,
                "message": f"Successfully set {field_path} to {value}",
            }
        else:
            return {
                "status": "error",
                "field": field_path,
                "message": f"Failed to set {field_path}",
            }
    except Exception as e:
        return {"error": str(e)}


@tool(args_schema=GetMissingRequiredArgs)
def get_missing_required_fields(
    session_id: str, section_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get all missing required fields in the document.
    Optionally filter by a specific section.
    """
    if not json_manager:
        return {"error": "JSON manager not initialized"}

    try:
        missing_fields = json_manager.get_missing_required_fields(session_id)

        if section_filter:
            missing_fields = [
                (path, type_)
                for path, type_ in missing_fields
                if path.startswith(section_filter)
            ]

        # Group by section for better organization
        by_section = {}
        for field_path, field_type in missing_fields:
            section = field_path.split(".")[0]
            if section not in by_section:
                by_section[section] = []
            by_section[section].append({"field": field_path, "type": field_type})

        # Get top priority fields (first 5)
        priority_fields = missing_fields[:5] if missing_fields else []

        return {
            "total_missing": len(missing_fields),
            "by_section": by_section,
            "priority_fields": [{"field": f[0], "type": f[1]} for f in priority_fields],
            "next_to_fill": priority_fields[0] if priority_fields else None,
        }
    except Exception as e:
        return {"error": str(e)}


@tool(args_schema=ValidateDocumentArgs)
def validate_document(session_id: str) -> Dict[str, Any]:
    """
    Validate if the lease document is complete and ready to be generated.
    Returns validation status and any missing required information.
    """
    if not json_manager:
        return {"error": "JSON manager not initialized"}

    try:
        validation = json_manager.validate_document(session_id)

        response = {
            "is_complete": validation["is_complete"],
            "can_generate": validation["can_generate_document"],
            "overall_completion": f"{validation['overall_completion']:.1f}%",
            "missing_required_count": validation["missing_required_count"],
        }

        if not validation["is_complete"]:
            # Add summary of what's missing
            missing_by_section = {}
            for field_path, field_type in validation["missing_required_fields"]:
                section = field_path.split(".")[0]
                if section not in missing_by_section:
                    missing_by_section[section] = 0
                missing_by_section[section] += 1

            response["missing_summary"] = missing_by_section
            response["next_steps"] = (
                "Please provide the missing required information to complete the document."
            )
        else:
            response["next_steps"] = "Document is complete and ready to be generated!"

        return response
    except Exception as e:
        return {"error": str(e)}


# Additional utility tools
@tool
def extract_information_from_text(session_id: str, text: str) -> Dict[str, Any]:
    """
    Extract lease-relevant information from user text.
    This tool analyzes text and identifies potential field values.
    """
    extracted = {}
    text_lower = text.lower()

    # Extract common patterns
    import re

    # Email patterns
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    emails = re.findall(email_pattern, text)
    if emails:
        extracted["emails"] = emails

    # Amount patterns (for rent, deposit, etc.)
    amount_pattern = r"(\d+(?:\s?\d{3})*(?:,\d+)?)\s*(?:€|euros?|EUR)"
    amounts = re.findall(amount_pattern, text, re.IGNORECASE)
    if amounts:
        extracted["amounts"] = [a.replace(" ", "").replace(",", ".") for a in amounts]

    # Date patterns
    date_pattern = r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b"
    dates = re.findall(date_pattern, text)
    if dates:
        extracted["dates"] = [f"{d[0]}/{d[1]}/{d[2]}" for d in dates]

    # Surface area
    surface_pattern = r"(\d+(?:,\d+)?)\s*(?:m²|m2|mètres? carrés?)"
    surfaces = re.findall(surface_pattern, text, re.IGNORECASE)
    if surfaces:
        extracted["surface"] = surfaces[0].replace(",", ".")

    # Number of rooms
    rooms_pattern = r"(\d+)\s*(?:pièces?|rooms?|chambres?)"
    rooms = re.findall(rooms_pattern, text, re.IGNORECASE)
    if rooms:
        extracted["rooms"] = rooms[0]

    # Location/address keywords
    if any(
        word in text_lower
        for word in ["paris", "lyon", "marseille", "toulouse", "nice"]
    ):
        # Extract potential address
        lines = text.split("\n")
        for line in lines:
            if any(
                word in line.lower() for word in ["rue", "avenue", "boulevard", "place"]
            ):
                extracted["potential_address"] = line.strip()

    # Contract duration
    if "3 ans" in text_lower or "trois ans" in text_lower:
        extracted["duration"] = "3 ans"
    elif "1 an" in text_lower or "un an" in text_lower:
        extracted["duration"] = "1 an"

    # Property type
    if "appartement" in text_lower:
        extracted["property_type"] = "appartement"
    elif "maison" in text_lower:
        extracted["property_type"] = "maison"
    elif "studio" in text_lower:
        extracted["property_type"] = "studio"

    # Furnished or not
    if "meublé" in text_lower:
        extracted["furnished"] = True
    elif "non meublé" in text_lower or "vide" in text_lower:
        extracted["furnished"] = False

    return {
        "extracted_information": extracted,
        "confidence": "medium",
        "suggestion": "Please confirm if the extracted information is correct",
    }


@tool
def suggest_next_questions(session_id: str) -> List[str]:
    """
    Suggest the next questions to ask based on missing required fields.
    """
    if not json_manager:
        return ["Unable to suggest questions - manager not initialized"]

    try:
        missing = json_manager.get_missing_required_fields(session_id)

        if missing["total_missing"] == 0:
            return [
                "Le document est complet! Voulez-vous réviser les informations saisies?"
            ]

        questions = []
        priority_fields = missing["priority_fields"][:3]  # Get top 3

        # Generate natural questions based on field types
        field_questions = {
            "nom_prenom_ou_denomination": "Quel est le nom complet du bailleur?",
            "adresse_siege_social": "Quelle est l'adresse du bailleur?",
            "nom_prenom": "Quel est le nom du locataire?",
            "adresse_complete": "Quelle est l'adresse complète du logement?",
            "surface_habitable_m2": "Quelle est la surface habitable en m²?",
            "nombre_pieces_principales": "Combien de pièces principales compte le logement?",
            "montant_hors_charges": "Quel est le montant du loyer hors charges?",
            "date_prise_effet": "Quelle est la date de début du bail?",
            "montant_depot_garantie": "Quel est le montant du dépôt de garantie?",
            "ville": "Dans quelle ville sera signé le bail?",
            "date": "Quelle est la date de signature prévue?",
        }

        for field_info in priority_fields:
            field_name = field_info["field"].split(".")[-1]
            if field_name in field_questions:
                questions.append(field_questions[field_name])
            else:
                # Generic question
                section = field_info["field"].split(".")[0]
                questions.append(
                    f"Pouvez-vous fournir: {field_name} (section {section})?"
                )

        return questions
    except Exception as e:
        return [f"Erreur: {str(e)}"]


@tool
def get_field_descriptions() -> Dict[str, str]:
    """
    Get human-friendly descriptions of all field types for better user communication.
    """
    return {
        "meta_donnees": "Métadonnées du document",
        "designation_parties": "Informations sur les parties (bailleur, locataire, garant)",
        "bailleur": "Propriétaire du logement",
        "locataires": "Personne(s) qui loue(nt) le logement",
        "garants": "Personne(s) se portant caution",
        "objet_contrat": "Description du logement",
        "logement": "Détails du bien immobilier",
        "duree_contrat": "Durée et dates du bail",
        "conditions_financieres": "Loyer, charges et modalités de paiement",
        "loyer": "Montant mensuel à payer",
        "charges": "Charges locatives",
        "travaux": "Travaux effectués dans le logement",
        "garanties": "Dépôt de garantie",
        "colocation": "Informations sur la colocation",
        "honoraires_location": "Frais d'agence",
        "signature": "Lieu et date de signature",
    }
