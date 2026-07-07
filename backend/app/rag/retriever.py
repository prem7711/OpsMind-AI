from functools import lru_cache

from langchain_chroma import Chroma

from app.config import settings
from app.llm import get_embeddings

COLLECTION_NAME = "sentinel_knowledge_base"


@lru_cache
def get_vectorstore() -> Chroma:
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=settings.chroma_path,
    )


def get_retriever(k: int = 4):
    return get_vectorstore().as_retriever(search_kwargs={"k": k})
