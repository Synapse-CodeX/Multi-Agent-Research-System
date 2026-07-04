from typing import Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from agents import build_reader_agent, build_search_agent, critic_chain, writer_chain


class ResearchState(TypedDict):
    """Shared state that flows through the graph.

    Each node reads what it needs from this dict and returns a partial
    dict of updates — LangGraph merges those updates back into the state.
    """
    topic: str
    search_results: Optional[str]
    scraped_content: Optional[str]
    report: Optional[str]
    feedback: Optional[str]


# ── Node functions ─────────────────────────────────────────────────────────────
# Each node builds its own agent instance so nodes stay stateless and cheap
# to re-run / test in isolation.

def search_node(state: ResearchState) -> dict:
    agent = build_search_agent()
    result = agent.invoke({
        "messages": [("user", f"Find recent, reliable and detailed information about: {state['topic']}")]
    })
    return {"search_results": result["messages"][-1].content}


def reader_node(state: ResearchState) -> dict:
    agent = build_reader_agent()
    result = agent.invoke({
        "messages": [(
            "user",
            f"Based on the following search results about '{state['topic']}', "
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"Search Results:\n{state['search_results'][:800]}"
        )]
    })
    return {"scraped_content": result["messages"][-1].content}


def writer_node(state: ResearchState) -> dict:
    research_combined = (
        f"SEARCH RESULTS:\n{state['search_results']}\n\n"
        f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}"
    )
    report = writer_chain.invoke({"topic": state["topic"], "research": research_combined})
    return {"report": report}


def critic_node(state: ResearchState) -> dict:
    feedback = critic_chain.invoke({"report": state["report"]})
    return {"feedback": feedback}


# ── Graph assembly ────────────────────────────────────────────────────────────
def build_research_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("search", search_node)
    graph.add_node("reader", reader_node)
    graph.add_node("writer", writer_node)
    graph.add_node("critic", critic_node)

    graph.add_edge(START, "search")
    graph.add_edge("search", "reader")
    graph.add_edge("reader", "writer")
    graph.add_edge("writer", "critic")
    graph.add_edge("critic", END)

    return graph.compile()


# Compiled once at import time and reused everywhere (pipeline.py, app.py).
research_graph = build_research_graph()