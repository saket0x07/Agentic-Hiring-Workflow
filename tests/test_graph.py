import asyncio
import json
from app.graph.workflow import graph

initial_state = {
    "job_id": "JOB-TEST-101",
    "workflow_stage": "START",
    "status": "PENDING",
    "hiring_request": {
        "role": "Software Engineer",
        "department": "Engineering",
        "experience": "2 years",
        "location": "New York",
        "employment_type": "full_time",
        "work_mode": "remote",
        "budget": "$120k",
        "required_skills": ["Python", "FastAPI"],
        "preferred_skills": ["Docker", "LangChain"],
        "notes": "Urgent hiring"
    },
    "generated_jd": None,
    "pdf_path": None,
    "approved": False,
    "feedback": None,
    "messages": [],
    "errors": []
}

async def main():
    response = await graph.ainvoke(initial_state)
    print("Graph execution response:")
    output_str = json.dumps(response, indent=2, ensure_ascii=True)
    print(output_str)

if __name__ == "__main__":
    asyncio.run(main())