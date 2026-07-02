# PeopleRisk AI

## Project Overview
PeopleRisk AI is a cutting-edge, multi-agent enterprise HR attrition prediction and conversational platform designed for ThinkPalm teams. It represents a major transition from static data dashboards to a dynamic, AI-driven conversational search interface powered by LangGraph, flexible LLM integrations (Google GenAI, Groq, Anthropic), and automated manager dispatch mechanisms.

## Tech Stack & Architecture

| Component | Technology |
| :--- | :--- |
| **Language** | Python |
| **Orchestration** | LangGraph |
| **LLM Interface** | LangChain (Dynamic Provider Routing: Gemini, Llama, Claude) |
| **Machine Learning** | scikit-learn, XGBoost |
| **Explainability** | SHAP |
| **Data Processing** | Pandas, NumPy |
| **Database** | SQLite |
| **Frontend/UI** | Streamlit |
| **Reporting/Export** | python-docx, WeasyPrint |
| **Notifications** | smtplib, Slack Webhooks (Block Kit) |

## Project Status & Roadmap

- [x] **Phase 1: Data Foundation** (Anonymized 1,000-row SQLite seed generation)
- [x] **Phase 2: ML Core & Explainability Pipeline** (XGBoost Classifier + SHAP TreeExplainer)
- [x] **Phase 3: LangGraph Multi-Agent Orchestration** (Dynamic Provider abstraction, Conversational Memory, Intent Routing)
- [x] **Phase 4: Streamlit Conversational UI** (Dual-tab dashboard, Interactive Chat Copilot, Config Popover)
- [x] **Phase 5: Action & Automation Stack** (DOCX/PDF generation, SMTP Email Dispatch, Slack Alert Integration)
- [x] **Phase 6: Premium UI/UX Refinement** (ChatGPT-style sticky layouts, neon focus glow, zero-click Groq auto-connect, and intelligent follow-up chips)

## Machine Learning Core & Metrics

Our Phase 2 XGBoost model has been validated with the following performance metrics:
- **Accuracy**: 89.50%
- **Precision**: 90.40%
- **Recall**: 98.90% (Crucial for capturing potential flight risks)
- **F1-Score**: 94.46%

### Explainability
The ML pipeline leverages SHAP (SHapley Additive exPlanations) to provide individual-level interpretability. The SHAP TreeExplainer extracts the top 3 categorical drivers of attrition risk (e.g., Tenure, Salary, Monthly Hours) for each employee. These insights, along with the predicted risk probabilities (0-100%), are dynamically written to the `attrition_scores` SQLite database table.

## AI & Automation Features

### LangGraph Orchestration
The conversational backend relies on a state machine built with `LangGraph`. It intercepts user queries, routes them via an `IntentRouter` (e.g., General Chat vs. Retention Document Generation), and executes logic against dynamic LLMs using `langchain_core` APIs. Memory persistence is managed automatically.

### UI & Automation
The application uses Streamlit for a beautiful, premium Dark Mode interface engineered with a split-pane ChatGPT-style layout. 
- **Zero-Click Connect**: On launch, the system automatically reads environment variables and initializes the Groq API for immediate readiness.
- **Smart Responses**: When the AI generates insights or a "Retention Mitigation Action Plan," the UI dynamically renders context-aware Follow-Up chips and a 3-button Action Row directly beneath the response:
1. **📄 Download DOCX**: Uses `python-docx` to download an editable Word Document.
2. **✉️ Email PDF to Manager**: Uses `WeasyPrint` to compile a beautiful HTML template into a PDF and safely emails it to the manager via `smtplib` (with built-in space sanitization for App Passwords).
3. **💬 Send Slack Alert**: Dispatches a highly visible Block Kit payload via `requests` directly to a corporate Slack channel.

## Environment Setup & Installation

### 1. System Dependencies (macOS Apple Silicon)
WeasyPrint requires native C-libraries for PDF rendering:
```bash
brew install pango glib libffi
```

### 2. Python Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## How to Execute the Platform

### 1. Run the ML Pipeline (Only required if regenerating data)
```bash
source .venv/bin/activate
python src/models/training.py
python src/analytics/explainability.py
```

### 2. Boot the Streamlit UI
*Important Note for macOS Users: To bypass SIP (System Integrity Protection) stripping the Homebrew library paths for WeasyPrint, execute Python via the module flag:*

```bash
source .venv/bin/activate
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib
PYTHONPATH=. python -m streamlit run src/ui/app.py
```

Once running, the Copilot will automatically initialize the `Groq` LLM backend and anchor itself to the dashboard! You can open the "System Configuration & Settings" popover at the top right to verify or change the active AI Provider and API Key. For Automation (Email/Slack), populate the settings in the popover (using App Passwords if utilizing Gmail/O365). Leave them blank for simulated execution.
