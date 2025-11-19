import os
import uuid
from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from agent.graph import create_agent

# Load environment variables
load_dotenv()

def main():
    # Initialize LLM
    # You can configure the model here based on your .env
    # Using a default OpenAI compatible setup as per the example request
    # Adjust base_url and api_key as needed if using Scaleway/Fireworks
    
    # api_key = os.getenv("OPENAI_API_KEY") # Or other key var
    # base_url = os.getenv("OPENAI_BASE_URL") # Optional
    
    # if not api_key:
    #     print("Error: API Key not found. Please set it in .env")
    #     return

    # llm = ChatOpenAI(
    #     model="gpt-5", # Or the specific model name
    #     api_key=api_key,
    #     base_url=base_url
    # )

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found. Please set it in .env")
        return

    llm = ChatAnthropic(
        model="claude-sonnet-4-5", 
        api_key=api_key
    )

    # Create Agent
    agent, system_prompt = create_agent(llm)

    # Session Management
    session_id = str(uuid.uuid4())
    print(f"--- Starting New Session: {session_id} ---")
    
    # Initial State
    messages = [SystemMessage(content=system_prompt)]
    
    print("Agent: Hello! I am here to help you create your French lease document. Let's get started.")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Goodbye!")
            break
            
        # Add user message to state
        # We need to pass session_id to the agent so it can use it in tools
        # We can append it to the user message or handle it in the state
        # For simplicity, we'll remind the agent of the session_id in the system prompt or context
        # But since the system prompt is static, let's add a hidden system message with the session ID if it's the first turn
        # OR just append it to the user input for the agent's context (invisible to user)
        
        # Better approach: The agent state has 'session_id'. 
        # But the graph definition in graph.py expects 'session_id' in the state.
        # When we invoke, we pass the state.
        
        current_state = {
            "messages": messages + [HumanMessage(content=f"Session ID: {session_id}\nUser Input: {user_input}")],
            "session_id": session_id
        }
        
        # Stream execution
        print("\nAgent is thinking...")
        final_response = None
        for event in agent.stream(current_state):
            for key, value in event.items():
                if "messages" in value:
                    messages = value["messages"] # Update messages history
                    if key == "agent":
                        msg = value["messages"][-1]
                        if msg.content:
                            print(f"Agent: {msg.content}")

if __name__ == "__main__":
    main()
