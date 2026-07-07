from langchain_core.tools import StructuredTool

from app.rag.retriever import get_retriever


def make_doc_search_tool() -> list:
    """RAG tool over the infra knowledge base (Kubernetes, Docker, Postgres, Redis, Kafka, Spring Boot, Go, Prometheus)."""
    retriever = get_retriever()

    def search_knowledge_base(query: str) -> str:
        """Search infra documentation for guidance relevant to a symptom or error (e.g. 'CrashLoopBackOff', 'connection pool exhausted')."""
        docs = retriever.invoke(query)
        if not docs:
            return "no relevant documentation found"
        return "\n---\n".join(f"[{d.metadata.get('source_name', 'doc')}] {d.page_content}" for d in docs)

    return [
        StructuredTool.from_function(
            search_knowledge_base, name="search_knowledge_base", description=search_knowledge_base.__doc__
        )
    ]
