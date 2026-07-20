
from langgraph.graph import END,START,StateGraph

from app.graph.state import HiringState
from app.graph.nodes.jd_generator  import jd_generator_node

def build_graph():
    workflow = StateGraph(HiringState)
    workflow.add_node("jd_generator",jd_generator_node)
    workflow.add_edge(START, "jd_generator")
    workflow.add_edge("jd_generator", END)
    return workflow.compile()
