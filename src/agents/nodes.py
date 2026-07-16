from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage
from src.agents.state import AgentState, IntentEnum
from src.agents.sql_generator import nl_to_dataframe

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
                    "If they ask about attrition, data, employee stats, departments, roles, salaries, "
                    "risk percentages, drivers, headcount, or flight risks, it's DATA_QUERY. "
                    "If they want to generate a document or note to a manager to retain an employee, it's RETENTION_DOC. "
                    "Otherwise, it's GENERAL."
        )
        
        # Bind the LLM to strictly output the Pydantic model
        structured_llm = llm.with_structured_output(IntentClassification)
        response = structured_llm.invoke([system_prompt] + messages)
        
        return {"current_intent": response.intent}
    
    return router_node

def _latest_user_text(messages) -> str:
    """Extract the most recent human message content for NL→SQL."""
    for msg in reversed(messages):
        role = getattr(msg, "type", None) or getattr(msg, "role", None)
        if role in ("human", "user") or (
            isinstance(msg, tuple) and len(msg) >= 2 and msg[0] in ("user", "human")
        ):
            if isinstance(msg, tuple):
                return str(msg[1])
            return str(getattr(msg, "content", msg))
    # Fallback: stringify last message
    if not messages:
        return ""
    last = messages[-1]
    return str(getattr(last, "content", last))


def create_data_query_node(llm):
    """
    Creates a node that turns the user's question into SQL, runs it safely,
    and narrates the result.
    """
    def data_query_node(state: AgentState):
        messages = state["messages"]
        user_question = _latest_user_text(messages)

        df, sql_used, sql_note = nl_to_dataframe(llm, user_question)
        extracted = df.to_dict(orient="records")
        row_count = len(extracted)

        # Cap payload size sent back to the LLM for narration
        preview = extracted[:40]
        note_line = f" Note: {sql_note}" if sql_note else ""

        system_prompt = SystemMessage(
            content=(
                "You are a helpful HR data analyst for PeopleRisk AI. "
                "Answer the user's question using ONLY the query results below. "
                "Be specific with EmployeeIDs, departments, roles, and risk %. "
                "If results are empty, say so and suggest a narrower or broader question. "
                "Do not invent employees that are not in the data. "
                "Format clearly (short bullets or a compact table).\n\n"
                f"SQL executed:\n{sql_used}\n"
                f"Rows returned: {row_count}.{note_line}\n"
                f"Results:\n{preview}"
            )
        )

        response = llm.invoke([system_prompt] + messages)

        return {
            "extracted_data": {
                "sql": sql_used,
                "note": sql_note,
                "row_count": row_count,
                "rows": extracted,
            },
            "messages": [response],
        }

    return data_query_node

def create_retention_agent_node(llm):
    """
    Creates a node that drafts a targeted manager mitigation note.
    """
    def retention_agent_node(state: AgentState):
        messages = state["messages"]
        extracted_data = state.get("extracted_data", {})
        if isinstance(extracted_data, dict) and "rows" in extracted_data:
            context = extracted_data.get("rows") or extracted_data
        else:
            context = extracted_data

        system_prompt = SystemMessage(
            content="You are an expert HR retention specialist. Generate a customized manager mitigation note "
                    "based on the employee's structural SHAP attributes (Top 3 drivers and Risk Percentage) to help retain them. "
                    f"Context data available: {context}"
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
