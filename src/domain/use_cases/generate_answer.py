"""RAG — busca semântica + geração com contexto real."""
from dataclasses import dataclass
from ..ports.embedding_port import EmbeddingPort
from ..ports.llm_port import LLMPort
from ..ports.vector_store_port import VectorStorePort

@dataclass
class RAGResponse:
    answer: str
    sources: list[str]
    confidence: float

class GenerateAnswerUseCase:
    def __init__(self, embedder: EmbeddingPort, store: VectorStorePort, llm: LLMPort):
        self._embedder = embedder
        self._store = store
        self._llm = llm

    async def execute(self, query: str, top_k: int = 5) -> RAGResponse:
        query_embedding = await self._embedder.embed(query)
        chunks = await self._store.similarity_search(query_embedding, top_k=top_k, threshold=0.7)

        if not chunks:
            return RAGResponse(answer="Sem informações relevantes na base.", sources=[], confidence=0.0)

        context = "\n\n---\n\n".join([
            f"[Fonte: {c.metadata.get('source', 'unknown')}]\n{c.text}" for c in chunks
        ])

        prompt = f"""Responda usando APENAS o contexto fornecido. Cite as fontes.

## Contexto:
{context}

## Pergunta:
{query}

## Resposta:"""

        answer = await self._llm.generate(prompt, temperature=0.1, max_tokens=1024)
        return RAGResponse(
            answer=answer,
            sources=list(set(c.metadata.get("source", "") for c in chunks)),
            confidence=max(c.similarity for c in chunks),
        )
