# Czanix Boilerplate — AI/RAG Pipeline

> Pipeline de Retrieval-Augmented Generation pronto para produção. Vertex AI, pgvector, embeddings e busca semântica — sem wrapper mágico, sem vendor lock-in.

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Vertex AI](https://img.shields.io/badge/Vertex%20AI-Gemini-4285F4?style=flat&logo=google-cloud&logoColor=white)](https://cloud.google.com/vertex-ai)
[![PostgreSQL](https://img.shields.io/badge/pgvector-0.7-316192?style=flat&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tech Reference](https://img.shields.io/badge/Czanix-Tech%20Reference-gold)](https://czanix.com/pt/stack)

---

## O que é RAG e por que importa

LLMs são impressionantes, mas alucinam. RAG resolve isso injetando **contexto real** na geração:

```
Pergunta do usuário
    ↓
Busca semântica no seu banco de dados (pgvector)
    ↓
Top K documentos relevantes
    ↓
Prompt = Contexto real + Pergunta
    ↓
LLM gera resposta fundamentada nos seus dados
    ↓
Resposta com fonte citável
```

**Sem RAG:** "Qual o prazo de entrega?" → LLM inventa um prazo.
**Com RAG:** "Qual o prazo de entrega?" → LLM consulta sua base de conhecimento e responde com dados reais.

---

## Quando usar (e quando não usar)

**Use RAG quando:**
- Precisa de respostas baseadas em dados proprietários (docs, KB, contratos)
- O LLM precisa de contexto atualizado (dados mudam frequentemente)
- Compliance exige rastreabilidade (precisa citar a fonte)
- Custo de fine-tuning é proibitivo

**NÃO use RAG quando:**
- O conhecimento necessário é público e estável (use o LLM direto)
- O volume de dados é pequeno o suficiente para caber no context window
- Precisa de raciocínio multi-step complexo (RAG é retrieval, não reasoning)

---

## Arquitetura

```
src/
├── domain/                          # Regras de negócio
│   ├── entities/
│   │   ├── document.py              # Documento indexável
│   │   ├── chunk.py                 # Fragmento com embedding
│   │   └── query_result.py          # Resultado rankeado
│   ├── ports/
│   │   ├── embedding_port.py        # Interface para embeddings
│   │   ├── llm_port.py              # Interface para LLM
│   │   └── vector_store_port.py     # Interface para busca vetorial
│   └── use_cases/
│       ├── index_document.py        # Chunking + embedding + store
│       ├── semantic_search.py       # Query → relevantes
│       └── generate_answer.py       # RAG completo
│
├── infrastructure/
│   ├── embeddings/
│   │   ├── vertex_embedding.py      # Google Vertex AI
│   │   ├── openai_embedding.py      # OpenAI ada-002
│   │   └── local_embedding.py       # Sentence-Transformers (offline)
│   ├── llm/
│   │   ├── vertex_gemini.py         # Gemini Pro/Flash
│   │   ├── openai_gpt.py            # GPT-4o
│   │   └── ollama_local.py          # Ollama (llama3, mistral)
│   ├── vector_store/
│   │   ├── pgvector_store.py        # PostgreSQL + pgvector
│   │   └── chroma_store.py          # ChromaDB (dev/prototipação)
│   └── chunking/
│       ├── recursive_chunker.py     # Recursive text splitting
│       └── semantic_chunker.py      # Split por similaridade
│
├── presentation/
│   ├── api/
│   │   ├── routes.py                # FastAPI endpoints
│   │   └── schemas.py               # Pydantic models
│   └── cli/
│       └── indexer.py               # CLI para indexação batch
│
├── config/
│   └── settings.py                  # Configuração tipada
│
└── main.py
```

### Por que Ports/Adapters (Hexagonal)?

Porque amanhã você troca Vertex AI por Ollama local sem tocar em use case. O domínio não sabe (e não precisa saber) qual LLM está rodando.

---

## Início rápido

```bash
# 1. Clone
git clone https://github.com/czanix/boilerplate-ai-rag.git meu-rag
cd meu-rag

# 2. Ambiente virtual
python -m venv .venv && source .venv/bin/activate

# 3. Dependências
pip install -r requirements.txt

# 4. PostgreSQL + pgvector
docker compose up -d

# 5. Variáveis de ambiente
cp .env.example .env
# Configure: GOOGLE_CLOUD_PROJECT, EMBEDDING_MODEL, LLM_MODEL

# 6. Cria extensão pgvector
python -m src.infrastructure.vector_store.pgvector_store --init

# 7. Indexe seus documentos
python -m src.presentation.cli.indexer --source ./docs/

# 8. API
uvicorn src.main:app --reload
```

---

## Pipeline de Indexação

```python
# index_document.py — o fluxo completo
class IndexDocumentUseCase:
    def __init__(
        self,
        chunker: Chunker,
        embedder: EmbeddingPort,
        store: VectorStorePort,
    ):
        self._chunker = chunker
        self._embedder = embedder
        self._store = store

    async def execute(self, document: Document) -> IndexResult:
        # 1. Chunking — divide documento em fragmentos semânticos
        chunks = self._chunker.split(
            text=document.content,
            chunk_size=512,      # tokens por chunk
            chunk_overlap=64,    # overlap para não perder contexto
            metadata={"source": document.source, "title": document.title},
        )

        # 2. Embedding — transforma texto em vetor de 768 dimensões
        embeddings = await self._embedder.embed_batch(
            [chunk.text for chunk in chunks]
        )

        # 3. Store — salva no pgvector para busca semântica
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

        await self._store.upsert(chunks)

        return IndexResult(
            document_id=document.id,
            chunks_created=len(chunks),
            status="indexed",
        )
```

---

## Busca Semântica + Geração (RAG)

```python
# generate_answer.py — o coração do RAG
class GenerateAnswerUseCase:
    def __init__(
        self,
        embedder: EmbeddingPort,
        store: VectorStorePort,
        llm: LLMPort,
    ):
        self._embedder = embedder
        self._store = store
        self._llm = llm

    async def execute(self, query: str, top_k: int = 5) -> RAGResponse:
        # 1. Embed a pergunta
        query_embedding = await self._embedder.embed(query)

        # 2. Busca semântica — documentos mais relevantes
        relevant_chunks = await self._store.similarity_search(
            embedding=query_embedding,
            top_k=top_k,
            threshold=0.7,  # mínimo de similaridade
        )

        if not relevant_chunks:
            return RAGResponse(
                answer="Não encontrei informações relevantes na base.",
                sources=[],
                confidence=0.0,
            )

        # 3. Monta o prompt com contexto real
        context = "\n\n---\n\n".join([
            f"[Fonte: {chunk.metadata['source']}]\n{chunk.text}"
            for chunk in relevant_chunks
        ])

        prompt = f"""Responda a pergunta usando APENAS o contexto fornecido.
Se a resposta não estiver no contexto, diga que não tem informação suficiente.
Cite as fontes usadas.

## Contexto:
{context}

## Pergunta:
{query}

## Resposta:"""

        # 4. Gera resposta fundamentada
        answer = await self._llm.generate(
            prompt=prompt,
            temperature=0.1,  # baixa para respostas factuais
            max_tokens=1024,
        )

        return RAGResponse(
            answer=answer,
            sources=[c.metadata["source"] for c in relevant_chunks],
            confidence=max(c.similarity for c in relevant_chunks),
        )
```

---

## pgvector — SQL que entende semântica

```sql
-- Schema
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE chunks (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id UUID NOT NULL,
    content     TEXT NOT NULL,
    embedding   vector(768),       -- dimensão do modelo de embedding
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índice HNSW — busca aproximada rápida
CREATE INDEX ix_chunks_embedding
    ON chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Busca semântica em SQL puro
SELECT content, metadata,
       1 - (embedding <=> $1::vector) AS similarity
FROM chunks
WHERE 1 - (embedding <=> $1::vector) > 0.7
ORDER BY embedding <=> $1::vector
LIMIT 5;
```

**Por que pgvector e não Pinecone/Weaviate?** Porque você já tem PostgreSQL. Sem novo serviço, sem novo vendor, sem novo custo. Para <1M vetores, pgvector é mais que suficiente. [Trade-off completo →](https://czanix.com/pt/stack/tradeoffs)

---

## Multi-provider — sem vendor lock-in

```python
# settings.py — troca de provider por variável de ambiente
class Settings(BaseSettings):
    # Embedding: vertex, openai, ou local
    embedding_provider: str = "vertex"
    embedding_model: str = "text-embedding-004"

    # LLM: vertex, openai, ou ollama
    llm_provider: str = "vertex"
    llm_model: str = "gemini-1.5-flash"

    # Vector store: pgvector ou chroma
    vector_store: str = "pgvector"
```

**Dev local:** `ollama` + `chroma` (zero custo, zero API key)
**Produção:** `vertex` + `pgvector` (performance + integração)

---

## API Endpoints

```
POST   /api/v1/documents       # Indexa documento
GET    /api/v1/search           # Busca semântica pura
POST   /api/v1/ask              # RAG completo (busca + geração)
GET    /api/v1/health           # Health check
DELETE /api/v1/documents/:id    # Remove documento e chunks
```

```bash
# Exemplo: perguntar algo à sua base de conhecimento
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Qual a política de cancelamento?", "top_k": 5}'

# Resposta:
{
  "answer": "Conforme o documento de políticas internas...",
  "sources": ["politicas/cancelamento.pdf", "faq/v2.md"],
  "confidence": 0.89
}
```

---

## Testes

```bash
pytest                              # Todos
pytest tests/unit/                   # Sem dependência externa
pytest tests/integration/            # Com pgvector real
pytest --cov=src --cov-report=html   # Coverage
```

---

## Referência técnica

- [IA & Tecnologias Emergentes](https://czanix.com/pt/stack/ia)
- [Tech Radar — Vertex AI, pgvector, Ollama](https://czanix.com/pt/stack/tech-radar)
- [Catálogo de Trade-offs](https://czanix.com/pt/stack/tradeoffs)

---

## Licença

MIT — use, adapte, melhore. Se ajudou, [deixa uma estrela](https://github.com/czanix/boilerplate-ai-rag) ⭐

---

<div align="center">
<sub>Desenvolvido e mantido por <a href="https://czanix.com">Cesar Zanis</a> — Czanix</sub>
</div>
