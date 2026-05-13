from abc import ABC, abstractmethod
from ..entities.chunk import Chunk

class VectorStorePort(ABC):
    @abstractmethod
    async def upsert(self, chunks: list[Chunk]) -> None: ...

    @abstractmethod
    async def similarity_search(self, embedding: list[float], top_k: int = 5, threshold: float = 0.7) -> list[Chunk]: ...
