import sqlite3
import pandas as pd
from pathlib import Path
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage
from src.agents.state import AgentState, IntentEnum

class IntentClassification(BaseModel):
    """Schema for extracting the user's intent."""
    intent: IntentEnum = Field(description="The classified intent of the user's message.")

def create_router_node(llm):
    """
    Creates a node that classifies the conversation into a specific intent.
    Uses structured output parsing.
    """
    def router_node(state: AgentState):
        messages = state["messages"]
        system_prompt = SystemMessage(
            content="You are an HR AI assistant. Classify the user's intent into GENERAL, DATA_QUERY, or RETENTION_DOC. "
                    "If they ask about attrition, data, employee stats, or flight risks, it's DATA_QUERY. "
                    "If they want to generate a document or note to a manager to retain an employee, it's RETENTION_DOC. "
                    "Otherwise, it's GENERAL."
        )
        
        # Bind the LLM to strictly output the Pydantic model
        structured_llm = llm.with_structured_output(IntentClassification)
        response = structured_llm.invoke([system_prompt] + messages)
        
        return {"current_intent": response.intent}
    
    return router_node

def create_data_query_node(llm):
    """
    Creates a node that executes a Pandas data query against SQLite and formulates an answer.
    """
    def data_query_node(state: AgentState):
        messages = state["messages"]
        
        # Connect to hr_data.db
        project_root = Path(__file__).parent.parent.parent
        db_path = project_root / 'hr_data.db'
        
        with sqlite3.connect(db_path) as conn:
            # For this phase, we do a static query simulating a data fetch of top flight risks.
            # In Phase 4, we could use the LLM to generate the SQL query dynamically.
            query = "SELECT e.EmployeeID, e.Department, e.Role, a.RiskPercentage, a.Driver1, a.Driver2, a.Driver3 FROM employees e JOIN attrition_scores a ON e.EmployeeID = a.EmployeeID ORDER BY a.RiskPercentage DESC LIMIT 5"
            df = pd.read_sql_query(query, conn)
            
        extracted = df.to_dict(orient='records')
        
        system_prompt = SystemMessage(
            content=f"You are a helpful HR data analyst. Here is the relevant employee data (top flight risks): {extracted}. "
                    "Answer the user's query clearly using this data. Format the output nicely."
        )
        
        response = llm.invoke([system_prompt] + messages)
        
        return {"extracted_data": extracted, "messages": [response]}
        
    return data_query_node

def create_retention_agent_node(llm):
    """
    Creates a node that drafts a targeted manager mitigation note.
    """
    def retention_agent_node(state: AgentState):
        messages = state["messages"]
        extracted_data = state.get("extracted_data", {})
        
        system_prompt = SystemMessage(
            content="You are an expert HR retention specialist. Generate a customized manager mitigation note "
                    "based on the employee's structural SHAP attributes (Top 3 drivers and Risk Percentage) to help retain them. "
                    f"Context data available: {extracted_data}"
        )
        response = llm.invoke([system_prompt] + messages)
        return {"messages": [response]}
        
    return retention_agent_node

def create_general_chat_node(llm):
    """
    Creates a node that handles generic chat queries.
    """
    def general_chat_node(state: AgentState):
        messages = state["messages"]
        system_prompt = SystemMessage(
            content="You are PeopleRisk AI, a polite and helpful HR conversational assistant for ThinkPalm teams."
        )
        response = llm.invoke([system_prompt] + messages)
        return {"messages": [response]}
        
    return general_chat_node
