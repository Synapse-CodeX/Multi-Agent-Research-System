from graph import research_graph

STEP_LABELS = {
    "search": "Search agent finished gathering information",
    "reader": "Reader agent finished scraping deep content",
    "writer": "Writer chain finished drafting the report",
    "critic": "Critic chain finished reviewing the report",
}


def run_research_pipeline(topic: str) -> dict:
    """Run the full multi-agent research pipeline and return the final state.

    Uses research_graph.stream() rather than .invoke() so each stage's
    output is printed as soon as it completes, instead of waiting for the
    whole pipeline to finish before printing anything.
    """
    final_state = {"topic": topic}

    for step_output in research_graph.stream({"topic": topic}):
        for node_name, node_result in step_output.items():
            print("\n" + "=" * 50)
            print(STEP_LABELS.get(node_name, f"step complete: {node_name}"))
            print("=" * 50)
            for key, value in node_result.items():
                print(f"\n{key}:\n{value}")
            final_state.update(node_result)

    return final_state


if __name__ == "__main__":
    topic_input = input("\nEnter a research topic: ")
    result = run_research_pipeline(topic_input)

    print("\n\n" + "=" * 50)
    print("FINAL REPORT")
    print("=" * 50)
    print(result.get("report"))

    print("\n\n" + "=" * 50)
    print("CRITIC FEEDBACK")
    print("=" * 50)
    print(result.get("feedback"))