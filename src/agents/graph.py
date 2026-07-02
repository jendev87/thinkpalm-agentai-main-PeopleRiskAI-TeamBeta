import os
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.config.llm import get_chat_model
from src.agents.state import AgentState, IntentEnum
from src.agents.nodes import (
    create_router_node,
    create_data_query_node,
    create_retention_agent_node,
    create_general_chat_node
)

def create_graph(provider: str, model_name: str, api_key: str = None):
    """
    Graph Builder Pattern: Instantiates the LLM, binds it to nodes, 
    and returns a compiled LangGraph workflow with an in-memory checkpointer.
    """
    # 1. Initialize the LLM
    llm = get_chat_model(provider, model_name, api_key)
    
    # 2. Build the Graph
    builder = StateGraph(AgentState)
    
    # 3. Add Nodes (injecting the LLM)
    builder.add_node("router", create_router_node(llm))
    builder.add_node("data_query", create_data_query_node(llm))
    builder.add_node("retention", create_retention_agent_node(llm))
    builder.add_node("general", create_general_chat_node(llm))
    
    # 4. Define the routing logic
    def route_intent(state: AgentState):
        intent = state.get("current_intent")
        if intent == IntentEnum.DATA_QUERY:
            return "data_query"
        elif intent == IntentEnum.RETENTION_DOC:
            return "retention"
        else:
            return "general"
            
    # 5. Connect the Graph Edges
    builder.add_edge(START, "router")
    
    builder.add_conditional_edges(
        "router", 
        route_intent,
        {
            "data_query": "data_query",
            "retention": "retention",
            "general": "general"
        }
    )
    
    builder.add_edge("data_query", END)
    builder.add_edge("retention", END)
    builder.add_edge("general", END)
    
    # 6. Compile with a Checkpointer for State Persistence
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    
    return graph

if __name__ == '__main__':
    print("Initializing Graph with google_genai (gemini-2.5-flash-lite)...")
    
    # For testing purposes, we use a dummy key if not set. 
    # To run this successfully, ensure GOOGLE_API_KEY is exported in your environment.
    test_api_key = os.environ.get("GOOGLE_API_KEY", "DUMMY_TEST_KEY")
    
    try:
        app = create_graph(
            provider="google_genai", 
            model_name="gemini-2.5-flash-lite", 
            api_key=test_api_key
        )
        
        print("\n--- Test: Executing DATA_QUERY Intent ---")
        
        # We need a config with a thread_id for the checkpointer
        config = {"configurable": {"thread_id": "test_thread_1"}}
        
        # User's initial message
        input_state = {
            "messages": [("user", "Can you show me the attrition data for our top flight risks?")]
        }
        
        # Stream the graph execution
        for event in app.stream(input_state, config=config):
            for node_name, node_state in event.items():
                print(f"Executed Node: {node_name}")
                if "current_intent" in node_state and node_name == "router":
                    print(f"  -> Extracted Intent: {node_state['current_intent']}")
                    
        print("\n--- Test: Reading Final State from Memory ---")
        final_state = app.get_state(config)
        if final_state.values.get("messages"):
            last_message = final_state.values["messages"][-1]
            print(f"Final AI Response:\n{last_message.content}")
            
    except Exception as e:
        print(f"\nGraph execution failed. This is expected if the API key is a dummy or dependencies are missing: {e}")
