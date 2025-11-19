"""
Example usage of the French Lease Assistant
"""

import os
import json
from pathlib import Path
from typing import List
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Import the assistant
from main import FrenchLeaseAssistant


def example_basic_usage():
    """Basic usage example"""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)

    # Initialize the assistant
    assistant = FrenchLeaseAssistant(
        model_name="claude-sonnet-4-5",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    # Create a new session
    session_id = assistant.new_session()
    print(f"Session created: {session_id}")

    # Have a conversation
    messages = [
        "Bonjour, je suis propriétaire et je souhaite louer mon appartement",
        "Je m'appelle Jean Dupont et j'habite au 123 rue de la Paix, 75001 Paris",
        "Mon email est jean.dupont@example.com",
        "L'appartement est situé au 456 avenue Victor Hugo, 75016 Paris",
        "C'est un 3 pièces de 65m² dans un immeuble collectif",
        "Le loyer sera de 1500€ hors charges, avec 100€ de charges",
        "Le bail commencera le 1er janvier 2024 pour une durée de 3 ans",
        "Le locataire s'appelle Marie Martin, email: marie.martin@example.com",
        "Le dépôt de garantie sera d'un mois de loyer soit 1500€",
        "Le bail sera signé à Paris le 15 décembre 2023",
    ]

    for message in messages:
        print(f"\nUser: {message}")
        response = assistant.chat(session_id, message)
        print(f"Assistant: {response[:400]}...")  # Truncate for display

    # Check status
    status = assistant.get_session_status(session_id)
    print(f"\n📊 Final Status:")
    print(f"  Completion: {status['overall_completion']}")
    print(f"  Is Complete: {status['is_complete']}")

    return session_id


def example_resume_session():
    """Example of resuming an existing session"""
    print("\n" + "=" * 60)
    print("Example 2: Resume Session")
    print("=" * 60)

    # Initialize the assistant
    assistant = FrenchLeaseAssistant(
        model_name="claude-sonnet-4-5",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    # List existing sessions
    sessions = assistant.list_sessions()
    if sessions:
        # Resume the first session
        session_id = sessions[0]["session_id"]
        print(f"Resuming session: {session_id}")

        # Check current status
        status = assistant.get_session_status(session_id)
        print(f"Current completion: {status['overall_completion']}")

        # Continue the conversation
        response = assistant.chat(
            session_id, "Quels sont les champs qu'il me reste à remplir?"
        )
        print(f"Assistant: {response}")
    else:
        print("No existing sessions found")


def example_batch_input():
    """Example of providing all information at once"""
    print("\n" + "=" * 60)
    print("Example 3: Batch Input")
    print("=" * 60)

    # Initialize the assistant
    assistant = FrenchLeaseAssistant(
        model_name="claude-sonnet-4-5",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    session_id = assistant.new_session()

    # Provide all information in one message
    complete_info = """
    Je souhaite créer un bail de location avec les informations suivantes:
    
    BAILLEUR:
    - Nom: Société Immobilière ABC
    - Adresse: 789 Boulevard Haussmann, 75008 Paris
    - Email: contact@abc-immo.fr
    - Type: Personne morale
    
    LOCATAIRE:
    - Nom: Pierre Durand
    - Email: p.durand@email.com
    
    LOGEMENT:
    - Adresse: 321 Rue de Rivoli, 75001 Paris
    - Type: Appartement dans immeuble collectif
    - Surface: 45 m²
    - Nombre de pièces: 2
    - Chauffage: Individuel électrique
    - Eau chaude: Individuelle
    - DPE: Classe D
    - Équipements: Non meublé
    - Usage: Habitation principale
    
    CONDITIONS FINANCIÈRES:
    - Loyer: 1200€ hors charges
    - Charges: 80€ (provisions)
    - Dépôt de garantie: 1200€
    - Paiement: Mensuel à échoir, le 5 de chaque mois
    - Zone tendue: Oui (Paris)
    
    DURÉE:
    - Début: 01/03/2024
    - Durée: 3 ans
    
    SIGNATURE:
    - Ville: Paris
    - Date: 20/02/2024
    """

    print("Sending complete information...")
    response = assistant.chat(session_id, complete_info)
    print(f"Assistant: {response[:300]}...")

    # Check if document is complete
    status = assistant.get_session_status(session_id)
    print(f"\n📊 Status after batch input:")
    print(f"  Completion: {status['overall_completion']}")
    print(f"  Missing fields: {status['missing_required_count']}")

    # If not complete, ask what's missing
    if not status["is_complete"]:
        response = assistant.chat(session_id, "Que manque-t-il?")
        print(f"\nAssistant: {response}")

    return session_id


def example_export_document():
    """Example of exporting a completed document"""
    print("\n" + "=" * 60)
    print("Example 4: Export Document")
    print("=" * 60)

    # First create and complete a session (simplified)
    assistant = FrenchLeaseAssistant(
        model_name="claude-sonnet-4-5",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    session_id = example_basic_usage()  # Reuse the basic example

    # Try to export
    result = assistant.export_lease(session_id, format="json")

    if result["status"] == "success":
        # Save to file
        output_file = f"example_lease_{session_id[:8]}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result["data"], f, ensure_ascii=False, indent=2)
        print(f"✅ Document exported to {output_file}")

        # Show a sample of the exported data
        print("\nSample of exported data:")
        sample = {
            "bailleur": result["data"]["designation_parties"]["bailleur"],
            "loyer": result["data"]["conditions_financieres"]["loyer"],
        }
        print(json.dumps(sample, indent=2, ensure_ascii=False)[:500])
    else:
        print(f"❌ Export failed: {result['message']}")
        if "missing_fields" in result:
            print(f"Missing fields: {result['missing_fields']}")


def example_advanced_features():
    """Example of using advanced features"""
    print("\n" + "=" * 60)
    print("Example 5: Advanced Features")
    print("=" * 60)

    assistant = FrenchLeaseAssistant(
        model_name="claude-sonnet-4-5",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    session_id = assistant.new_session()

    # Example 1: Handling corrections
    print("\n1. Handling Corrections:")
    assistant.chat(session_id, "Le loyer est de 2000€")
    response = assistant.chat(session_id, "En fait non, le loyer est de 1800€")
    print(f"Correction handled: {response[:100]}...")

    # Example 2: Asking for clarification
    print("\n2. Complex input requiring clarification:")
    response = assistant.chat(
        session_id, "L'appartement a 3 ou 4 pièces, je ne suis pas sûr"
    )
    print(f"Assistant asks for clarification: {response[:150]}...")

    # Example 3: Validating information
    print("\n3. Validation:")
    response = assistant.chat(
        session_id, "Peux-tu me faire un récapitulatif de ce qui a été saisi?"
    )
    print(f"Summary: {response[:200]}...")

    # Example 4: Getting help on specific fields
    print("\n4. Getting help:")
    response = assistant.chat(
        session_id, "Qu'est-ce que le trimestre de référence IRL?"
    )
    print(f"Explanation: {response[:200]}...")


def run_all_examples():
    """Run all examples"""
    print("🚀 Running French Lease Assistant Examples")
    print("=" * 60)

    # Ensure data directories exist
    Path("data").mkdir(exist_ok=True)
    Path("data/sessions").mkdir(exist_ok=True)
    Path("data/memory").mkdir(exist_ok=True)

    try:
        # Run examples
        example_basic_usage()
        example_resume_session()
        example_batch_input()
        # example_export_document()  # Commented as it depends on completion
        example_advanced_features()

        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("Make sure you have set up your API keys in .env file")


if __name__ == "__main__":
    run_all_examples()
