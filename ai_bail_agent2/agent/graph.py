import operator
from typing import TypedDict, Annotated, List, Union

from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from agent.tools import get_global_feedback, get_part_detail, set_value

# --- AGENT STATE DEFINITION ---

class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], operator.add]
    session_id: str

# --- AGENT BUILDER ---

def create_agent(llm):
    """
    Creates the LangGraph agent.
    """
    # Define tools
    tools = [get_global_feedback, get_part_detail, set_value]
    llm_with_tools = llm.bind_tools(tools)

    # --- NODES ---

    def agent_node(state: AgentState):
        """Calls the LLM to decide the next action."""
        messages = state["messages"]
        # Ensure session_id is in the context if needed, or just rely on the tool calls having it passed by the LLM
        # The LLM needs to know the session_id to call the tools.
        # We can inject it into the system prompt or ensure the LLM knows it.
        
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState) -> Union[str, str]:
        """Determines whether to call tools or to end."""
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools"
        return END

    # --- GRAPH CONSTRUCTION ---

    workflow = StateGraph(AgentState)

    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))

    workflow.add_edge(START, "agent")
    
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", END: END}
    )
    
    workflow.add_edge("tools", "agent")

    agent = workflow.compile()

    # --- SYSTEM PROMPT ---
    
    system_message = """You are an expert assistant helping a user fill out a French lease (bail de location) JSON file.
Your goal is to gather all the necessary information to complete the JSON structure.

You have access to the following tools:
1. `get_global_feedback(session_id)`: Check which sections are incomplete.
2. `get_part_detail(session_id, category)`: See exactly what fields are missing in a section.
3. `set_value(session_id, path, value)`: Update the JSON with information provided by the user.

**Process:**
1. **Identify the Session**: You will be provided with a `session_id`. ALWAYS use this ID for tool calls.
2. **Check Status**: At the start, or when unsure, use `get_global_feedback` to see what needs to be done.
3. **Ask Questions**: Pick an incomplete section, use `get_part_detail` to find missing fields, and ask the user for that specific information.
4. **Update JSON**: When the user provides information, IMMEDIATELY use `set_value` to save it.
   - The `path` for `set_value` should be the dot-notation path to the field (e.g., `designation_parties.bailleur.nom_prenom_ou_denomination`).
   - If the user gives multiple pieces of info, make multiple tool calls.
5. **Iterate**: Continue until all required fields are filled.

**Important:**
- Be polite and professional.
- Speak in French.
- If the user provides ambiguous info, ask for clarification.
- You can switch between sections if the user changes the topic.
- When asking for information, explain WHY if it's not obvious (e.g., "I need the address to complete the 'Housing' section").
"""

    return agent, system_message
