# PeopleRisk AI

## Project Overview
PeopleRisk AI is a cutting-edge, multi-agent enterprise HR attrition prediction and conversational platform. It represents a transition from static data dashboards to a dynamic, AI-driven conversational search interface powered by LangGraph, flexible LLM integrations (Google GenAI, Groq, Anthropic), and automated manager dispatch mechanisms.

This repository is designed to be easily extensible by both human developers and autonomous AI agents. 

---

## System Architecture & Module Design

The project is structured in a highly modular way under the `src/` directory to separate concerns and ensure maintainability.

### 1. `src/agents/` (AI & Orchestration)
Handles the conversational AI backend and state machine.
- **LangGraph Orchestrator**: Manages the conversational state, memory persistence, and flow.
- **Intent Router**: intercepts user queries and routes them dynamically (e.g., General Chat vs. Retention Document Generation).
- **Dynamic Provider Interface**: Abstracted LangChain bindings that dynamically switch between Gemini, Llama (via Groq), and Claude based on environment variables or UI configuration.

### 2. `src/models/` (Machine Learning Core)
Responsible for predicting employee flight risk.
- **XGBoost Classifier**: Trains on historical/synthetic HR data to predict the probability of attrition.
- **Metrics**: 89.5% Accuracy, 94.46% F1-Score, 98.9% Recall (optimized for capturing potential flight risks).

### 3. `src/analytics/` (Explainability)
Provides human-readable context to the ML predictions.
- **SHAP TreeExplainer**: Extracts the top 3 categorical drivers of attrition risk (e.g., Tenure, Salary, Monthly Hours) for each employee. These insights are synced back to the SQLite database.

### 4. `src/ui/` (Frontend & Interaction)
The client-facing interface built using **Streamlit**.
- **Dashboard Pane**: Renders metrics and high-risk employees in a standard data view.
- **Chat Copilot**: A sticky, ChatGPT-style chat panel featuring dynamic user/assistant rendering, seamless scrolling, and zero-click Groq auto-connection.
- **UI Components**: Uses CSS grid/flex layouts and custom styling to maintain a unified dark-mode enterprise aesthetic.

### 5. `src/automation/` (Action & Dispatch)
Executes real-world actions based on AI intents.
- **Document Generation**: Generates editable Word Documents using `python-docx`.
- **PDF & Email Dispatch**: Compiles beautiful HTML templates into PDFs using `WeasyPrint` and dispatches them via `smtplib`.
- **Slack Alerts**: Fires high-visibility Block Kit payloads via `requests` to corporate Slack channels.

### 6. `src/data/` & `src/storage/` (Persistence)
- Manages the local `SQLite` database (`hr_data.db`).
- Handles conversation persistence and state tracking across Streamlit sessions.

### 7. `src/config/` (Environment)
- Responsible for injecting environment variables from `.env`.
- Manages cross-module constants and feature flags.

---

## Tech Stack Summary

| Layer | Technologies |
| :--- | :--- |
| **Language** | Python 3.9+ |
| **Orchestration** | LangGraph, LangChain |
| **Machine Learning** | scikit-learn, XGBoost, SHAP |
| **Data Processing** | Pandas, NumPy, SQLite3 |
| **Frontend/UI** | Streamlit, Custom CSS |
| **Reporting & Actions** | python-docx, WeasyPrint, smtplib, Slack Block Kit |

---

## Environment Setup & Installation

### 1. System Dependencies
The PDF generation engine (`WeasyPrint`) requires native C-libraries for rendering. Install these dependencies using your operating system's package manager:
- **macOS (Homebrew)**: `brew install pango glib libffi`
- **Linux (Apt)**: `sudo apt-get install libpango1.0-dev libglib2.0-dev libffi-dev`
- **Windows**: Refer to the GTK3 installation instructions for WeasyPrint.

### 2. Python Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Variables
Copy the provided `.env.example` file to create your local `.env`.
```bash
cp .env.example .env
```
Populate the API keys and SMTP credentials as needed. The platform can operate in a simulated mode if Slack/SMTP credentials are left blank.

---

## Execution Workflow

### 1. Run the ML Pipeline
If the SQLite database (`hr_data.db`) is missing or needs regeneration, run the data foundation and training pipelines:
```bash
source .venv/bin/activate
python -m src.models.training
python -m src.analytics.explainability
```

### 2. Boot the Streamlit UI
Start the conversational frontend:
```bash
source .venv/bin/activate
PYTHONPATH=. python -m streamlit run src/ui/app.py
```

*Note: Depending on your system configuration (e.g., if utilizing Homebrew on macOS), you may need to explicitly export library paths before running Streamlit if WeasyPrint fails to locate Pango/Glib.*

Once running, the Copilot will automatically initialize the LLM backend and anchor itself to the dashboard. You can access the "System Configuration & Settings" popover to hot-swap AI providers or manage automation credentials on the fly.
