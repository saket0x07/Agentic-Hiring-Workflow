from langgraph.graph import END, START, StateGraph

from app.graph.retrieval_state import RetrievalState
from app.graph.jd_embedding import JDEmbeddingNode
from app.graph.resume_search import ResumeSearchNode
from app.graph.fetch_candidates import FetchCandidatesNodes
from app.graph.rerank_candidates import RerankCandidatesNodes


builder = StateGraph(RetrievalState)

builder.add_node("embed_jd", JDEmbeddingNode())
builder.add_node("search_resumes", ResumeSearchNode())
builder.add_node("fetch_profiles", FetchCandidatesNodes())
builder.add_node("rerank_candidates", RerankCandidatesNodes())


builder.add_edge(START, "embed_jd")
builder.add_edge("embed_jd", "search_resumes")
builder.add_edge("search_resumes", "fetch_profiles")
builder.add_edge("fetch_profiles", "rerank_candidates")
builder.add_edge("rerank_candidates", END)

retrieval_workflow = builder.compile()