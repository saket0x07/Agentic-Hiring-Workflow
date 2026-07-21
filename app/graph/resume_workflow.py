from langgraph.graph import END, START, StateGraph

from app.graph.resume_embedding import ResumeEmbeddingNode
from app.graph.resume_extractor import ResumeExtractorNode
from app.graph.resume_index import ResumeIndexerNode
from app.graph.resume_parser import ResumeParserNode
from app.graph.resume_state import ResumeState
from app.graph.resume_storage import ResumeStorageNode

builder = StateGraph(ResumeState)

builder.add_node("extract_raw_text", ResumeExtractorNode())
builder.add_node("parse_resume", ResumeParserNode())
builder.add_node("store_resume", ResumeStorageNode())
builder.add_node("resume_embed", ResumeEmbeddingNode())
builder.add_node("resume_index", ResumeIndexerNode())

builder.add_edge(START, "extract_raw_text")
builder.add_edge("extract_raw_text", "parse_resume")
builder.add_edge("parse_resume", "store_resume")
builder.add_edge("store_resume", "resume_embed")
builder.add_edge("resume_embed", "resume_index")
builder.add_edge("resume_index", END)

resume_workflow = builder.compile()
