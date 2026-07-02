import os
from langchain.chat_models import init_chat_model

def get_chat_model(provider: str, model_name: str, api_key: str = None):
    """
    Factory function to initialize a chat model using LangChain's unified init_chat_model.
    Supports dynamic API key injection overriding environment settings.
    """
    if api_key:
        if provider == "google_genai":
            os.environ["GOOGLE_API_KEY"] = api_key
        elif provider == "groq":
            os.environ["GROQ_API_KEY"] = api_key
        elif provider == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = api_key
            
    # Explicitly map the provider to the correct model_provider argument
    return init_chat_model(model_name, model_provider=provider)
