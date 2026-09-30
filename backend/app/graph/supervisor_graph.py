from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any, Optional
from ..agents.search_agent import search_agent_node
from ..agents.ranker_agent import ranker_agent_node
from ..agents.outreach_agent import outreach_agent_node


class TalentState(TypedDict, total=False):
    query: str
    filters: Dict[str, Any]
    job_description: str
    top_k: int
    search_results: List[Dict]
    rewritten_query: str
    ranked: List[Dict]
    outreach: List[Dict]
    auto_generate_outreach: bool


def should_generate_outreach(state: TalentState):
    if state.get("auto_generate_outreach") and state.get("job_description"):
        return "outreach"
    return END


def build_talent_graph():
    graph = StateGraph(TalentState)
    graph.add_node("search", search_agent_node)
    graph.add_node("ranker", ranker_agent_node)
    graph.add_node("outreach", outreach_agent_node)

    graph.set_entry_point("search")
    graph.add_edge("search", "ranker")
    graph.add_conditional_edges("ranker", should_generate_outreach, {
                                "outreach": "outreach", END: END})
    graph.add_edge("outreach", END)

    return graph.compile()


talent_graph = build_talent_graph()
