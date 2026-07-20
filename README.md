# Agentic Hiring Workflow 🤖💼

An automated, multi-agent AI system built with **LangGraph**, **LangChain**, **FastAPI**, and **Streamlit** designed to streamline end-to-end technical hiring pipelines.

---

## 📁 Directory Structure

```text
Agentic-Hiring-Workflow/
│
├── app/
│   ├── api/
│   │   └── main.py
│   │
│   └── ui/
│       └── streamlit_app.py
│
├── config/
│   └── settings.py
│
├── src/
│   ├── agents/
│   │   └── jd_generator.py
│   │
│   ├── graph/
│   │   ├── builder.py
│   │   ├── workflow.py
│   │   ├── state.py
│   │   └── nodes/
│   │       ├── jd_generator.py
│   │       └── hitl.py
│   │
│   ├── prompts/
│   │   └── jd_generation.py
│   │
│   ├── schemas/
│   │   ├── hiring.py
│   │   └── jd.py
│   │
│   ├── services/
│   │   ├── email_service.py
│   │   └── pdf_service.py
│   │
│   └── utils/
│       └── logger.py
│
├── data/
│   ├── jobs/
│   ├── resumes/
│   └── outputs/
│
├── tests/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```
