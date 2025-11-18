#!/usr/bin/env python3
"""
Interactive Demo for the Rental Agreement Completion Agent
This script provides a simple command-line interface to interact with the agent.
"""

import sys
import os

# Add necessary environment variables if needed
if not os.environ.get("ANTHROPIC_API_KEY"):
    print("⚠️ Please set your ANTHROPIC_API_KEY environment variable")
    print("export ANTHROPIC_API_KEY='your-api-key-here'")
    sys.exit(1)

from rental_agreement_agent import create_rental_agent, ConversationState, TEMPLATE_JSON
from langchain_core.messages import HumanMessage, AIMessage
import json


def run_interactive_demo():
    """Run the interactive demo of the rental agreement agent."""

    print("\n" + "=" * 70)
    print(" " * 10 + "🏠 ASSISTANT DE CRÉATION DE BAIL DE LOCATION 🏠")
    print("=" * 70)
    print(
        """
Bienvenue ! Cet assistant va vous aider à créer un bail de location
en vous posant des questions progressives sur votre bien immobilier.

Instructions :
- Répondez naturellement aux questions posées
- Vous pouvez donner plusieurs informations à la fois
- L'agent validera les données et demandera confirmation si nécessaire
- Tapez 'status' pour voir la progression
- Tapez 'quit' pour quitter
    """
    )
    print("=" * 70 + "\n")

    # Save the template
    print("📝 Chargement du modèle de bail...")
    with open("bail_template.json", "w", encoding="utf-8") as f:
        f.write(TEMPLATE_JSON)

    # Create the agent
    print("🤖 Initialisation de l'agent...")
    agent = create_rental_agent()

    # Configuration with thread ID for conversation persistence
    config = {"configurable": {"thread_id": "demo_session"}}

    # Initialize conversation
    print("✅ Agent prêt !\n")
    print("-" * 70)

    state = agent.invoke({"messages": []}, config)

    # Display initial message
    if state.get("messages"):
        for msg in state["messages"]:
            if isinstance(msg, AIMessage):
                print(f"\n🤖 Assistant:\n{msg.content}\n")
                print("-" * 70)

    # Main interaction loop
    while True:
        try:
            # Check if conversation is complete
            if state.get("conversation_phase") == "complete":
                print("\n" + "=" * 70)
                print(" " * 25 + "✅ BAIL COMPLÉTÉ !")
                print("=" * 70)
                break

            # Get user input
            user_input = input("\n👤 Vous: ").strip()

            # Handle special commands
            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n👋 Merci d'avoir utilisé l'assistant. À bientôt !")
                break

            if user_input.lower() == "status":
                # Show completion status
                if "completion_status" in state:
                    print("\n📊 ÉTAT DE PROGRESSION:")
                    print("-" * 40)
                    for section, percentage in state["completion_status"].items():
                        bar_length = int(percentage / 5)  # 20 character bar
                        bar = "█" * bar_length + "░" * (20 - bar_length)
                        print(f"  {section:25} [{bar}] {percentage:.1f}%")

                    overall = sum(state["completion_status"].values()) / len(
                        state["completion_status"]
                    )
                    print("-" * 40)
                    print(f"  {'TOTAL':25} {overall:.1f}%")
                continue

            if user_input.lower() == "help":
                print(
                    """
📌 AIDE:
- Répondez naturellement aux questions
- 'status' : voir la progression
- 'quit' : quitter l'application
- Vous pouvez donner plusieurs informations à la fois

Exemple de réponse multiple:
"Jean Dupont, 15 rue de la Paix 75001 Paris, jean@email.com"
                """
                )
                continue

            # Process user message
            print("\n⏳ Traitement de votre réponse...")

            # Send user message to agent
            user_message = HumanMessage(content=user_input)

            # First, extract information
            state = agent.invoke({"messages": [user_message]}, config)

            # Then generate next question or handle confirmation
            state = agent.invoke({"messages": []}, config)

            # Display response
            print("-" * 70)
            if state.get("messages"):
                # Get the last AI message
                for msg in reversed(state["messages"]):
                    if isinstance(msg, AIMessage):
                        print(f"\n🤖 Assistant:\n{msg.content}")
                        break

            # Show quick progress indicator
            if "completion_status" in state:
                overall = sum(state["completion_status"].values()) / len(
                    state["completion_status"]
                )
                bar_length = int(overall / 5)
                bar = "█" * bar_length + "░" * (20 - bar_length)
                print(f"\n📊 Progression: [{bar}] {overall:.1f}%")

            print("-" * 70)

        except KeyboardInterrupt:
            print("\n\n⚠️ Interruption détectée. Sauvegarde en cours...")
            break
        except Exception as e:
            print(f"\n❌ Erreur: {str(e)}")
            print("Veuillez réessayer ou taper 'quit' pour quitter.")

    print("\n" + "=" * 70)
    print("Merci d'avoir utilisé l'Assistant de Création de Bail !")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_interactive_demo()
