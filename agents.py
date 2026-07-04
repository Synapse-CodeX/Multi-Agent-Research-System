from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import create_agent
from tools import web_search, scrape_url
from dotenv import load_dotenv

load_dotenv()

# ── 1. Base Hugging Face endpoint ─────────────────────────────────────────────
llm_endpoint = HuggingFaceEndpoint(
    repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
    task="text-generation",
    max_new_tokens=1024,
    temperature=0.1,
)

# ── 2. Chat wrapper — adds tool-binding + system message support ─────────────
llm = ChatHuggingFace(llm=llm_endpoint)
print(type(llm), hasattr(llm, "bind_tools"))



def build_search_agent():
    """Agent that can call web_search to gather information."""
    return create_agent(
        model=llm,
        tools=[web_search],
        system_prompt="You are a research assistant. Use the web_search tool to find "
                      "recent, reliable information on the given topic, then summarize "
                      "the key facts, titles, and URLs you found.",
    )


def build_reader_agent():
    """Agent that can call scrape_url to read a page in depth."""
    return create_agent(
        model=llm,
        tools=[scrape_url],
        system_prompt="You are a research assistant. Given a set of search results, "
                      "pick the single most relevant URL and use the scrape_url tool "
                      "to pull its full content for deeper reading.",
    )


# ── Writer chain — a plain prompt -> llm chain, no tools needed ─────────────
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()


# ── Critic chain ──────────────────────────────────────────────────────────────
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()