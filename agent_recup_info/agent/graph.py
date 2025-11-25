import operator
from datetime import datetime
from typing import TypedDict, Annotated, List, Union

from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode

from agent.tools import (
    get_global_feedback, 
    get_part_detail, 
    get_list_info,
    add_list_item,
    remove_list_item,
    set_value
)


# --- AGENT STATE DEFINITION ---

class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], operator.add]
    session_id: str


# --- AGENT BUILDER ---

def create_agent(llm):
    """
    Creates the LangGraph agent.
    """
    # Define tools - now includes list management tools
    tools = [
        get_global_feedback, 
        get_part_detail,
        get_list_info,
        add_list_item,
        remove_list_item,
        set_value
    ]
    llm_with_tools = llm.bind_tools(tools)

    # --- NODES ---

    def agent_node(state: AgentState):
        """Calls the LLM to decide the next action."""
        messages = state["messages"]
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
    
    current_date = datetime.now().strftime("%d/%m/%Y")

    system_message = f"""You are an expert assistant helping a user fill out a French lease (bail de location meublé) JSON file.
Your goal is to gather all the necessary information to complete the JSON structure.
Today's date is {current_date}.

## Process

1. **Identify the Session**: You will be provided with a `session_id`. ALWAYS use this ID for tool calls.

2. **Check Status**: At the start, or when unsure, use `get_global_feedback` to see what needs to be done.

3. **Ask Questions**: Pick an incomplete section, use `get_part_detail` to find missing fields, and ask the user for that specific information.

4. **Handle Lists**: When dealing with multiple tenants or guarantors:
   - Ask how many people there are
   - Use `add_list_item` to create slots for each person
   - Fill in each person's information with the correct index

5. **Update JSON**: When the user provides information, IMMEDIATELY use `set_value` to save it.
   - Make multiple updates in a single `set_value` call when possible for efficiency.

6. **Iterate**: Continue until all required fields are filled.

## Important Rules

- Be polite and professional.
- Speak in French.
- If the user provides ambiguous info, ask for clarification.
- When asking for information, explain WHY if it's not obvious.
- For lists, always check the current state with `get_list_info` before making changes.
- Remember that list indices are 0-based (first item is 0, second is 1, etc.).
- If some fields are not required, do not ask for them.
- If some value are obvious (or standard) with previous answers (like the "Le logement est-il situé en zone tendue" question but the apartment is at Paris, or "Est-ce une colocation ?" with 2 renters), do not ask for them and update the JSON file with the obvious value and say it to the user.
- The user don't see the JSON file, so don't explain the JSON structure to the user. Just speak about the document.
"""

    return agent, system_message