from langgraph.graph import StateGraph, START, END

from app.graph.resume_state import ResumeState
from app.graph.nodes.resume_extractor import ResumeExtractorNode

from app.graph.nodes.resume_parser import ResumeParserNode
from app.graph.nodes.resume_storage import ResumeStorageNode


builder = StateGraph(ResumeState)

builder.add_node("extract_raw_text",ResumeExtractorNode())
builder.add_node("parse_resume",ResumeParserNode())
builder.add_node("store_resume",ResumeStorageNode())    

builder.add_edge(START,"extract_raw_text")
builder.add_edge("extract_raw_text","parse_resume")
builder.add_edge("parse_resume","store_resume")
builder.add_edge("store_resume",END)

resume_workflow = builder.compile()

















