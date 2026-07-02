import traceback
from src.agents.graph import create_graph

try:
    create_graph("google_genai", "gemini-2.5-flash-lite", "dummy")
except Exception as e:
    traceback.print_exc()
